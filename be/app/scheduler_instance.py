"""
스케줄러 싱글톤 인스턴스

순환 참조를 방지하기 위해 스케줄러 인스턴스를 별도 모듈로 분리
"""

import threading
from typing import Optional
from app.services.scheduler_service import SchedulerService

# 전역 스케줄러 인스턴스
_scheduler: Optional[SchedulerService] = None
# 동시성 제어를 위한 락
_scheduler_lock = threading.Lock()


def get_scheduler() -> SchedulerService:
    """
    스케줄러 인스턴스 반환

    Returns:
        SchedulerService 인스턴스

    Raises:
        RuntimeError: 스케줄러가 초기화되지 않은 경우
    """
    if _scheduler is None:
        raise RuntimeError("Scheduler not initialized. Call init_scheduler() first.")
    return _scheduler


def init_scheduler() -> SchedulerService:
    """
    스케줄러 초기화 및 반환 (Thread-Safe 싱글톤 패턴)

    Returns:
        초기화된 SchedulerService 인스턴스
    """
    global _scheduler

    # Double-checked locking 패턴으로 성능 최적화
    if _scheduler is None:
        with _scheduler_lock:
            # 락 획득 후 다시 한 번 확인 (다른 스레드가 이미 생성했을 수 있음)
            if _scheduler is None:
                _scheduler = SchedulerService()

    return _scheduler


async def shutdown_scheduler():
    """
    스케줄러 종료
    """
    global _scheduler
    if _scheduler is not None:
        await _scheduler.shutdown()
        _scheduler = None
