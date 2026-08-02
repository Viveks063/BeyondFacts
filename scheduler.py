"""
Scheduler Engine for Beyond Facts AI Social Agent.
Monitors daily posting slots (08:00, 10:00, 12:00, 14:00, 16:00, 18:00, 20:00, 22:00),
verifies database state to avoid duplicate posts or missed slots,
and triggers the content generation, rendering, publishing, and analytics pipeline.
Includes HTTP health check server for 24/7 cloud deployments (Render, Railway).
"""

import os
import sys
import time
import argparse
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from config import DEFAULT_SCHEDULE, CHECK_INTERVAL_SECONDS
from database import DatabaseManager
from generator import ContentGenerator
from poster import PosterEngine
from publisher import PublisherEngine
from analytics import AnalyticsEngine

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("Scheduler")


class HealthCheckHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler to satisfy Render/Railway port health check scans."""
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Beyond Facts AI Social Agent Daemon Active 24/7\n")

    def log_message(self, format, *args):
        # Silence standard HTTP access logging to keep daemon logs clean
        pass


def start_health_server():
    """Starts background HTTP health check server on $PORT for Render/Railway."""
    port_str = os.getenv("PORT", "8000")
    try:
        port = int(port_str)
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        logger.info(f"🌐 HTTP Health Check Server running on port {port} for cloud hosting.")
        server.serve_forever()
    except Exception as e:
        logger.warning(f"Could not start health check HTTP server on port {port_str}: {e}")


class SocialAgentScheduler:
    """
    Main Orchestrator and Scheduler for Beyond Facts AI Social Agent.
    """

    def __init__(self, use_dynamic_ai_queue: bool = True):
        self.db = DatabaseManager()
        self.generator = ContentGenerator()
        self.poster_engine = PosterEngine()
        self.publisher_engine = PublisherEngine()
        self.analytics_engine = AnalyticsEngine(db=self.db)
        self.use_dynamic_ai_queue = use_dynamic_ai_queue

    def get_current_schedule(self) -> List[Dict[str, str]]:
        """Gets either the default schedule or AI dynamically optimized queue."""
        if self.use_dynamic_ai_queue:
            try:
                return self.analytics_engine.generate_dynamic_queue()
            except Exception as e:
                logger.warning(f"Could not compute dynamic queue, using default schedule: {e}")
                return DEFAULT_SCHEDULE
        return DEFAULT_SCHEDULE

    def find_due_slot(self, now: Optional[datetime] = None) -> Optional[Dict[str, str]]:
        """
        Checks if there is a scheduled post due right now that has NOT been posted today.
        Matches time slots within a grace window (e.g. current hour/slot).
        """
        if now is None:
            now = datetime.now()

        current_hour = now.hour
        today_date_str = now.strftime("%Y-%m-%d")

        schedule = self.get_current_schedule()

        for slot_item in schedule:
            slot_time = slot_item["slot"]
            slot_hour = int(slot_time.split(":")[0])

            # Slot is due if current hour matches slot_hour AND post has not been made today for this slot
            if current_hour == slot_hour:
                is_already_posted = self.db.is_slot_posted_today(slot_time, date_str=today_date_str)
                if not is_already_posted:
                    logger.info(f"📍 Post DUE detected for slot {slot_time} ({slot_item['category']})!")
                    return slot_item
                else:
                    logger.debug(f"Slot {slot_time} ({slot_item['category']}) already processed today.")

        return None

    def execute_post_pipeline(self, slot_item: Dict[str, str]) -> bool:
        """
        Executes the end-to-end publishing pipeline for a due slot:
        Check Schedule -> Generate -> Render Poster -> Upload CDN -> Publish Instagram -> DB Save -> Analytics
        """
        slot_time = slot_item["slot"]
        category = slot_item["category"]
        emoji = slot_item.get("emoji", "🧠")

        logger.info(f"\n=======================================================")
        logger.info(f"🚀 Starting Pipeline Execution for Slot: {slot_time} [{category} {emoji}]")
        logger.info(f"=======================================================")

        try:
            # Step 1: Content Generation (Head of Content + Verified Multi-Source Pool)
            logger.info("Step 1/5: Generating curiosity carousel from multi-source story pool...")
            post_data = self.generator.generate_for_category(category)
            topic = post_data.get("topic", f"Fascinating {category} Fact")
            caption = post_data.get("caption", "")

            # Step 2: Create initial DB record (PROCESSING)
            post_id = self.db.create_post_record(
                topic=topic,
                category=category,
                caption=caption,
                image="",
                time_slot=slot_time,
                status="PROCESSING"
            )

            # Step 3: Poster Generation & CDN Upload
            logger.info("Step 2/5: Rendering Playwright PNG slides and uploading to Cloudinary CDN...")
            render_res = self.poster_engine.generate_and_upload(post_data, base_name=f"post_{post_id}")
            public_urls = render_res.get("public_urls", [])
            primary_url = render_res.get("primary_image_url", "")

            if not public_urls:
                raise ValueError("No image URLs produced by poster engine.")

            # Step 4: Publish to Instagram
            logger.info(f"Step 3/5: Publishing carousel to Instagram API...")
            publish_results = self.publisher_engine.publish_post(
                image_urls=public_urls,
                caption=caption
            )
            ig_post_id = publish_results.get("Instagram")

            status = "PUBLISHED" if ig_post_id else "FAILED"

            # Step 5: Update Database
            logger.info(f"Step 4/5: Updating database record #{post_id} with status '{status}'...")
            self.db.update_post_status(
                post_id=post_id,
                status=status,
                instagram_post_id=ig_post_id,
                image_url=primary_url
            )

            # Step 6: Update analytics
            if status == "PUBLISHED":
                logger.info(f"Step 5/5: Updating engagement metrics baseline...")
                self.analytics_engine.update_post_metrics_from_ig(post_id)
                logger.info(f"🎉 SUCCESS! Slot {slot_time} [{category}] posted successfully (IG Media ID: {ig_post_id})")
                return True
            else:
                logger.warning(f"⚠️ Could not complete Instagram publication for slot {slot_time} [{category}]. Recorded status as 'FAILED' in DB.")
                return True

        except Exception as e:
            logger.error(f"Error executing post pipeline for slot {slot_time}: {e}", exc_info=True)
            return True

    def check_schedule(self) -> bool:
        """
        Single tick check: Checks if a post is due and executes if so.
        """
        logger.info("Checking schedule for due posts...")
        due_slot = self.find_due_slot()
        if due_slot:
            return self.execute_post_pipeline(due_slot)
        else:
            logger.info("No posts currently due for this slot.")
            return True

    def run_daemon(self):
        """
        Continuous safe daemon mode: checks every minute without crashing.
        Includes background HTTP health server for cloud deployments.
        """
        # Start background health server for Render/Railway
        t = threading.Thread(target=start_health_server, daemon=True)
        t.start()

        logger.info("Starting Beyond Facts Scheduler Daemon (checking every 60 seconds)...")
        print("\n🤖 Beyond Facts AI Social Agent Daemon Running!")
        print("Press Ctrl+C to stop.\n")

        while True:
            try:
                self.check_schedule()
            except Exception as e:
                logger.error(f"Unexpected error in daemon loop: {e}", exc_info=True)

            time.sleep(CHECK_INTERVAL_SECONDS)

    def print_schedule_status(self):
        """Displays today's posting schedule and database status."""
        today_date = datetime.now().strftime("%Y-%m-%d")
        schedule = self.get_current_schedule()

        print(f"\n=======================================================")
        print(f" 📅 Beyond Facts Schedule Status ({today_date})")
        print(f"=======================================================")

        posts = self.db.get_all_posts(limit=20)
        posted_slots = {p["time_slot"]: p for p in posts if p.get("posted_at", "").startswith(today_date)}

        for item in schedule:
            slot = item["slot"]
            cat = item["category"]
            emoji = item.get("emoji", "")

            if slot in posted_slots:
                p = posted_slots[slot]
                status_str = f"✅ POSTED [{p['status']}] - Topic: '{p['topic']}'"
            else:
                status_str = "⏳ PENDING"

            print(f"  {slot} → {cat:<12} {emoji}  | {status_str}")

        print("=======================================================\n")


def main():
    parser = argparse.ArgumentParser(description="Beyond Facts AI Social Agent Scheduler")
    parser.add_argument("--check", "--once", action="store_true", help="Run a single schedule check and exit (for Cron / GitHub Actions)")
    parser.add_argument("--daemon", action="store_true", help="Run continuous background daemon process")
    parser.add_argument("--status", action="store_true", help="Print schedule status for today")
    parser.add_argument("--force", type=str, help="Force run a specific time slot (e.g. 08:00)")

    args = parser.parse_args()
    scheduler = SocialAgentScheduler()

    if args.status:
        scheduler.print_schedule_status()
        sys.exit(0)
    elif args.force:
        slot_item = next((s for s in scheduler.get_current_schedule() if s["slot"] == args.force), {
            "slot": args.force, "category": "Psychology", "emoji": "🧠"
        })
        print(f"Force executing slot {args.force} ({slot_item['category']})...")
        scheduler.execute_post_pipeline(slot_item)
        sys.exit(0)
    elif args.daemon:
        scheduler.run_daemon()
    else:
        scheduler.check_schedule()
        sys.exit(0)


if __name__ == "__main__":
    main()
