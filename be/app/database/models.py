"""
SQLAlchemy 데이터베이스 모델

템플릿과 엽서 데이터를 저장하는 테이블 정의
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


class User(Base):
    """사용자 테이블"""
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Postcard(Base):
    """엽서 테이블 (즉시 발송 및 예약 발송 통합)"""
    __tablename__ = "postcards"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    template_id = Column(String, nullable=False)
    text_contents = Column(JSON)  # {"text_config_id": "text", ...} - 제주어 번역본
    original_text_contents = Column(JSON)  # 원본 텍스트 (번역 전)
    user_photo_paths = Column(JSON)  # {"photo_config_id": "path", ...}
    
    # 수신자 정보
    recipient_email = Column(String)  # 빈 엽서 생성 시 nullable
    recipient_name = Column(String)
    sender_name = Column(String)
    
    # 발송 상태 및 스케줄링
    status = Column(String, default="writing")  # writing, pending, sent, failed, cancelled
    scheduled_at = Column(DateTime)  # 발송 예정 시간 (NULL이면 즉시 발송)
    sent_at = Column(DateTime)  # 실제 발송 시간
    
    # 생성된 엽서 이미지 (발송 후 생성)
    postcard_image_path = Column(String)  # NULL이면 아직 생성 안됨
    error_message = Column(Text)  # 실패 시 오류 메시지
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


