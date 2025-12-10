"""
Dynamic font loader

Loads font JSON files from static/fonts/ directory on-demand.
"""
import os
import json
import logging
from typing import List, Optional
from app.models.font import Font

logger = logging.getLogger(__name__)

FONT_DIR = "static/fonts"


def get_fonts() -> List[Font]:
    """Load and return all fonts from the font directory."""
    fonts = []
    
    if not os.path.exists(FONT_DIR):
        logger.warning(f"Font directory does not exist: {FONT_DIR}")
        return fonts

    for filename in os.listdir(FONT_DIR):
        if filename.endswith(".json"):
            file_path = os.path.join(FONT_DIR, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    font = Font(**data)
                    fonts.append(font)
            except Exception as e:
                logger.error(f"Failed to load font '{filename}': {e}")
    
    # Sort by display_order
    fonts.sort(key=lambda f: f.display_order)
    
    return fonts


def get_font(font_id: str) -> Optional[Font]:
    """Load and return a specific font by ID."""
    if not os.path.exists(FONT_DIR):
        logger.warning(f"Font directory does not exist: {FONT_DIR}")
        return None

    for filename in os.listdir(FONT_DIR):
        if filename.endswith(".json"):
            file_path = os.path.join(FONT_DIR, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    font = Font(**data)
                    if font.id == font_id:
                        return font
            except Exception as e:
                logger.error(f"Failed to load font '{filename}': {e}")
    
    return None
