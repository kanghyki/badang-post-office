"""
Template service

Provides functionality to query and manage template data.
"""

from typing import List, Optional
import json
import os
from app.models.template import Template
from app.template_store import (
    get_templates as get_all_from_store,
    get_template as get_one_from_store,
)

TEMPLATE_DIR = "static/templates"


def get_all_templates() -> List[Template]:
    """
    Load and return all templates.
    """
    return get_all_from_store()


def get_template_by_id(template_id: str) -> Optional[Template]:
    """
    Load and return a specific template by ID.
    """
    return get_one_from_store(template_id)


def save_template_to_disk(template_data: Template) -> Template:
    """
    Save template data to a JSON file.
    File name uses the template's ID (e.g., {id}.json)
    (Used by development utility API)

    Args:
        template_data: Template data to save (Pydantic model)

    Returns:
        Saved template data
    """
    filename = f"{template_data.id}.json"
    file_path = os.path.join(TEMPLATE_DIR, filename)

    # Validate uniqueness of text and photo config IDs
    text_config_ids = [cfg.id for cfg in template_data.text_configs]
    if len(text_config_ids) != len(set(text_config_ids)):
        raise ValueError("Text config IDs must be unique within the template.")

    photo_config_ids = [cfg.id for cfg in template_data.photo_configs]
    if len(photo_config_ids) != len(set(photo_config_ids)):
        raise ValueError("Photo config IDs must be unique within the template.")
    
    try:
        # Ensure directory exists
        os.makedirs(TEMPLATE_DIR, exist_ok=True)
        
        # Convert Pydantic model to dict, then to JSON with indentation
        template_dict = template_data.model_dump(exclude_none=True)
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(template_dict, f, indent=4, ensure_ascii=False)

        # Return the template data itself (already validated)
        return template_data

    except Exception as e:
        raise


def delete_template_from_disk(template_id: str) -> bool:
    """
    Delete a template JSON file.
    (Used by development utility API)

    Args:
        template_id: ID of the template to delete

    Returns:
        True if deletion was successful, False otherwise
    """
    filename = f"{template_id}.json"
    file_path = os.path.join(TEMPLATE_DIR, filename)

    try:
        if not os.path.exists(file_path):
            return False

        os.remove(file_path)
        return True

    except Exception as e:
        raise
