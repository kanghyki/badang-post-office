"""
인메모리 템플릿 저장소

서버 시작 시 static/templates/ 디렉토리의 .json 파일들을 로드하여
템플릿 데이터를 메모리에 저장하고 관리합니다.
"""
import os
import json
import logging
from typing import List, Optional
from app.models.template import Template

logger = logging.getLogger(__name__)

# 전역 변수로 템플릿 목록을 메모리에 저장
TEMPLATES: List[Template] = []
TEMPLATE_DIR = "static/templates"


def load_templates():
    """
    TEMPLATE_DIR에서 .json 파일들을 읽어 TEMPLATES 리스트를 채웁니다.
    서버 시작 시 호출됩니다.
    """
    global TEMPLATES
    TEMPLATES = []
    
    if not os.path.exists(TEMPLATE_DIR):
        logger.warning(f"Template directory does not exist: {TEMPLATE_DIR}")
        return

    logger.info("Loading templates...")
    for filename in os.listdir(TEMPLATE_DIR):
        if filename.endswith(".json"):
            file_path = os.path.join(TEMPLATE_DIR, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    template = Template(**data)
                    TEMPLATES.append(template)
            except Exception as e:
                logger.error(f"Failed to load template '{filename}': {e}")
    
    # display_order를 기준으로 정렬
    TEMPLATES.sort(key=lambda t: t.display_order)
    
    logger.info(f"✅ {len(TEMPLATES)} templates loaded into memory")


def get_templates() -> List[Template]:
    """메모리에 로드된 모든 템플릿 목록을 반환합니다."""
    return TEMPLATES


def get_template(template_id: str) -> Optional[Template]:
    """ID로 특정 템플릿을 찾아 반환합니다."""
    for template in TEMPLATES:
        if template.id == template_id:
            return template
    return None

