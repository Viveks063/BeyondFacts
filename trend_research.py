"""
Multi-Source News & Real Story Research Aggregator for Beyond Facts.
Fetches live stories from Reddit (r/todayilearned, r/science, r/interestingasfuck),
Wikipedia 'Did You Know', NASA, ScienceDaily, Interesting Engineering, and Google Trends.
"""

import os
import json
import logging
import requests
import feedparser
from typing import List, Dict, Any

load_dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(load_dotenv_path):
    from dotenv import load_dotenv
    load_dotenv(load_dotenv_path, override=True)

logger = logging.getLogger("TrendResearchAgent")

# Reliable high-curiosity content sources
FEED_SOURCES = [
    {"name": "Reddit TIL", "url": "https://www.reddit.com/r/todayilearned/hot.json?limit=25", "type": "reddit"},
    {"name": "Reddit Science", "url": "https://www.reddit.com/r/science/hot.json?limit=20", "type": "reddit"},
    {"name": "Reddit Interesting", "url": "https://www.reddit.com/r/interestingasfuck/hot.json?limit=20", "type": "reddit"},
    {"name": "Wikipedia DYK", "url": "https://en.wikipedia.org/w/api.php?action=featuredfeed&feed=dyk&feedformat=atom", "type": "rss"},
    {"name": "NASA News", "url": "https://www.nasa.gov/news-release/feed/", "type": "rss"},
    {"name": "ScienceDaily", "url": "https://www.sciencedaily.com/rss/all.xml", "type": "rss"},
    {"name": "Interesting Engineering", "url": "https://www.interestingengineering.com/rss", "type": "rss"},
    {"name": "Google Discovery", "url": "https://news.google.com/rss/search?q=unbelievable+scientific+discovery+history+mistake&hl=en-US&gl=US&ceid=US:en", "type": "rss"}
]


class TrendResearchAgent:
    """
    Multi-source story aggregator.
    Collects 50-100 real, verified reporting items from high-authority sources.
    """

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) BeyondFactsBot/2.0"
        }

    def fetch_reddit_posts(self, url: str) -> List[Dict[str, Any]]:
        posts = []
        try:
            res = requests.get(url, headers=self.headers, timeout=8)
            if res.status_code == 200:
                data = res.json()
                children = data.get("data", {}).get("children", [])
                for child in children:
                    pdata = child.get("data", {})
                    title = pdata.get("title", "").strip()
                    permalink = f"https://reddit.com{pdata.get('permalink', '')}"
                    score = pdata.get("score", 0)
                    if title and not pdata.get("stickied") and score > 100:
                        # Clean common Reddit TIL prefix if present
                        clean_title = title.replace("TIL that ", "").replace("TIL ", "").strip()
                        posts.append({
                            "title": clean_title,
                            "summary": pdata.get("selftext", clean_title)[:250],
                            "source_name": "Reddit",
                            "url": permalink,
                            "score": score
                        })
        except Exception as e:
            logger.warning(f"Could not fetch Reddit feed {url}: {e}")
        return posts

    def fetch_rss_posts(self, url: str, source_name: str) -> List[Dict[str, Any]]:
        posts = []
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                title = entry.get("title", "").strip()
                summary = entry.get("summary", entry.get("description", "")).strip()
                link = entry.get("link", url)
                if title:
                    posts.append({
                        "title": title,
                        "summary": summary[:250],
                        "source_name": source_name,
                        "url": link,
                        "score": 500
                    })
        except Exception as e:
            logger.warning(f"Could not fetch RSS feed {url}: {e}")
        return posts

    def collect_live_story_pool(self) -> List[Dict[str, Any]]:
        """
        Collects up to 100 interesting real stories across all sources.
        """
        logger.info("📡 Aggregating live story pool from Reddit, NASA, Wikipedia, ScienceDaily, & Smithsonian...")
        pool = []

        for source in FEED_SOURCES:
            if source["type"] == "reddit":
                items = self.fetch_reddit_posts(source["url"])
                pool.extend(items)
            elif source["type"] == "rss":
                items = self.fetch_rss_posts(source["url"], source["name"])
                pool.extend(items)

        logger.info(f"✅ Successfully collected {len(pool)} real story candidates for Gemini selection.")
        return pool


if __name__ == "__main__":
    agent = TrendResearchAgent()
    stories = agent.collect_live_story_pool()
    print(f"Collected {len(stories)} stories.")
    if stories:
        print("Sample story 1:", stories[0]["title"])
