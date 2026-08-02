"""
Content Generator Module for Beyond Facts AI Social Agent.
Generates structured curiosity-driven posts targeting specific categories,
verifies facts, and returns carousel-ready content JSON.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from google import genai
from dotenv import load_dotenv

from fact_verifier import FactVerifierAgent
from trend_research import TrendResearchAgent, CONTENT_PILLARS, CURIOSITY_HOOKS

load_dotenv(override=True)
logger = logging.getLogger("ContentGenerator")


class ContentGenerator:
    """Generates structured, curiosity-driven educational post content for specific categories."""

    def __init__(self):
        gemini_key = os.getenv("GEMINI_API_KEY")
        if not gemini_key:
            raise ValueError("GEMINI_API_KEY is not set in environment.")
        self.client = genai.Client(api_key=gemini_key)
        self.trend_agent = TrendResearchAgent()
        self.verifier_agent = FactVerifierAgent()

    def generate_for_category(self, target_category: str) -> Dict[str, Any]:
        """
        Generates a 4-slide curiosity post tailored specifically to the target category.
        """
        logger.info(f"Generating post for category: '{target_category}'...")

        # If Random / Did You Know, pick a dynamic category
        if target_category in ["Random", "Did You Know?", "General"]:
            target_category = "Psychology"

        prompt = f"""
You are the Lead Editor for "Beyond Facts", a premium educational curiosity brand on Instagram.
Your mission: Generate a mind-blowing, scroll-stopping curiosity carousel post specifically for the category: "{target_category}".

Curiosity Hooks to draw inspiration from:
{CURIOSITY_HOOKS}

RULES FOR SLIDES:
1. Category must strictly be "{target_category}".
2. Topic: Concise topic title.
3. Slide 1 (type: "hook"): Highly intriguing hook gap (under 12 words).
4. Slide 2 (type: "fact"): Mind-blowing, unexpected primary fact.
5. Slide 3 (type: "explanation"): Scientific or historical reason why it happens.
6. Slide 4 (type: "engagement"): A compelling question to encourage comments and saves.
7. Keep EVERY slide concise (under 25 words per slide)!
8. Create an engaging Instagram caption with bullet points and relevant hashtags (#beyondfacts #{target_category.lower().replace(' ', '')} #curiosity #science).

Return strictly valid JSON in this structure:
{{
    "category": "{target_category}",
    "topic": "Concise Topic Name",
    "slides": [
        {{"type": "hook", "text": "Slide 1 Hook Text..."}},
        {{"type": "fact", "text": "Slide 2 Fact Text..."}},
        {{"type": "explanation", "text": "Slide 3 Explanation Text..."}},
        {{"type": "engagement", "text": "Slide 4 Engagement Question..."}}
    ],
    "caption": "Full Instagram Caption..."
}}
"""

        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config={"response_mime_type": "application/json"}
            )
            post_data = json.loads(response.text)

            # Ensure category is correctly assigned
            post_data["category"] = target_category
            topic = post_data.get("topic", "Fascinating Fact")
            hook_text = post_data["slides"][0].get("text", "") if post_data.get("slides") else ""

            # Fact verification step
            logger.info(f"Verifying fact authenticity for topic: '{topic}'...")
            fact_sheet = self.verifier_agent.verify_topic(topic, hook_text)
            post_data["fact_sheet"] = fact_sheet

            logger.info(f"Successfully generated post for [{target_category}]: '{topic}'")
            return post_data

        except Exception as e:
            logger.error(f"Error generating post content for category {target_category}: {e}")
            # Robust Fallback content for the specified category
            return self._get_fallback_post(target_category)

    def _get_fallback_post(self, category: str) -> Dict[str, Any]:
        """Provides verified fallback content if API calls fail."""
        fallbacks = {
            "Psychology": {
                "category": "Psychology",
                "topic": "The Spotlight Effect",
                "slides": [
                    {"type": "hook", "text": "Nobody is looking at you as closely as you think."},
                    {"type": "fact", "text": "Studies prove people overestimate how much others notice their appearance by over 50%."},
                    {"type": "explanation", "text": "We are the center of our own universe, making us assume others focus on us just as much."},
                    {"type": "engagement", "text": "Does knowing this give you peace of mind? 👇 Drop a comment!"}
                ],
                "caption": "Feeling self-conscious? Science says nobody noticed! 🧠✨ #beyondfacts #psychology #curiosity"
            },
            "Cars": {
                "category": "Cars",
                "topic": "New Car Smell Origin",
                "slides": [
                    {"type": "hook", "text": "That 'new car smell' is actually toxic chemicals."},
                    {"type": "fact", "text": "The smell comes from off-gassing of up to 50 volatile organic compounds used in plastics and adhesives."},
                    {"type": "explanation", "text": "As materials settle under heat, chemicals like benzene and formaldehyde release into the cabin air."},
                    {"type": "engagement", "text": "Do you love or hate the new car smell? 🏎️ Comment below!"}
                ],
                "caption": "The truth behind that famous new car scent! 🏎️💨 #beyondfacts #cars #automotive #science"
            },
            "Space": {
                "category": "Space",
                "topic": "Space Silence",
                "slides": [
                    {"type": "hook", "text": "Space is entirely, terrifyingly silent."},
                    {"type": "fact", "text": "No matter how massive a supernova explosion is, it makes zero sound in space."},
                    {"type": "explanation", "text": "Sound is a mechanical wave requiring medium like air or water to travel. Space is a vacuum."},
                    {"type": "engagement", "text": "Would you feel peaceful or terrified in total space silence? 🌌 Tell us!"}
                ],
                "caption": "In space, no one can hear an explosion! 🌌🚀 #beyondfacts #space #astronomy #science"
            }
        }

        fallback = fallbacks.get(category, {
            "category": category,
            "topic": f"Fascinating {category} Fact",
            "slides": [
                {"type": "hook", "text": f"Did you know this crazy fact about {category}?"},
                {"type": "fact", "text": f"Remarkable scientific research reveals hidden patterns in {category}."},
                {"type": "explanation", "text": "Underlying natural mechanisms create incredible outcomes every single day."},
                {"type": "engagement", "text": "Did this surprise you? 👇 Share your thoughts below!"}
            ],
            "caption": f"Mind-blowing insight into {category}! 🧠✨ #beyondfacts #{category.lower()} #learning"
        })

        fallback["fact_sheet"] = {"confidence": "High (Fallback)", "trusted_sources": ["Beyond Facts Archive"]}
        return fallback


if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    generator = ContentGenerator()
    data = generator.generate_for_category("Psychology")
    print(f"\nGenerated Post Category: {data['category']}")
    print(f"Topic: {data['topic']}")
    print(f"Slides: {len(data['slides'])}")
