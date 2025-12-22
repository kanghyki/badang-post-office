import asyncio
import logging
from app.worker import celery_app
from app.database.database import get_db_session
from app.services.postcard_service import PostcardService

logger = logging.getLogger(__name__)

@celery_app.task(name="process_postcard_send")
def process_postcard_send_task(postcard_id: str, user_id: str):
    """
    편지 발송을 처리하는 워커 작업
    
    이미지 생성, 번역, 이메일 발송 등 시간이 오래 걸리는 작업을 수행합니다.
    """
    logger.info(f"Task started: process_postcard_send for postcard_id={postcard_id}")
    
    async def _run():
        async with get_db_session() as db:
            service = PostcardService(db)
            # 기존에 정의된 비동기 비즈니스 로직 호출
            await service._send_postcard_background(postcard_id, user_id)
            
    try:
        # 비동기 루프 실행
        asyncio.run(_run())
        logger.info(f"Task completed: process_postcard_send for postcard_id={postcard_id}")
    except Exception as e:
        logger.error(f"Task failed: process_postcard_send for postcard_id={postcard_id}, error={str(e)}")
        raise e
