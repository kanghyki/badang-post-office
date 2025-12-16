"""
Redis Pub/Sub 서비스

SSE를 위한 실시간 메시지 전달 서비스
"""

import redis.asyncio as redis
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class RedisService:
    """Redis Pub/Sub 서비스"""

    def __init__(self):
        self.redis = None

    async def connect(self):
        """Redis 연결"""
        try:
            self.redis = await redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                password=settings.redis_password if settings.redis_password else None,
                decode_responses=True
            )
            # 연결 테스트
            await self.redis.ping()
            logger.info(f"✅ Redis connected: {settings.redis_host}:{settings.redis_port}")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {str(e)}")
            raise

    async def publish(self, channel: str, message: str):
        """메시지 발행"""
        if self.redis:
            try:
                await self.redis.publish(channel, message)
            except Exception as e:
                logger.error(f"❌ Redis publish failed: {str(e)}")

    async def subscribe(self, channel: str):
        """채널 구독 (제너레이터)"""
        if self.redis:
            pubsub = self.redis.pubsub()
            await pubsub.subscribe(channel)
            try:
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        yield message["data"]
            finally:
                await pubsub.unsubscribe(channel)
                await pubsub.close()

    async def close(self):
        """Redis 연결 종료"""
        if self.redis:
            await self.redis.close()
            logger.info("✅ Redis disconnected")


# 전역 인스턴스
redis_service = RedisService()
