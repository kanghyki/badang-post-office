"""
폰트 관련 Pydantic 모델

폰트의 구조와 검증 로직을 정의합니다.
인메모리 및 파일 기반 아키텍처를 따릅니다.
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class Font(BaseModel):
    """
    폰트 파일(JSON)의 구조를 정의하는 Pydantic 모델.
    이 모델이 폰트 데이터의 기준(source of truth)이 됩니다.
    """
    id: str
    name: str
    description: Optional[str] = None
    font_path: str
    category: Optional[str] = None
    display_order: int = 0


class FontResponse(BaseModel):
    """
    API 응답용 폰트 (간소화)
    """
    id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None

    @classmethod
    def from_font(cls, font: Font) -> "FontResponse":
        """
        Font 모델로부터 FontResponse를 생성합니다.
        """
        return cls(
            id=font.id,
            name=font.name,
            description=font.description,
            category=font.category
        )


class FontListResponse(BaseModel):
    """폰트 목록 응답"""
    fonts: List[FontResponse]
