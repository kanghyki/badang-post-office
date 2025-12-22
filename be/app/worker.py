import os
from celery import Celery
from app.config import settings

# Celery 인스턴스 생성
# broker: 작업 큐 (Redis)
# backend: 작업 결과 저장 (선택 사항)
celery_app = Celery(
    "badang_worker",
    broker=f"redis://{os.getenv('REDIS_HOST', 'localhost')}:6379/0",
    backend=f"redis://{os.getenv('REDIS_HOST', 'localhost')}:6379/0",
    include=["app.tasks"]
)

# Celery 설정
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Seoul",
    enable_utc=True,
    task_acks_late=True,  # 작업이 성공적으로 끝난 후 ACK (안정성)
    worker_prefetch_multiplier=1,  # 한 번에 하나의 작업만 가져옴 (이미지 처리는 무거우므로)
)

if __name__ == "__main__":
    celery_app.start()
