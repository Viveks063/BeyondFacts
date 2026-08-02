import os
import time
import logging
from typing import Optional, Dict, Any
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("InstagramPublisher")

# Graph API Version
GRAPH_API_VERSION = "v20.0"
BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


class InstagramAPIError(Exception):
    """Custom Exception for Instagram API Errors."""
    pass


def _get_credentials() -> tuple[str, str]:
    """Retrieves access token and business ID from environment variables."""
    access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    business_id = os.getenv("INSTAGRAM_BUSINESS_ID")

    if not access_token or not business_id:
        logger.error("Missing INSTAGRAM_ACCESS_TOKEN or INSTAGRAM_BUSINESS_ID in environment variables.")
        raise ValueError("INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_BUSINESS_ID must be set in .env")

    return access_token, business_id


def upload_image(image_url: str, caption: str = "", is_carousel_item: bool = False) -> str:
    """
    Creates an Instagram media container for an image post.

    Args:
        image_url (str): Publicly accessible URL of the image.
        caption (str): Caption for the Instagram post (ignored if is_carousel_item).
        is_carousel_item (bool): Set to True if this image is part of a carousel.

    Returns:
        str: Container creation ID.
    """
    access_token, business_id = _get_credentials()
    url = f"{BASE_URL}/{business_id}/media"

    payload = {
        "image_url": image_url,
        "access_token": access_token
    }
    
    if is_carousel_item:
        payload["is_carousel_item"] = "true"
    elif caption:
        payload["caption"] = caption

    logger.info(f"Creating media container for image URL: {image_url}")
    try:
        response = requests.post(url, data=payload, timeout=30)
        data = response.json()

        if response.status_code != 200 or "id" not in data:
            error_msg = data.get("error", {}).get("message", "Unknown error creating media container")
            logger.error(f"Failed to create media container: {error_msg} (Status: {response.status_code})")
            raise InstagramAPIError(f"Upload Image Container Error: {error_msg}")

        creation_id = data["id"]
        logger.info(f"Media container created successfully. Creation ID: {creation_id}")
        return creation_id

    except requests.RequestException as e:
        logger.error(f"Network error during upload_image: {e}")
        raise InstagramAPIError(f"Network error creating media container: {e}") from e

def create_carousel_container(children: list[str], caption: str) -> str:
    """Creates a carousel container grouping multiple media items."""
    access_token, business_id = _get_credentials()
    url = f"{BASE_URL}/{business_id}/media"

    payload = {
        "media_type": "CAROUSEL",
        "children": ",".join(children),
        "caption": caption,
        "access_token": access_token
    }

    logger.info(f"Creating CAROUSEL container with {len(children)} children...")
    try:
        response = requests.post(url, data=payload, timeout=30)
        data = response.json()

        if response.status_code != 200 or "id" not in data:
            error_msg = data.get("error", {}).get("message", "Unknown error creating carousel container")
            raise InstagramAPIError(f"Carousel Container Error: {error_msg}")

        carousel_id = data["id"]
        logger.info(f"Carousel container created successfully. ID: {carousel_id}")
        return carousel_id

    except requests.RequestException as e:
        raise InstagramAPIError(f"Network error creating carousel container: {e}") from e

def check_container_status(creation_id: str) -> Dict[str, Any]:
    """
    Checks the status code of a media container.

    Args:
        creation_id (str): Media container ID.

    Returns:
        Dict[str, Any]: Status dictionary containing status_code and optional error info.
    """
    access_token, _ = _get_credentials()
    url = f"{BASE_URL}/{creation_id}"
    params = {
        "fields": "status_code,status",
        "access_token": access_token
    }

    try:
        response = requests.get(url, params=params, timeout=20)
        data = response.json()
        if response.status_code == 200:
            return data
        logger.warning(f"Unable to fetch container status: {data.get('error', {})}")
        return {"status_code": "UNKNOWN"}
    except requests.RequestException as e:
        logger.warning(f"Error checking container status: {e}")
        return {"status_code": "UNKNOWN"}


