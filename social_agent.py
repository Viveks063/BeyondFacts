import os
import sys
import sqlite3
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from post_instagram import post_to_instagram
from trend_research import TrendResearchAgent
from fact_verifier import FactVerifierAgent
from design_engine.poster_generator import PosterGenerator
from design_engine.themes import ThemeSystem
import cloudinary
import cloudinary.uploader

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv(override=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("BeyondFactsAgent")


# ==========================================
# 1. Database Manager (history.db)
# ==========================================
class HistoryDatabase:
    """SQLite Database Manager for tracking generated and published posters."""

    def __init__(self, db_path: str = "history.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS post_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT,
                    category TEXT,
                    caption TEXT,
                    image_url TEXT,
                    platform TEXT,
                    platform_post_id TEXT,
                    status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def save_post(
        self,
        topic: str,
        category: str,
        caption: str,
        image_url: str,
        platform: str,
        platform_post_id: Optional[str],
        status: str
    ) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO post_history (topic, category, caption, image_url, platform, platform_post_id, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (topic, category, caption, image_url, platform, platform_post_id, status))
            conn.commit()
            return cursor.lastrowid


# ==========================================
# 2. SOLID Strategy: SocialPublisher Interface
# ==========================================
class SocialPublisher(ABC):
    @property
    @abstractmethod
    def platform_name(self) -> str:
        pass

    @abstractmethod
    def publish(self, image_urls: list[str] | str, caption: str) -> Optional[str]:
        pass


class InstagramPublisher(SocialPublisher):
    @property
    def platform_name(self) -> str:
        return "Instagram"

    def publish(self, image_urls: list[str] | str, caption: str) -> Optional[str]:
        return post_to_instagram(image_urls=image_urls, caption=caption)


# ==========================================
# 3. Cloudinary Uploader
# ==========================================
class CloudinaryUploader:
    def __init__(self):
        cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
        api_key = os.getenv("CLOUDINARY_API_KEY")
        api_secret = os.getenv("CLOUDINARY_API_SECRET")

        if cloud_name and api_key and api_secret:
            cloudinary.config(
                cloud_name=cloud_name,
                api_key=api_key,
                api_secret=api_secret,
                secure=True
            )
            self.configured = True
            logger.info("Cloudinary configured.")
        else:
            self.configured = False
            logger.warning("Cloudinary credentials missing in .env.")

    def upload_files(self, file_paths: list[str]) -> list[str]:
        public_urls = []
        if self.configured:
            for file_path in file_paths:
                if os.path.exists(file_path):
                    logger.info(f"Uploading poster {file_path} to Cloudinary...")
                    res = cloudinary.uploader.upload(file_path)
                    public_url = res.get("secure_url")
                    logger.info(f"Cloudinary upload successful: {public_url}")
                    public_urls.append(public_url)
            return public_urls
        else:
            logger.info("Using hosted demo image URL for Instagram API requirement.")
            return ["https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=1080&q=80"] * len(file_paths)


# ==========================================
# 4. Beyond Facts Agent Pipeline
# ==========================================
class BeyondFactsAgent:
    """
    End-to-End Beyond Facts Agent Pipeline:
    Gemini JSON -> Fact Verification -> Playwright Design Engine (Carousel PNGs) -> Cloudinary -> Instagram Publisher.
    """

    def __init__(self):
        self.trend_agent = TrendResearchAgent()
        self.verifier_agent = FactVerifierAgent()
        self.poster_generator = PosterGenerator()
        self.uploader = CloudinaryUploader()
        self.db = HistoryDatabase()
        self.publishers: list[SocialPublisher] = [InstagramPublisher()]

    def run_pipeline(self):
        logger.info("=== Starting 'Beyond Facts' Autonomous Poster Pipeline ===")

        # Step 1: Discover Curiosity Topic (Gemini JSON)
        post_data = self.trend_agent.discover_best_topic()
        topic = post_data.get("topic", "Fascinating Fact")
        hook_slide = next((s for s in post_data.get("slides", []) if s.get("type") == "hook"), {})
        
        print(f"\n🧠 Curiosity Topic Discovered: '{topic}'")
        print(f"📌 Hook: '{hook_slide.get('text', 'Did You Know?')}'")
        print(f"🏷️ Category: '{post_data.get('category')}'")

        # Step 2: Fact Verification
        fact_sheet = self.verifier_agent.verify_topic(topic, hook_slide.get("text", ""))
        print(f"✅ Verified Sources: {', '.join(fact_sheet.get('trusted_sources', []))}")

        # Step 3: Design Engine Generation (HTML -> Playwright High-DPI PNGs)
        timestamp = int(time.time())
        base_filename = f"poster_{timestamp}"
        png_paths = self.poster_generator.generate_carousel(post_data, base_filename=base_filename)

        print(f"\n🎨 High-DPI 1080x1350 Carousel Generated: {len(png_paths)} slides")

        # Step 4: Upload to Cloudinary
        public_image_urls = self.uploader.upload_files(png_paths)

        # Step 5: Publish & Persist
        caption = post_data.get("caption", "")

        for publisher in self.publishers:
            logger.info(f"Publishing poster to {publisher.platform_name}...")
            post_id = publisher.publish(image_urls=public_image_urls, caption=caption)

            status = "SUCCESS" if post_id else "FAILED"

            record_id = self.db.save_post(
                topic=topic,
                category=post_data.get("category", "General"),
                caption=caption,
                image_url=public_image_urls[0] if public_image_urls else "",
                platform=publisher.platform_name,
                platform_post_id=post_id,
                status=status
            )

            if post_id:
                print(f"\n🎉 SUCCESS: Published carousel to {publisher.platform_name}! (Media ID: {post_id}, DB Record #{record_id})")
            else:
                print(f"\n❌ FAILURE: Could not publish to {publisher.platform_name}. (DB Record #{record_id})")


if __name__ == "__main__":
    import time
    agent = BeyondFactsAgent()
    agent.run_pipeline()
