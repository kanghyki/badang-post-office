"""
편지 이벤트 관리 서비스

SSE 이벤트를 DB에 저장하고 재생하는 기능을 제공합니다.
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.models import PostcardEvent
from app.services.redis_service import redis_service
import json

logger = logging.getLogger(__name__)


class PostcardEventService:
    """편지 이벤트 서비스"""

    @staticmethod
    async def publish_and_save(
        db: AsyncSession,
        postcard_id: str,
        event_type: str,
        event_data: Optional[Dict[str, Any]] = None
    ):
        """
        이벤트를 Redis로 발행하고 DB에 저장

        Args:
            db: AsyncSession
            postcard_id: 편지 ID
            event_type: 이벤트 타입 (translating, converting, etc.)
            event_data: 이벤트 메타데이터 (에러 메시지 등)
        """
        # Redis Pub/Sub 발행
        message = {"status": event_type}
        if event_data:
            message.update(event_data)

        await redis_service.publish(
            f"postcard:{postcard_id}",
            json.dumps(message)
        )

        # DB에 저장
        event = PostcardEvent(
            postcard_id=postcard_id,
            event_type=event_type,
            event_data=event_data
        )
        db.add(event)
        await db.commit()

        logger.info(f"📤 이벤트 발행 및 저장: {postcard_id} - {event_type}")

    @staticmethod
    async def get_events(
        db: AsyncSession,
        postcard_id: str
    ) -> List[Dict[str, Any]]:
        """
        편지의 모든 이벤트 조회 (시간순)

        Args:
            db: AsyncSession
            postcard_id: 편지 ID

        Returns:
            이벤트 목록 [{'status': 'translating', ...}, ...]
        """
        stmt = (
            select(PostcardEvent)
            .where(PostcardEvent.postcard_id == postcard_id)
            .order_by(PostcardEvent.created_at.asc())
        )
        result = await db.execute(stmt)
        events = result.scalars().all()

        return [
            {
                "status": event.event_type,
                **(event.event_data or {})
            }
            for event in events
        ]