def publish_post(creation_id: str) -> str:
    """
    Publishes a ready media container to Instagram.

    Args:
        creation_id (str): Media container ID to publish.

    Returns:
        str: Published media ID.
    """
    access_token, business_id = _get_credentials()
    url = f"{BASE_URL}/{business_id}/media_publish"

    payload = {
        "creation_id": creation_id,
        "access_token": access_token
    }

    logger.info(f"Publishing media container ID: {creation_id}")
    try:
        response = requests.post(url, data=payload, timeout=30)
        data = response.json()

        if response.status_code != 200 or "id" not in data:
            error_msg = data.get("error", {}).get("message", "Unknown error publishing post")
            logger.error(f"Failed to publish post: {error_msg} (Status: {response.status_code})")
            raise InstagramAPIError(f"Publish Post Error: {error_msg}")

        media_id = data["id"]
        logger.info(f"Post published successfully! Published Media ID: {media_id}")
        return media_id

    except requests.RequestException as e:
        logger.error(f"Network error during publish_post: {e}")
        raise InstagramAPIError(f"Network error publishing post: {e}") from e


def post_to_instagram(image_urls: list[str] | str, caption: str, max_retries: int = 3) -> Optional[str]:
    """
    Complete workflow to upload and publish a single image or carousel to Instagram.

    Args:
        image_urls (list[str] | str): Publicly accessible image URL(s).
        caption (str): Instagram post caption.
        max_retries (int): Maximum retry attempts.

    Returns:
        Optional[str]: Published media ID on success, None on failure.
    """
    retry_delay = 2

    # Normalize to list
    if isinstance(image_urls, str):
        image_urls = [image_urls]

    is_carousel = len(image_urls) > 1

    for attempt in range(1, max_retries + 1):
        logger.info(f"--- Instagram Post Attempt {attempt}/{max_retries} ---")
        try:
            if is_carousel:
                children_ids = []
                for idx, url in enumerate(image_urls):
                    logger.info(f"Uploading Carousel Item {idx+1}/{len(image_urls)}")
                    child_id = upload_image(url, is_carousel_item=True)
                    children_ids.append(child_id)
                
                # Wait for children to be ready
                for child_id in children_ids:
                    for _ in range(6):
                        status = check_container_status(child_id).get("status_code", "FINISHED")
                        if status == "FINISHED": break
                        time.sleep(3)

                creation_id = create_carousel_container(children_ids, caption)
            else:
                creation_id = upload_image(image_urls[0], caption)

            # Wait for main container
            status_ready = False
            for poll in range(8):
                time.sleep(4)
                status_info = check_container_status(creation_id)
                status_code = status_info.get("status_code", "FINISHED")
                logger.info(f"Container status check [{poll + 1}/8]: {status_code}")

                if status_code == "FINISHED":
                    status_ready = True
                    break
                elif status_code == "ERROR":
                    raise InstagramAPIError("Media container processing failed on Meta servers.")

            if not status_ready:
                logger.warning("Container status polling timed out, proceeding to attempt publish...")

            # Publish container
            media_id = publish_post(creation_id)
            return media_id

        except InstagramAPIError as e:
            logger.warning(f"Attempt {attempt} failed with API error: {e}")
            if attempt < max_retries:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                logger.error("All Instagram post attempts failed.")
                return None
        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt}: {e}", exc_info=True)
            return None

    return None


if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    test_image_url = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=1080&q=80"
    test_caption = "Hello Instagram 🚀 Testing automated posting module!"

    print("\n================ Testing post_instagram.py ================")
    published_id = post_to_instagram(test_image_url, test_caption)
    if published_id:
        print(f"\n✅ SUCCESS: Post published to Instagram! Media ID: {published_id}")
    else:
        print("\n❌ FAILURE: Could not publish post to Instagram.")
