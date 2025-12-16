"""
엽서 관련 Pydantic 모델

엽서 생성 요청 및 응답의 구조를 정의합니다.
"""

from pydantic import BaseModel, field_validator, Field, ConfigDict
from typing import Optional, Literal
from uuid import UUID
from datetime import datetime, timedelta
from app.utils.timezone import to_utc, validate_schedule_time


class PostcardCreateRequest(BaseModel):
    """
    엽서 생성/발송 요청
    
    scheduled_at이 없으면 즉시 발송, 있으면 예약 발송
    """
    template_id: str
    text: str
    recipient_email: str
    recipient_name: Optional[str] = None
    sender_name: Optional[str] = None
    scheduled_at: Optional[datetime] = Field(None, description="발송 예정 시간 (없으면 즉시 발송)")

    @field_validator("text")
    @classmethod
    def validate_text_length(cls, v: str) -> str:
        """텍스트 길이 검증 (최대 500자)"""
        if len(v) > 500:
            raise ValueError("텍스트는 최대 500자까지 입력 가능합니다.")
        return v
    
    @field_validator("scheduled_at")
    @classmethod
    def validate_scheduled_time(cls, v: Optional[datetime]) -> Optional[datetime]:
        """예약 시간 검증 (과거 시간이면 즉시발송, 최대 2년 이내)"""
        if v is None:
            return v

        from app.utils.timezone import now_utc

        # UTC timezone-aware로 변환
        v_utc = to_utc(v)

        # 과거 시간이면 None으로 변경 (즉시발송)
        if v_utc <= now_utc():
            return None

        # 최대 시간 검증만 수행 (최소 시간 제한 제거)
        is_valid, error = validate_schedule_time(v_utc, min_minutes=0, max_days=730)
        if not is_valid:
            raise ValueError(error)

        return v_utc


class PostcardResponse(BaseModel):
    """
    엽서 응답

    생성된 엽서의 정보를 반환합니다.
    """
    id: str
    template_id: str
    text: Optional[str] = None  # 제주어 번역본 (빈 엽서 시 None)
    original_text: Optional[str] = None  # 원본 (표준어)
    recipient_email: Optional[str] = None  # 빈 엽서 시 None
    recipient_name: Optional[str] = None
    sender_name: Optional[str] = None
    status: Literal["writing", "pending", "processing", "sent", "failed"]
    scheduled_at: Optional[datetime] = None  # NULL이면 즉시 발송
    sent_at: Optional[datetime] = None
    postcard_path: Optional[str] = None  # 생성된 엽서 이미지 경로
    user_photo_url: Optional[str] = None  # 사용자 업로드 사진 URL (첫 번째 사진)
    jeju_photo_url: Optional[str] = None  # 제주 스타일 변환 이미지 URL
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PostcardUpdateRequest(BaseModel):
    """엽서 수정 요청 (pending 상태만 가능)"""
    scheduled_at: Optional[datetime] = Field(None, description="새로운 발송 예정 시간")
    text: Optional[str] = Field(None, description="새로운 텍스트")
    recipient_email: Optional[str] = None
    recipient_name: Optional[str] = None
    sender_name: Optional[str] = None

    @field_validator("text")
    @classmethod
    def validate_text_length(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) > 500:
            raise ValueError("텍스트는 최대 500자까지 입력 가능합니다.")
        return v

    @field_validator("scheduled_at")
    @classmethod
    def validate_scheduled_time(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v:
            from app.utils.timezone import now_utc

            v_utc = to_utc(v)

            # 과거 시간이면 None으로 변경 (즉시발송)
            if v_utc <= now_utc():
                return None

            # 최대 시간 검증만 수행 (최소 시간 제한 제거)
            is_valid, error = validate_schedule_time(v_utc, min_minutes=0, max_days=730)
            if not is_valid:
                raise ValueError(error)
            return v_utc
        return v


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

    model_config = ConfigDict(from_attributes=True)

