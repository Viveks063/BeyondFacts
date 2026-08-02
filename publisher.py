"""
Publisher Module for Beyond Facts AI Social Agent.
Implements standard interface for publishing posts to Instagram API with error handling and fallback modes.
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Union
from post_instagram import post_to_instagram

logger = logging.getLogger("PublisherModule")


class SocialPublisher(ABC):
    """Abstract Strategy interface for social media platform publishing."""

    @property
    @abstractmethod
    def platform_name(self) -> str:
        pass

    @abstractmethod
    def publish(self, image_urls: Union[List[str], str], caption: str) -> Optional[str]:
        pass


class InstagramPublisher(SocialPublisher):
    """Concrete Instagram Graph API Publisher."""

    @property
    def platform_name(self) -> str:
        return "Instagram"

    def publish(self, image_urls: Union[List[str], str], caption: str) -> Optional[str]:
        logger.info(f"Publishing to Instagram ({len(image_urls) if isinstance(image_urls, list) else 1} slide(s))...")
        try:
            post_id = post_to_instagram(image_urls=image_urls, caption=caption)
            if post_id:
                logger.info(f"Successfully published to Instagram! Media ID: {post_id}")
            else:
                logger.warning("Instagram publishing returned no Media ID.")
            return post_id
        except Exception as e:
            logger.error(f"Error publishing to Instagram: {e}", exc_info=True)
            return None


class PublisherEngine:
    """Orchestrates multi-platform publishing."""

    def __init__(self):
        self.publishers: List[SocialPublisher] = [InstagramPublisher()]

    def publish_post(self, image_urls: Union[List[str], str], caption: str) -> dict:
        """
        Publishes content across all configured publishers.

        Returns dict of platform -> post_id
        """
        results = {}
        for publisher in self.publishers:
            name = publisher.platform_name
            logger.info(f"Dispatching post to {name}...")
            post_id = publisher.publish(image_urls, caption)
            results[name] = post_id
        return results


if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    publisher = PublisherEngine()
    print(f"Configured publishers: {[p.platform_name for p in publisher.publishers]}")
