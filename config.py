"""
Configuration module for Beyond Facts AI Social Agent.
Defines daily schedules, topic queue maps, API settings, and database paths.
"""

import os
from dotenv import load_dotenv

load_dotenv(override=True)

# Base Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "history.db")

# 8 Posts per day schedule (2-hour intervals)
DEFAULT_SCHEDULE = [
    {"slot": "08:00", "category": "Psychology", "emoji": "🧠"},
    {"slot": "10:00", "category": "Cars", "emoji": "🏎️"},
    {"slot": "12:00", "category": "History", "emoji": "📜"},
    {"slot": "14:00", "category": "Science", "emoji": "🚀"},
    {"slot": "16:00", "category": "Animals", "emoji": "🐘"},
    {"slot": "18:00", "category": "Money", "emoji": "💰"},
    {"slot": "20:00", "category": "Space", "emoji": "🌌"},
    {"slot": "22:00", "category": "Random", "emoji": "⚡"},
]

# Supported Pillars
ALL_CATEGORIES = [
    "Psychology", "Cars", "History", "Science",
    "Animals", "Money", "Space", "Random", "Did You Know?", "Technology"
]

# Scheduler Check Interval (seconds) for daemon mode
CHECK_INTERVAL_SECONDS = 60

# Cloudinary / Image Hosting Config
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

# Instagram Credentials
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
INSTAGRAM_BUSINESS_ID = os.getenv("INSTAGRAM_BUSINESS_ID")

# Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
