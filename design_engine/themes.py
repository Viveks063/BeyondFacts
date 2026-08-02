import random
from typing import Dict, Any, Optional

class ThemeSystem:
    """Design System Theme Definitions for Beyond Facts Posters."""

    THEMES: Dict[str, Dict[str, str]] = {
        "dark_glass": {
            "name": "Dark Glass",
            "body_class": "bg-[#0B0F17] text-white",
            "card_class": "glass-card text-white",
            "badge_bg": "bg-white/5",
            "border_color": "border-white/10",
            "text_primary": "text-white",
            "text_secondary": "text-slate-300",
            "accent_glow": "bg-indigo-600"
        },
        "white_minimal": {
            "name": "White Minimal",
            "body_class": "bg-[#F8FAFC] text-slate-900",
            "card_class": "glass-card-light text-slate-900 shadow-xl",
            "badge_bg": "bg-slate-200/60",
            "border_color": "border-slate-300/80",
            "text_primary": "text-slate-950",
            "text_secondary": "text-slate-600",
            "accent_glow": "bg-sky-400"
        },
        "blue_gradient": {
            "name": "Blue Gradient",
            "body_class": "bg-gradient-to-br from-[#0A192F] via-[#0F2A4A] to-[#020C1B] text-white",
            "card_class": "glass-card text-white border-cyan-500/20",
            "badge_bg": "bg-cyan-500/10",
            "border_color": "border-cyan-500/30",
            "text_primary": "text-white",
            "text_secondary": "text-cyan-100",
            "accent_glow": "bg-cyan-500"
        },
        "purple_neon": {
            "name": "Purple Neon",
            "body_class": "bg-[#0F0728] text-white",
            "card_class": "glass-card text-white border-purple-500/20",
            "badge_bg": "bg-purple-500/10",
            "border_color": "border-purple-500/30",
            "text_primary": "text-white",
            "text_secondary": "text-purple-200",
            "accent_glow": "bg-fuchsia-600"
        },
        "gold_luxury": {
            "name": "Gold Luxury",
            "body_class": "bg-[#0D0B07] text-amber-50",
            "card_class": "glass-card text-amber-50 border-amber-500/20",
            "badge_bg": "bg-amber-500/10",
            "border_color": "border-amber-500/30",
            "text_primary": "text-amber-50",
            "text_secondary": "text-amber-200/80",
            "accent_glow": "bg-amber-600"
        }
    }

    CATEGORY_STYLES: Dict[str, Dict[str, str]] = {
        "Psychology": {
            "icon": "brain",
            "icon_color": "text-purple-400",
            "glow_bg": "bg-purple-600",
            "accent_line": "bg-purple-500",
            "logo_bg": "bg-gradient-to-br from-purple-500 to-indigo-600"
        },
        "Did You Know?": {
            "icon": "sparkles",
            "icon_color": "text-amber-400",
            "glow_bg": "bg-amber-500",
            "accent_line": "bg-amber-400",
            "logo_bg": "bg-gradient-to-br from-amber-400 to-orange-500"
        },
        "Science": {
            "icon": "atom",
            "icon_color": "text-sky-400",
            "glow_bg": "bg-sky-600",
            "accent_line": "bg-sky-400",
            "logo_bg": "bg-gradient-to-br from-sky-400 to-blue-600"
        },
        "History": {
            "icon": "scroll",
            "icon_color": "text-amber-600",
            "glow_bg": "bg-amber-800",
            "accent_line": "bg-amber-600",
            "logo_bg": "bg-gradient-to-br from-amber-600 to-yellow-800"
        },
        "Cars": {
            "icon": "gauge",
            "icon_color": "text-rose-500",
            "glow_bg": "bg-rose-600",
            "accent_line": "bg-rose-500",
            "logo_bg": "bg-gradient-to-br from-rose-500 to-red-700"
        },
        "Space": {
            "icon": "globe",
            "icon_color": "text-indigo-400",
            "glow_bg": "bg-indigo-600",
            "accent_line": "bg-indigo-400",
            "logo_bg": "bg-gradient-to-br from-indigo-500 to-purple-800"
        },
        "Geography": {
            "icon": "compass",
            "icon_color": "text-teal-400",
            "glow_bg": "bg-teal-600",
            "accent_line": "bg-teal-400",
            "logo_bg": "bg-gradient-to-br from-teal-400 to-emerald-600"
        },
        "Animals": {
            "icon": "leaf",
            "icon_color": "text-emerald-400",
            "glow_bg": "bg-emerald-600",
            "accent_line": "bg-emerald-400",
            "logo_bg": "bg-gradient-to-br from-emerald-400 to-green-600"
        },
        "Technology": {
            "icon": "cpu",
            "icon_color": "text-cyan-400",
            "glow_bg": "bg-cyan-600",
            "accent_line": "bg-cyan-400",
            "logo_bg": "bg-gradient-to-br from-cyan-400 to-blue-600"
        },
        "Money & Business": {
            "icon": "trending-up",
            "icon_color": "text-emerald-500",
            "glow_bg": "bg-emerald-600",
            "accent_line": "bg-emerald-500",
            "logo_bg": "bg-gradient-to-br from-emerald-500 to-teal-700"
        }
    }

    @classmethod
    def get_theme(cls, theme_name: Optional[str] = None) -> Dict[str, str]:
        if theme_name and theme_name in cls.THEMES:
            return cls.THEMES[theme_name]
        return random.choice(list(cls.THEMES.values()))

    @classmethod
    def get_category_style(cls, category: str) -> Dict[str, str]:
        return cls.CATEGORY_STYLES.get(category, cls.CATEGORY_STYLES["Did You Know?"])
