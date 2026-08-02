import os
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader
from design_engine.themes import ThemeSystem

class LayoutEngine:
    """Calculates responsive typography sizes based on character lengths to prevent overflow."""

    @staticmethod
    def get_headline_class(headline: str) -> str:
        length = len(headline)
        if length < 25:
            return "text-6xl"
        elif length < 50:
            return "text-5xl"
        elif length < 80:
            return "text-4xl"
        else:
            return "text-3xl"

    @staticmethod
    def get_fact_class(fact: str) -> str:
        length = len(fact)
        if length < 100:
            return "text-3xl"
        elif length < 180:
            return "text-2xl"
        else:
            return "text-xl"


class PosterRenderer:
    """Renders Jinja2 HTML templates for the poster generator."""

    def __init__(self, templates_dir: str = "design_engine/templates"):
        self.env = Environment(loader=FileSystemLoader(templates_dir))

    def render_slide_html(self, data: Dict[str, Any], slide_index: int, slide: Dict[str, str], theme_override: str = None) -> str:
        category = data.get("category", "Did You Know?")
        theme = ThemeSystem.get_theme(theme_override)
        category_style = ThemeSystem.get_category_style(category)
        
        total_slides = len(data.get("slides", []))

        context = {
            "category": category,
            "slide_index": slide_index,
            "total_slides": total_slides,
            "slide_type": slide.get("type", "fact"),
            "slide_text": slide.get("text", ""),
            "theme": theme,
            "category_style": category_style
        }

        template = self.env.get_template("slide.html")
        return template.render(**context)
