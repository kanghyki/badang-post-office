"""
템플릿 관련 Pydantic 모델

엽서 템플릿의 구조와 검증 로직을 정의합니다.
인메모리 및 파일 기반 아키텍처를 따릅니다.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid as uuid_lib


class TextConfig(BaseModel):
    """텍스트 레이아웃 설정"""
    id: str
    x: int
    y: int
    font_size: int = 28
    color: str = "black"
    align: str = "center"
    line_height: float = 1.2  # 줄 높이 비율 (1.0 = 100%, 1.5 = 150%)
    max_width: Optional[int] = None
    max_height: Optional[int] = None
    font_id: Optional[str] = None


class PhotoConfig(BaseModel):
    """사진 레이아웃 설정"""
    id: str
    x: int
    y: int
    max_width: Optional[int] = None
    max_height: Optional[int] = None
    effects: Optional[Dict[str, Any]] = None  # 이미지 효과 설정 (grayscale, sepia, blur, brightness, contrast 등)


class Template(BaseModel):
    """
    템플릿 파일(JSON)의 구조를 정의하는 Pydantic 모델.
    이 모델이 템플릿 데이터의 기준(source of truth)이 됩니다.
    """
    id: str = Field(default_factory=lambda: str(uuid_lib.uuid4()))
    name: str
    description: Optional[str] = None
    template_image_path: str
    width: int
    height: int
    text_configs: List[TextConfig] = []
    photo_configs: List[PhotoConfig] = []
    default_font_id: Optional[str] = None
    display_order: int = 0


class TemplateResponse(BaseModel):
    """
    API 응답용 템플릿 (간소화)
    사용자에게 보여줄 템플릿 정보만 포함합니다.
    """
    id: str
    name: str
    description: Optional[str] = None
    template_image_path: str
    width: int
    height: int
    supports_photo: bool

    @classmethod
    def from_template(cls, template: Template) -> "TemplateResponse":
        """
        Template 모델로부터 TemplateResponse를 생성합니다.
        """
        return cls(
            id=template.id,
            name=template.name,
            description=template.description,
            template_image_path=template.template_image_path,
            width=template.width,
            height=template.height,
            supports_photo=len(template.photo_configs) > 0,
        )


class TemplateListResponse(BaseModel):
    """템플릿 목록 응답"""
    templates: List[TemplateResponse]


class TemplateUpdateRequest(BaseModel):
    """템플릿 설정 업데이트 요청 (편집기용)"""
    text_configs: Optional[List[TextConfig]] = None
    photo_configs: Optional[List[PhotoConfig]] = None
    default_font_id: Optional[str] = None

