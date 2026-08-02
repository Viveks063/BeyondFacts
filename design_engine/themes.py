"""
Design System Theme Definitions for Beyond Facts.
Minimalist, Soft, Editorial aesthetics.
"""

from typing import Dict, Any, Optional
import random

class ThemeSystem:
    """Soft, Minimal, & Editorial Design System Themes."""

    THEMES: Dict[str, Dict[str, str]] = {
        "soft_oat": {
            "name": "Soft Oat",
            "body_class": "bg-[#F9F8F3] text-[#1F1F1F]",
            "card_class": "bg-[#F2F0E8] border border-black/[0.04] text-[#1F1F1F]",
            "badge_bg": "bg-black/[0.04]",
            "border_color": "border-black/[0.06]",
            "text_primary": "text-[#1F1F1F]",
            "text_secondary": "text-[#666460]",
            "accent_pill": "bg-[#E8E5DC] text-[#2C2B29]"
        },
        "minimal_graphite": {
            "name": "Minimal Graphite",
            "body_class": "bg-[#141416] text-[#F3F3F1]",
            "card_class": "bg-[#1E1E22] border border-white/[0.06] text-[#F3F3F1]",
            "badge_bg": "bg-white/[0.06]",
            "border_color": "border-white/[0.08]",
            "text_primary": "text-[#F3F3F1]",
            "text_secondary": "text-[#A0A0A6]",
            "accent_pill": "bg-[#28282E] text-[#F3F3F1]"
        },
        "soft_sage": {
            "name": "Nordic Sage",
            "body_class": "bg-[#F0F4F2] text-[#1C2A26]",
            "card_class": "bg-[#E5ECE9] border border-black/[0.04] text-[#1C2A26]",
            "badge_bg": "bg-black/[0.04]",
            "border_color": "border-black/[0.06]",
            "text_primary": "text-[#1C2A26]",
            "text_secondary": "text-[#556963]",
            "accent_pill": "bg-[#DAE4E0] text-[#1C2A26]"
        },
        "warm_linen": {
            "name": "Warm Linen",
            "body_class": "bg-[#F7F3EE] text-[#2B231F]",
            "card_class": "bg-[#EDE6DE] border border-black/[0.04] text-[#2B231F]",
            "badge_bg": "bg-black/[0.04]",
            "border_color": "border-black/[0.06]",
            "text_primary": "text-[#2B231F]",
            "text_secondary": "text-[#6E635C]",
            "accent_pill": "bg-[#E2D8CC] text-[#2B231F]"
        },
        "editorial_white": {
            "name": "Editorial White",
            "body_class": "bg-[#FAFAFA] text-[#111111]",
            "card_class": "bg-[#F1F1F1] border border-black/[0.05] text-[#111111]",
            "badge_bg": "bg-black/[0.04]",
            "border_color": "border-black/[0.08]",
            "text_primary": "text-[#111111]",
            "text_secondary": "text-[#555555]",
            "accent_pill": "bg-[#E5E5E5] text-[#111111]"
        }
    }

    CATEGORY_STYLES: Dict[str, Dict[str, str]] = {
        "Psychology": {"label": "Psychology", "tag": "MENTAL MODEL"},
        "Cars": {"label": "Automotive", "tag": "DESIGN & ENGINEERING"},
        "History": {"label": "History", "tag": "ARCHIVE"},
        "Science": {"label": "Science", "tag": "DISCOVERY"},
        "Animals": {"label": "Nature", "tag": "WILDLIFE"},
        "Money": {"label": "Economics", "tag": "CAPITAL"},
        "Space": {"label": "Cosmos", "tag": "ASTROPHYSICS"},
        "Random": {"label": "Curiosity", "tag": "UNCOVERED"},
        "Did You Know?": {"label": "Curiosity", "tag": "FACT"},
        "Technology": {"label": "Technology", "tag": "FUTURE"}
    }

    @classmethod
    def get_theme(cls, theme_name: Optional[str] = None) -> Dict[str, str]:
        if theme_name and theme_name in cls.THEMES:
            return cls.THEMES[theme_name]
        return random.choice(list(cls.THEMES.values()))

    @classmethod
    def get_category_style(cls, category: str) -> Dict[str, str]:
        return cls.CATEGORY_STYLES.get(category, {"label": category, "tag": "INSIGHT"})
