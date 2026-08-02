import os
import asyncio
import logging
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright
from design_engine.render import PosterRenderer

logger = logging.getLogger("PosterGenerator")


class PosterGenerator:
    """
    Playwright-based High-DPI Poster Generation System.
    Renders HTML + Tailwind into 1080x1350 Instagram Ready PNG posters.
    """

    def __init__(self, output_dir: str = "design_engine/generated"):
        self.output_dir = output_dir
        self.renderer = PosterRenderer()
        os.makedirs(self.output_dir, exist_ok=True)

    async def render_carousel_async(self, data: Dict[str, Any], base_filename: str, theme_override: Optional[str] = None) -> list[str]:
        output_paths = []
        slides = data.get("slides", [])
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1080, "height": 1350},
                device_scale_factor=2
            )
            page = await context.new_page()

            for i, slide in enumerate(slides):
                html_content = self.renderer.render_slide_html(data, i + 1, slide, theme_override)
                
                output_filename = f"{base_filename}_slide_{i+1}.png"
                output_path = os.path.abspath(os.path.join(self.output_dir, output_filename))
                
                await page.set_content(html_content, wait_until="networkidle")
                await page.wait_for_timeout(300)
                await page.screenshot(path=output_path, type="png")
                output_paths.append(output_path)

            await browser.close()

        logger.info(f"Carousel successfully generated: {len(output_paths)} slides")
        return output_paths

    def generate_carousel(self, data: Dict[str, Any], base_filename: str = "poster", theme_override: Optional[str] = None) -> list[str]:
        """Synchronous wrapper for generating a carousel."""
        logger.info(f"Generating carousel for category: '{data.get('category')}'...")
        return asyncio.run(self.render_carousel_async(data, base_filename, theme_override))


if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    logging.basicConfig(level=logging.INFO)
    generator = PosterGenerator()

    sample_data = {
        "category": "Psychology",
        "topic": "Embarrassing Memories",
        "slides": [
            {"type": "hook", "text": "Your brain is lying to you at 2 AM."},
            {"type": "fact", "text": "Your brain replays embarrassing moments at night because it consolidates emotional memories during REM sleep."},
            {"type": "explanation", "text": "Evolutionarily, your brain prioritizes negative experiences to keep you safe from repeating social mistakes."},
            {"type": "engagement", "text": "What's the most random memory that keeps you awake? 👇 Comment below!"}
        ]
    }

    poster_files = generator.generate_carousel(sample_data, "sample_carousel")
    print(f"\n✅ Carousel Generation Test Completed: {len(poster_files)} slides generated.")
