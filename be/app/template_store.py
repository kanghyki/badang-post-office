"""
Dynamic template loader

Loads template JSON files from static/templates/ directory on-demand.
"""
import os
import json
import logging
from typing import List, Optional
from app.models.template import Template

logger = logging.getLogger(__name__)

TEMPLATE_DIR = "static/templates"


def get_templates() -> List[Template]:
    """Load and return all templates from the template directory."""
    templates = []
    
    if not os.path.exists(TEMPLATE_DIR):
        logger.warning(f"Template directory does not exist: {TEMPLATE_DIR}")
        return templates

    for filename in os.listdir(TEMPLATE_DIR):
        if filename.endswith(".json"):
            file_path = os.path.join(TEMPLATE_DIR, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    template = Template(**data)
                    templates.append(template)
            except Exception as e:
                logger.error(f"Failed to load template '{filename}': {e}")
    
    # Sort by display_order
    templates.sort(key=lambda t: t.display_order)
    
    return templates


def get_template(template_id: str) -> Optional[Template]:
    """Load and return a specific template by ID."""
    if not os.path.exists(TEMPLATE_DIR):
        logger.warning(f"Template directory does not exist: {TEMPLATE_DIR}")
        return None

    for filename in os.listdir(TEMPLATE_DIR):
        if filename.endswith(".json"):
            file_path = os.path.join(TEMPLATE_DIR, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    template = Template(**data)
                    if template.id == template_id:
                        return template
            except Exception as e:
                logger.error(f"Failed to load template '{filename}': {e}")
    
    return None

