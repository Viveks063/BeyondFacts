import os
import json
import logging
import requests
import feedparser
import urllib.parse
from typing import List, Dict, Any
from google import genai
from dotenv import load_dotenv

load_dotenv(override=True)
logger = logging.getLogger("TrendResearchAgent")

CONTENT_PILLARS = [
    "Psychology", "Did You Know?", "Science", "Geography",
    "History", "Animals", "Cars", "Money & Business", "Technology", "Space"
]

CURIOSITY_HOOKS = [
    "This sounds fake, but it's true...",
    "Almost nobody knows this...",
    "Scientists discovered...",
    "You probably never noticed...",
    "This changes how you think...",
    "Wait until you learn this...",
    "Most people get this wrong..."
]


class TrendResearchAgent:
    """
    Phase 2: Curiosity-Driven Content Agent.
    Researches live curiosity trends, ranks them for maximum viral curiosity,
    and structures content into precise JSON schema.
    """

    def __init__(self):
        gemini_key = os.getenv("GEMINI_API_KEY")
        if not gemini_key:
            raise ValueError("GEMINI_API_KEY is not set in environment.")
        self.client = genai.Client(api_key=gemini_key)

        self.rss_sources = [
            "https://news.google.com/rss/search?q=science+history+psychology+discoveries&hl=en-US&gl=US&ceid=US:en",
            "https://hnrss.org/frontpage"
        ]

    def fetch_raw_trends(self, limit_per_source: int = 4) -> List[Dict[str, str]]:
        logger.info("Step 1: Researching curiosity topics from live feeds...")
        raw_items = []

        for url in self.rss_sources:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:limit_per_source]:
                    title = entry.get("title", "").strip()
                    summary = entry.get("summary", entry.get("description", "")).strip()
                    if title:
                        raw_items.append({
                            "title": title,
                            "summary": summary[:200]
                        })
            except Exception as e:
                logger.warning(f"Could not fetch feed {url}: {e}")

        return raw_items

    def rank_and_select_topic(self, raw_trends: List[Dict[str, str]]) -> Dict[str, Any]:
        logger.info("Step 2: Ranking topics for curiosity & shareability...")

        trends_context = json.dumps(raw_trends, indent=2)

        prompt = f"""
You are the Lead Editor for "Beyond Facts", a premium educational curiosity brand.
Mission: Make people learn one fascinating thing every day in under 30 seconds.

Content Pillars: {CONTENT_PILLARS}
Curiosity Hooks: {CURIOSITY_HOOKS}

Analyze these news and curiosity trends:
{trends_context}

Select the single best topic that makes someone stop scrolling and think "Wait... what?".
Build a 4-slide curiosity loop carousel.

RULES FOR SLIDES:
- Slide 1 (hook): The curiosity gap. Must be under 12 words.
- Slide 2 (fact): The mind-blowing fact.
- Slide 3 (explanation): The short reason why it's true.
- Slide 4 (engagement): A provocative question to drive comments.
- Keep EVERY slide under 25 words!

Return strictly JSON matching this structure:
{{
    "category": "Psychology | Science | History | Cars | Animals | Did You Know? | Money & Business | Space | Geography | Technology",
    "topic": "Topic Name for DB",
    "slides": [
        {{"type": "hook", "text": "Almost everyone would fail this experiment."}},
        {{"type": "fact", "text": "Ordinary people will obey authority even when they know it's wrong."}},
        {{"type": "explanation", "text": "This was demonstrated in the infamous Milgram experiment."}},
        {{"type": "engagement", "text": "Do you think you would have obeyed? 👇 Comment YES or NO."}}
    ],
    "caption": "This sounds fake... \n\n[Fact]\n\n[Explanation]\n\nQuestion?\n\n#beyondfacts #curiosity #science"
}}
"""

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )

        try:
            return json.loads(response.text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return {
                "category": "Psychology",
                "topic": "Embarrassing Memories",
                "slides": [
                    {"type": "hook", "text": "Your brain is lying to you at 2 AM."},
                    {"type": "fact", "text": "Your brain replays embarrassing moments at night because it consolidates emotional memories during REM sleep."},
                    {"type": "explanation", "text": "Evolutionarily, your brain prioritizes negative experiences to keep you safe from repeating social mistakes."},
                    {"type": "engagement", "text": "What's the most random memory that keeps you awake? 👇 Comment below!"}
                ],
                "caption": "Ever wonder why past embarrassing moments replay when you try to sleep? 🧠✨ #BeyondFacts #Psychology"
            }

    def discover_best_topic(self) -> Dict[str, Any]:
        raw_trends = self.fetch_raw_trends()
        return self.rank_and_select_topic(raw_trends)
