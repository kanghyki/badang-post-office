"""
예약 발송 스케줄러 서비스

APScheduler를 사용하여 예약된 엽서 발송을 관리합니다.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.jobstores.base import JobLookupError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
import pytz

from app.database.database import get_db_session
from app.database.models import Postcard
from app.services.postcard_service import PostcardService
from app.services.email_service import EmailService
from app.services.storage_service import LocalStorageService

logger = logging.getLogger(__name__)


class SchedulerService:
    """예약 발송 스케줄러 서비스"""

    def __init__(self):
        """스케줄러 초기화"""
        self.scheduler = AsyncIOScheduler(timezone=pytz.UTC)
        self.storage = LocalStorageService()

    async def start(self):
        """
        스케줄러 시작 및 기존 예약 복구
        """
        self.scheduler.start()
        logger.info("Scheduler started")

        # DB에서 pending 상태의 예약 복구
        await self._restore_scheduled_postcards()

    async def shutdown(self):
        """스케줄러 종료"""
        self.scheduler.shutdown(wait=False)
        logger.info("Scheduler shutdown")

    async def _restore_scheduled_postcards(self):
        """
        서버 재시작 시 DB에서 pending 상태의 예약을 복구
        
        - 예정 시각이 미래인 경우: 스케줄러에 등록
        - 예정 시각이 지난 경우: 즉시 발송
        """
        logger.info("-" * 60)
        logger.info("Restoring scheduled postcards from database...")
        
        async with get_db_session() as db:
            now_utc = datetime.now(pytz.UTC)
            
            # pending 상태이고 scheduled_at이 있는 모든 엽서 조회
            stmt = select(Postcard).where(
                Postcard.status == "pending",
                Postcard.scheduled_at != None
            )
            result = await db.execute(stmt)
            scheduled_postcards = result.scalars().all()
            
            total_count = len(scheduled_postcards)
            logger.info(f"Found {total_count} pending scheduled postcards in database")

            future_count = 0
            overdue_count = 0

            for scheduled in scheduled_postcards:
                try:
                    # timezone-aware 비교를 위해 변환
                    scheduled_time = scheduled.scheduled_at
                    if scheduled_time.tzinfo is None:
                        scheduled_time = pytz.UTC.localize(scheduled_time)
                    
                    if scheduled_time > now_utc:
                        # 미래: 스케줄러에 등록
                        self.scheduler.add_job(
                            self._send_scheduled_postcard,
                            trigger=DateTrigger(run_date=scheduled_time),
                            args=[scheduled.id],
                            id=scheduled.id,
                            replace_existing=True
                        )
                        logger.info(f"  Scheduled: {scheduled.id[:8]}... at {scheduled_time}")
                        future_count += 1
                    else:
                        # 과거: 즉시 발송 (지연 발송)
                        delay = now_utc - scheduled_time
                        logger.warning(f"  Overdue: {scheduled.id[:8]}... (delayed by {delay.total_seconds():.0f}s), sending immediately")
                        self.scheduler.add_job(
                            self._send_scheduled_postcard,
                            trigger=DateTrigger(run_date=now_utc),  # 즉시 실행
                            args=[scheduled.id],
                            id=scheduled.id,
                            replace_existing=True
                        )
                        overdue_count += 1
                        
                except Exception as e:
                    logger.error(f"  Failed to restore postcard {scheduled.id}: {str(e)}")

            logger.info(f"Restoration complete: {future_count} future, {overdue_count} overdue (total: {total_count})")
            logger.info("-" * 60)

    async def schedule_postcard(
        self,
        scheduled_id: str,
        scheduled_at: datetime
    ) -> bool:
        """
        예약 발송 스케줄 등록

        Args:
            scheduled_id: ScheduledPostcard ID
            scheduled_at: 발송 예정 시간 (UTC)

        Returns:
            성공 여부
        """
        try:
            # 최소 5분 이후, 최대 2년 이내 검증은 API 레이어에서 수행
            self.scheduler.add_job(
                self._send_scheduled_postcard,
                trigger=DateTrigger(run_date=scheduled_at),
                args=[scheduled_id],
                id=scheduled_id,
                replace_existing=True
            )
            logger.info(f"Scheduled postcard {scheduled_id} at {scheduled_at}")
            return True
        except Exception as e:
            logger.error(f"Failed to schedule postcard {scheduled_id}: {str(e)}")
            return False

    async def cancel_schedule(self, scheduled_id: str) -> bool:
        """
        예약 취소

        Args:
            scheduled_id: ScheduledPostcard ID

        Returns:
            성공 여부
        """
        try:
            self.scheduler.remove_job(scheduled_id)
            logger.info(f"Cancelled schedule {scheduled_id}")
            return True
        except JobLookupError:
            logger.warning(f"Schedule {scheduled_id} not found in scheduler")
            return False
        except Exception as e:
            logger.error(f"Failed to cancel schedule {scheduled_id}: {str(e)}")
            return False

    async def reschedule_postcard(
        self,
        scheduled_id: str,
        new_scheduled_at: datetime
    ) -> bool:
        """
        예약 시간 변경

        Args:
            scheduled_id: ScheduledPostcard ID
            new_scheduled_at: 새로운 발송 예정 시간 (UTC)

        Returns:
            성공 여부
        """
        try:
            self.scheduler.reschedule_job(
                scheduled_id,
                trigger=DateTrigger(run_date=new_scheduled_at)
            )
            logger.info(f"Rescheduled postcard {scheduled_id} to {new_scheduled_at}")
            return True
        except JobLookupError:
            logger.warning(f"Schedule {scheduled_id} not found, creating new schedule")
            return await self.schedule_postcard(scheduled_id, new_scheduled_at)
        except Exception as e:
            logger.error(f"Failed to reschedule postcard {scheduled_id}: {str(e)}")
            return False

    async def _send_scheduled_postcard(self, scheduled_id: str):
        """
        예약된 엽서 발송 (스케줄러에서 호출)

        Args:
            scheduled_id: Postcard ID
        """
        async with get_db_session() as db:
            try:
                # 예약 정보 조회
                stmt = select(Postcard).where(Postcard.id == scheduled_id)
                result = await db.execute(stmt)
                scheduled = result.scalar_one_or_none()

                if not scheduled:
                    logger.error(f"Scheduled postcard {scheduled_id} not found")
                    return

                if scheduled.status != "pending":
                    logger.warning(f"Scheduled postcard {scheduled_id} is not pending (status: {scheduled.status})")
                    return

                # 사진 데이터 복원 (저장된 경로에서 읽기)
                photos = None
                if scheduled.user_photo_paths:
                    photos = {}
                    for photo_id, photo_path in scheduled.user_photo_paths.items():
                        try:
                            photo_bytes = self.storage.read_file(photo_path)
                            photos[photo_id] = photo_bytes
                        except Exception as e:
                            logger.error(f"Failed to read photo {photo_path}: {str(e)}")

                # 엽서 생성
                postcard_service = PostcardService(db)
                postcard = await postcard_service.create_postcard(
                    template_id=scheduled.template_id,
                    texts=scheduled.text_contents,
                    photos=photos,
                    sender_name=scheduled.sender_name,
                    user_id=scheduled.user_id,
                    recipient_email=scheduled.recipient_email,
                )

                # 이메일 발송
                email_service = EmailService()
                await email_service.send_postcard_email(
                    to_email=scheduled.recipient_email,
                    to_name=scheduled.recipient_name,
                    postcard_image_path=postcard.postcard_path,
                    sender_name=scheduled.sender_name
                )

                # 상태 업데이트: sent
                stmt = (
                    update(Postcard)
                    .where(Postcard.id == scheduled_id)
                    .values(
                        status="sent",
                        postcard_image_path=postcard.postcard_path,
                        sent_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                )
                await db.execute(stmt)
                await db.commit()

                logger.info(f"Successfully sent scheduled postcard {scheduled_id}")

            except Exception as e:
                logger.error(f"Failed to send scheduled postcard {scheduled_id}: {str(e)}")

                # 상태 업데이트: failed
                try:
                    stmt = (
                        update(Postcard)
                        .where(Postcard.id == scheduled_id)
                        .values(
                            status="failed",
                            error_message=str(e),
                            updated_at=datetime.utcnow()
                        )
                    )
                    await db.execute(stmt)
                    await db.commit()
                except Exception as update_error:
                    logger.error(f"Failed to update status for {scheduled_id}: {str(update_error)}")
