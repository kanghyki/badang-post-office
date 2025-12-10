"""
폰트 관리 모듈

font_id를 기반으로 폰트를 동적으로 로드하고 캐싱합니다.
"""

import os
from typing import Optional, Dict, Tuple
from PIL import ImageFont
from app.services.font_service import get_font_by_id


class FontManager:
    """font_id 기반 폰트 동적 로드 및 캐싱"""

    def __init__(self):
        """캐시 초기화"""
        self.cache: Dict[Tuple[Optional[str], int], ImageFont.FreeTypeFont] = {}

    def get_font(self, font_id: Optional[str] = None, size: int = 28) -> ImageFont.FreeTypeFont:
        """
        font_id와 크기로 폰트를 로드합니다.

        Args:
            font_id: 폰트 ID (None이면 기본 폰트)
            size: 폰트 크기 (픽셀), 기본값 28

        Returns:
            PIL ImageFont 객체
        """
        cache_key = (font_id, size)

        if cache_key in self.cache:
            return self.cache[cache_key]

        font = None

        if font_id:
            try:
                font_data = get_font_by_id(font_id)
                if font_data and os.path.exists(font_data.font_path):
                    font = ImageFont.truetype(font_data.font_path, size)
            except Exception:
                pass

        if font is None:
            font = ImageFont.load_default()

        self.cache[cache_key] = font
        return font

