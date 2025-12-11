"""
스케줄러 싱글톤 인스턴스

순환 참조를 방지하기 위해 스케줄러 인스턴스를 별도 모듈로 분리
"""

from typing import Optional
from app.services.scheduler_service import SchedulerService

# 전역 스케줄러 인스턴스
_scheduler: Optional[SchedulerService] = None


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
    스케줄러 초기화 및 반환
    
    Returns:
        초기화된 SchedulerService 인스턴스
    """
    global _scheduler
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
