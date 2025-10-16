"""Initializes ggpyscraper package"""
from .parse_liquipedia import parse_liquipedia_html, parse_liquipedia_wc, parse_multiple_liquipedia_pages
from .liquipedia_objects import liquipedia_page, player, team, tournament

__all__ = [
    "parse_liquipedia_html",
    "parse_liquipedia_wc",
    "parse_multiple_liquipedia_pages",
    "liquipedia_page",
    "player",
    "team",
    "tournament"
]
