"""
엽서 관련 Pydantic 모델

엽서 생성 요청 및 응답의 구조를 정의합니다.
"""

from pydantic import BaseModel, validator
from typing import Optional
from uuid import UUID
from datetime import datetime


class PostcardCreateRequest(BaseModel):
    """
    엽서 생성 요청 (Form Data로 전송됨)

    Note: 실제 API에서는 Form과 File을 사용하므로 이 모델은 문서화 목적입니다.
    """
    template_id: str
    text: str
    sender_name: Optional[str] = None

    @validator("text")
    def validate_text_length(cls, v):
        """텍스트 길이 검증 (최대 100자)"""
        if len(v) > 100:
            raise ValueError("텍스트는 최대 100자까지 입력 가능합니다.")
        return v


class PostcardResponse(BaseModel):
    """
    엽서 생성 응답

    생성된 엽서의 정보를 반환합니다.
    """
    postcard_id: str
    postcard_path: str
    template_id: str
    text: str
    sender_name: Optional[str] = None
    created_at: datetime
    email_sent: bool = False
    recipient_email: Optional[str] = None

    class Config:
        from_attributes = True


class PostcardDB(BaseModel):
    """
    DB에 저장된 엽서 (전체 필드)

    SQLite postcards 테이블의 레코드를 표현합니다.
    """
    id: str
    template_id: Optional[str] = None
    text_content: str
    user_photo_path: Optional[str] = None
    postcard_image_path: str
    user_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

