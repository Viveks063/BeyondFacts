"""
Poster Generation & Media Hosting Engine for Beyond Facts.
Renders high-DPI carousel PNG slides via Playwright design engine
and uploads them to Cloudinary for Instagram publication.
"""

import os
import sys
import time
import logging
from typing import Dict, Any, List
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

from design_engine.poster_generator import PosterGenerator
from config import CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET

load_dotenv(override=True)
logger = logging.getLogger("PosterEngine")


class CloudinaryUploader:
    """Uploads locally rendered PNG slides to Cloudinary CDN."""

    def __init__(self):
        if CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET:
            cloudinary.config(
                cloud_name=CLOUDINARY_CLOUD_NAME,
                api_key=CLOUDINARY_API_KEY,
                api_secret=CLOUDINARY_API_SECRET,
                secure=True
            )
            self.configured = True
            logger.info("Cloudinary CDN connection configured.")
        else:
            self.configured = False
            logger.warning("Cloudinary credentials not set in environment. Using demo image fallback.")

    def upload_files(self, file_paths: List[str]) -> List[str]:
        """Uploads list of image files to Cloudinary and returns HTTPS secure URLs."""
        uploaded_urls = []
        if self.configured:
            for file_path in file_paths:
                if os.path.exists(file_path):
                    logger.info(f"Uploading slide to Cloudinary: {os.path.basename(file_path)}...")
                    res = cloudinary.uploader.upload(file_path)
                    secure_url = res.get("secure_url")
                    logger.info(f"Uploaded successfully: {secure_url}")
                    uploaded_urls.append(secure_url)
            return uploaded_urls
        else:
            # Hosted high-quality fallback image for testing if Cloudinary missing
            logger.info("Using hosted fallback image URL for Instagram Graph API.")
            return ["https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=1080&q=80"] * len(file_paths)


class PosterEngine:
    """Orchestrates poster creation and image hosting."""

    def __init__(self, output_dir: str = "design_engine/generated"):
        self.generator = PosterGenerator(output_dir=output_dir)
        self.uploader = CloudinaryUploader()

    def generate_and_upload(self, post_data: Dict[str, Any], base_name: str = None) -> Dict[str, Any]:
        """
        Renders Playwright high-DPI carousel PNGs and uploads them to CDN.

        Returns:
            Dict containing local_paths, image_urls, and post_data.
        """
        if not base_name:
            timestamp = int(time.time())
            category = post_data.get("category", "post").lower().replace(" ", "_")
            base_name = f"poster_{category}_{timestamp}"

        logger.info(f"Step 1: Rendering carousel slides for '{post_data.get('topic')}'...")
        local_png_paths = self.generator.generate_carousel(post_data, base_filename=base_name)

        logger.info(f"Step 2: Uploading {len(local_png_paths)} slides to CDN...")
        public_urls = self.uploader.upload_files(local_png_paths)

        return {
            "local_paths": local_png_paths,
            "public_urls": public_urls,
            "primary_image_url": public_urls[0] if public_urls else ""
        }


if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    poster_engine = PosterEngine()
    test_data = {
        "category": "Psychology",
        "topic": "The Spotlight Effect",
        "slides": [
            {"type": "hook", "text": "Nobody is looking at you as closely as you think."},
            {"type": "fact", "text": "Studies prove people overestimate how much others notice their appearance by over 50%."},
            {"type": "explanation", "text": "We are the center of our own universe, making us assume others focus on us just as much."},
            {"type": "engagement", "text": "Does knowing this give you peace of mind? 👇 Drop a comment!"}
        ]
    }

    res = poster_engine.generate_and_upload(test_data, "test_run")
    print(f"\nGenerated PNGs: {len(res['local_paths'])}")
    print(f"Public URLs: {res['public_urls']}")
