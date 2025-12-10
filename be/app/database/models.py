"""
SQLAlchemy 데이터베이스 모델

템플릿과 엽서 데이터를 저장하는 테이블 정의
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


class Postcard(Base):
    """엽서 테이블"""
    __tablename__ = "postcards"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    template_id = Column(String)
    text_contents = Column(JSON, nullable=False)  # {"text_config_id": "text", ...}
    user_photo_paths = Column(JSON)  # {"photo_config_id": "path", ...}
    postcard_image_path = Column(String, nullable=False)  # 생성된 엽서 이미지 경로
    sender_name = Column(String)  # 발신자 이름
    user_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


