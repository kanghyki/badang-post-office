"""
폰트 서비스

메모리에 로드된 폰트 데이터를 조회하는 기능을 제공합니다.
"""

from typing import List, Optional
from app.models.font import Font
from app.font_store import get_fonts as get_all_from_store, get_font as get_one_from_store


def get_all_fonts() -> List[Font]:
    """
    메모리에 로드된 모든 폰트 목록을 반환합니다.
    """
    return get_all_from_store()

def get_font_by_id(font_id: str) -> Optional[Font]:
    """
    ID로 특정 폰트를 찾아 반환합니다.
    """
    return get_one_from_store(font_id)
