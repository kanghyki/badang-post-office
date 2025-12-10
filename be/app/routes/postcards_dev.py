"""
엽서 개발/운영용 API 라우터

⚠️ 주의: 이 API는 개발 환경에서만 사용됩니다 (env=dev일 때만 활성화).
스케줄러 작업 조회 등 디버깅 및 모니터링 목적으로 사용됩니다.
"""

from fastapi import APIRouter, HTTPException, Depends
from app.database.models import User
from app.dependencies.auth import get_current_user
from app.scheduler_instance import get_scheduler
import logging

router = APIRouter(prefix="/v1/postcards", tags=["Dev"])
logger = logging.getLogger(__name__)


@router.get("/scheduled/jobs")
async def get_scheduled_jobs(
    current_user: User = Depends(get_current_user)
):
    """
    [개발용] 현재 스케줄러에 등록된 작업 목록 조회
    
    Returns:
        - job_count: 등록된 작업 수
        - jobs: 작업 목록 (id, next_run_time, postcard_id)
    """
    try:
        scheduler = get_scheduler()
        jobs = scheduler.scheduler.get_jobs()
        
        job_list = []
        for job in jobs:
            job_list.append({
                "job_id": job.id,
                "postcard_id": job.id,  # job_id = postcard_id
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        
        return {
            "job_count": len(job_list),
            "jobs": job_list,
            "scheduler_running": scheduler.scheduler.running
        }
        
    except Exception as e:
        logger.error(f"Failed to get scheduled jobs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"스케줄러 작업 조회 중 오류가 발생했습니다: {str(e)}"
        )
