"""
인메모리 폰트 저장소

서버 시작 시 static/fonts/ 디렉토리의 .json 파일들을 로드하여
폰트 데이터를 메모리에 저장하고 관리합니다.
"""
import os
import json
import logging
from typing import List, Optional
from app.models.font import Font

logger = logging.getLogger(__name__)

# 전역 변수로 폰트 목록을 메모리에 저장
FONTS: List[Font] = []
FONT_DIR = "static/fonts"


def load_fonts():
    """
    FONT_DIR에서 .json 파일들을 읽어 FONTS 리스트를 채웁니다.
    서버 시작 시 호출됩니다.
    """
    global FONTS
    FONTS = []
    
    if not os.path.exists(FONT_DIR):
        logger.warning(f"Font directory does not exist: {FONT_DIR}")
        return

    logger.info("Loading fonts...")
    for filename in os.listdir(FONT_DIR):
        if filename.endswith(".json"):
            file_path = os.path.join(FONT_DIR, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    font = Font(**data)
                    FONTS.append(font)
            except Exception as e:
                logger.error(f"Failed to load font '{filename}': {e}")
    
    # display_order를 기준으로 정렬
    FONTS.sort(key=lambda f: f.display_order)
    
    logger.info(f"✅ {len(FONTS)} fonts loaded into memory")


def get_fonts() -> List[Font]:
    """메모리에 로드된 모든 폰트 목록을 반환합니다."""
    return FONTS


def get_font(font_id: str) -> Optional[Font]:
    """ID로 특정 폰트를 찾아 반환합니다."""
    for font in FONTS:
        if font.id == font_id:
            return font
    return None
