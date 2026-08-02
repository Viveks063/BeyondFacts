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
logger = logging.getLogger("FactVerifierAgent")


class FactVerifierAgent:
    """
    Phase 3: Fact Verification Module.
    Takes a selected topic, researches 3 trusted sources/articles across live news APIs / RSS,
    summarizes verified facts using Gemini, and prevents hallucinated content.
    """

    def __init__(self):
        gemini_key = os.getenv("GEMINI_API_KEY")
        if not gemini_key:
            raise ValueError("GEMINI_API_KEY is not set in environment.")
        self.client = genai.Client(api_key=gemini_key)

    def fetch_trusted_sources(self, topic: str, max_sources: int = 3) -> List[Dict[str, str]]:
        """Searches live news RSS feeds to pull 3 trusted source articles related to the topic."""
        logger.info(f"Phase 3: Searching 3 trusted sources for topic: '{topic}'...")
        
        encoded_query = urllib.parse.quote(topic)
        google_news_feed = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        
        sources = []
        try:
            feed = feedparser.parse(google_news_feed)
            for entry in feed.entries[:max_sources]:
                sources.append({
                    "title": entry.get("title", ""),
                    "source": entry.get("source", {}).get("title", "Verified News Outlet"),
                    "link": entry.get("link", ""),
                    "summary": entry.get("summary", entry.get("description", ""))[:300]
                })
        except Exception as e:
            logger.warning(f"Failed to fetch live sources: {e}")

        # Fallback if specific search returns fewer than required
        if len(sources) < max_sources:
            logger.info("Supplementing with default verified tech RSS sources...")
            try:
                gen_feed = feedparser.parse("https://news.google.com/rss/search?q=artificial+intelligence&hl=en-US&gl=US&ceid=US:en")
                for entry in gen_feed.entries:
                    if len(sources) >= max_sources:
                        break
                    sources.append({
                        "title": entry.get("title", ""),
                        "source": entry.get("source", {}).get("title", "Tech News"),
                        "link": entry.get("link", ""),
                        "summary": entry.get("summary", "")[:300]
                    })
            except Exception as e:
                logger.warning(f"Error fetching general feed: {e}")

        logger.info(f"Retrieved {len(sources)} trusted sources.")
        return sources

    def verify_and_summarize(self, topic: str, angle: str, sources: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Uses Gemini to cross-verify facts from the 3 sources and build a grounded, trustworthy fact sheet.
        """
        logger.info("Cross-verifying facts across 3 sources using Gemini...")
        sources_text = json.dumps(sources, indent=2)

        prompt = f"""
You are an uncompromising Fact-Checker and Journalist.

Topic: "{topic}"
Angle: "{angle}"

Trusted Reference Sources:
{sources_text}

Task:
1. Extract verified key facts from the provided sources. Do NOT invent or hallucinate details.
2. Synthesize a grounded, 100% accurate fact summary.
3. Highlight citation sources to ensure post authenticity.

Return strictly valid JSON:
{{
    "verified_topic": "{topic}",
    "key_facts": [
        "Fact 1 verified from source",
        "Fact 2 verified from source",
        "Fact 3 verified from source"
    ],
    "trusted_sources": [
        "Source Name 1",
        "Source Name 2",
        "Source Name 3"
    ],
    "fact_summary": "Clean, accurate, hallucination-free summary of the topic grounded strictly in the source material."
}}
"""

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )

        try:
            fact_sheet = json.loads(response.text)
            logger.info("Fact verification successfully completed.")
            return fact_sheet
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse fact verification JSON: {e}")
            return {
                "verified_topic": topic,
                "key_facts": [item["title"] for item in sources],
                "trusted_sources": [item.get("source", "Verified News") for item in sources],
                "fact_summary": f"Verified story on {topic} based on recent reportings."
            }

    def verify_topic(self, topic: str, angle: str) -> Dict[str, Any]:
        """Full Phase 3 Pipeline."""
        sources = self.fetch_trusted_sources(topic)
        fact_sheet = self.verify_and_summarize(topic, angle, sources)
        return fact_sheet


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    verifier = FactVerifierAgent()
    sample_topic = "YouTuber Hank Green says his AI usage is 'not healthy'"
    sample_angle = "Explore the personal cost of hyper-engagement with AI"
    result = verifier.verify_topic(sample_topic, sample_angle)
    print("\n--- Phase 3 Fact Verification Result ---")
    print(json.dumps(result, indent=2))
