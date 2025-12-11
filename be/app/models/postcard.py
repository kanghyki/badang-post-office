"""
엽서 관련 Pydantic 모델

엽서 생성 요청 및 응답의 구조를 정의합니다.
"""

from pydantic import BaseModel, field_validator, Field, ConfigDict
from typing import Optional, Literal
from uuid import UUID
from datetime import datetime, timedelta
import pytz


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
        """예약 시간 검증 (최소 5분 후, 최대 2년 이내)"""
        if v is None:
            return v
            
        now = datetime.utcnow()
        min_time = now + timedelta(minutes=5)
        max_time = now + timedelta(days=730)  # 2년
        
        # 입력이 타임존 aware인 경우 UTC로 변환
        if v.tzinfo is not None:
            v_utc = v.astimezone(pytz.UTC).replace(tzinfo=None)
        else:
            v_utc = v
        
        if v_utc < min_time:
            raise ValueError("예약 시간은 최소 5분 후여야 합니다.")
        if v_utc > max_time:
            raise ValueError("예약 시간은 최대 2년 이내여야 합니다.")
        
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
    status: Literal["writing", "pending", "sent", "failed", "cancelled"]
    scheduled_at: Optional[datetime] = None  # NULL이면 즉시 발송
    sent_at: Optional[datetime] = None
    postcard_path: Optional[str] = None  # 생성된 엽서 이미지 경로
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
            now = datetime.utcnow()
            min_time = now + timedelta(minutes=5)
            max_time = now + timedelta(days=730)
            
            if v.tzinfo is not None:
                v_utc = v.astimezone(pytz.UTC).replace(tzinfo=None)
            else:
                v_utc = v
            
            if v_utc < min_time:
                raise ValueError("예약 시간은 최소 5분 후여야 합니다.")
            if v_utc > max_time:
                raise ValueError("예약 시간은 최대 2년 이내여야 합니다.")
            
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

