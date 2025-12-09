"""
템플릿 서비스

메모리에 로드된 템플릿 데이터를 조회하고,
개발용으로 JSON 파일에 저장하는 기능을 제공합니다.
"""

from typing import List, Optional
import json
import os
from app.models.template import Template
from app.template_store import (
    get_templates as get_all_from_store,
    get_template as get_one_from_store,
    load_templates,
)

TEMPLATE_DIR = "static/templates"


def get_all_templates() -> List[Template]:
    """
    메모리에 로드된 모든 템플릿 목록을 반환합니다.
    """
    return get_all_from_store()


def get_template_by_id(template_id: str) -> Optional[Template]:
    """
    ID로 특정 템플릿을 찾아 반환합니다.
    """
    return get_one_from_store(template_id)


def save_template_to_disk(template_data: Template) -> Template:
    """
    템플릿 데이터를 JSON 파일로 저장/덮어쓰기하고, 메모리를 리로드합니다.
    파일 이름은 템플릿의 ID를 사용합니다. (예: {id}.json)
    (개발용 유틸리티 API에서 사용)

    Args:
        template_data: 저장할 템플릿 데이터 (Pydantic 모델)

    Returns:
        저장된 템플릿 데이터
    """
    filename = f"{template_data.id}.json"
    file_path = os.path.join(TEMPLATE_DIR, filename)

    # 텍스트 및 사진 설정 ID의 고유성 검증
    text_config_ids = [cfg.id for cfg in template_data.text_configs]
    if len(text_config_ids) != len(set(text_config_ids)):
        raise ValueError("텍스트 설정 ID는 템플릿 내에서 고유해야 합니다.")

    photo_config_ids = [cfg.id for cfg in template_data.photo_configs]
    if len(photo_config_ids) != len(set(photo_config_ids)):
        raise ValueError("사진 설정 ID는 템플릿 내에서 고유해야 합니다.")
    
    try:
        # Pydantic 모델을 JSON 문자열로 변환 (들여쓰기로 가독성 확보)
        json_data = template_data.model_dump_json(indent=4)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(json_data)

        # 파일 저장 후, 메모리의 템플릿 목록을 다시 로드하여 즉시 반영
        load_templates()

        # 리로드된 데이터에서 방금 저장한 템플릿을 찾아 반환
        return get_template_by_id(template_data.id)

    except Exception as e:
        raise


def delete_template_from_disk(template_id: str) -> bool:
    """
    템플릿 JSON 파일을 삭제하고, 메모리를 리로드합니다.
    (개발용 유틸리티 API에서 사용)

    Args:
        template_id: 삭제할 템플릿의 ID

    Returns:
        삭제 성공 여부
    """
    filename = f"{template_id}.json"
    file_path = os.path.join(TEMPLATE_DIR, filename)

    try:
        if not os.path.exists(file_path):
            return False

        os.remove(file_path)

        # 파일 삭제 후, 메모리의 템플릿 목록을 다시 로드하여 즉시 반영
        load_templates()
        return True

    except Exception as e:
        raise
