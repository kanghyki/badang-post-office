from celery import Celery
import os

# Redis 연결 설정 (환경 변수 또는 기본값)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Celery 앱 초기화
celery_app = Celery(
    "jeju_postcard",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks"]  # 작업이 정의된 모듈
)

# 설정 최적화
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Seoul",
    enable_utc=True,
    # 작업 실패 시 재시도 설정 (선택 사항)
    task_acks_late=True,
)
