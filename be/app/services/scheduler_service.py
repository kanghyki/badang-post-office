"""
예약 발송 스케줄러 서비스

APScheduler를 사용하여 예약된 편지 발송을 관리합니다.
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

from app.utils.timezone import now_utc, ensure_utc

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
        self.scheduler = AsyncIOScheduler(
            timezone=pytz.UTC,
            job_defaults={
                'misfire_grace_time': None  # 시간 제한 없이 모든 놓친 작업 즉시 실행
            }
        )
        self.storage = LocalStorageService()

    async def start(self):
        """
        스케줄러 시작 및 기존 예약 복구
        """
        self.scheduler.start()
        logger.info("✓ Scheduler started")

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
        async with get_db_session() as db:
            now = now_utc()
            
            # pending 상태이고 scheduled_at이 있는 모든 편지 조회
            stmt = select(Postcard).where(
                Postcard.status == "pending",
                Postcard.scheduled_at != None
            )
            result = await db.execute(stmt)
            scheduled_postcards = result.scalars().all()
            
            total_count = len(scheduled_postcards)
            if total_count == 0:
                return

            future_count = 0
            overdue_count = 0

            for scheduled in scheduled_postcards:
                try:
                    # timezone-aware UTC로 변환
                    scheduled_time = ensure_utc(scheduled.scheduled_at)
                    
                    if scheduled_time > now:
                        # 미래: 스케줄러에 등록
                        self.scheduler.add_job(
                            self._send_scheduled_postcard,
                            trigger=DateTrigger(run_date=scheduled_time),
                            args=[scheduled.id],
                            id=scheduled.id,
                            replace_existing=True
                        )
                        future_count += 1
                    else:
                        # 과거: 즉시 발송 (지연 발송)
                        delay = now - scheduled_time
                        logger.warning(f"Overdue postcard {scheduled.id[:8]}... delayed by {delay.total_seconds():.0f}s, sending now")
                        self.scheduler.add_job(
                            self._send_scheduled_postcard,
                            trigger=DateTrigger(run_date=now),  # 즉시 실행
                            args=[scheduled.id],
                            id=scheduled.id,
                            replace_existing=True
                        )
                        overdue_count += 1
                        
                except Exception as e:
                    logger.error(f"Failed to restore postcard {scheduled.id}: {str(e)}")

            logger.info(f"✓ Restored {total_count} scheduled postcards ({future_count} future, {overdue_count} overdue)")

    def schedule_postcard(
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

    def cancel_schedule(self, scheduled_id: str) -> bool:
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

    def cancel_user_schedules(self, postcard_ids: list[str]) -> int:
        """
        특정 사용자의 모든 예약 취소

        Args:
            postcard_ids: 취소할 편지 ID 목록

        Returns:
            취소된 스케줄 개수
        """
        cancelled_count = 0
        for postcard_id in postcard_ids:
            if self.cancel_schedule(postcard_id):
                cancelled_count += 1
        
        logger.info(f"Cancelled {cancelled_count} schedules out of {len(postcard_ids)} postcards")
        return cancelled_count

    def reschedule_postcard(
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
            return self.schedule_postcard(scheduled_id, new_scheduled_at)
        except Exception as e:
            logger.error(f"Failed to reschedule postcard {scheduled_id}: {str(e)}")
            return False

    async def _send_scheduled_postcard(self, scheduled_id: str):
        """
        예약된 편지 발송 (스케줄러에서 호출)

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

                logger.info(f"🚀 [예약발송] 발송 시작: {scheduled_id}")

                # 상태를 processing으로 변경 (예약 중 → 발송 중)
                stmt = (
                    update(Postcard)
                    .where(Postcard.id == scheduled_id)
                    .values(status="processing", updated_at=datetime.utcnow())
                )
                await db.execute(stmt)
                await db.commit()

                # PostcardService의 즉시 발송 로직 재사용
                postcard_service = PostcardService(db)
                await postcard_service._send_postcard_background(scheduled_id, scheduled.user_id)

                logger.info(f"✅ [예약발송] 발송 완료: {scheduled_id}")

            except Exception as e:
                logger.error(f"❌ [예약발송] 발송 실패: {scheduled_id}: {str(e)}")
