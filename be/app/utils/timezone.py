"""
타임존 처리 유틸리티

모든 시간 처리를 UTC 기준으로 통일하고, timezone-aware datetime을 사용합니다.
"""

from datetime import datetime, timedelta
from typing import Optional
import pytz


def now_utc() -> datetime:
    """
    현재 시각을 UTC timezone-aware datetime으로 반환
    
    Returns:
        datetime: 현재 UTC 시각 (timezone-aware)
    """
    return datetime.now(pytz.UTC)


def to_utc(dt: datetime) -> datetime:
    """
    datetime을 UTC timezone-aware datetime으로 변환
    
    Args:
        dt: 변환할 datetime (timezone-aware 또는 naive)
    
    Returns:
        datetime: UTC timezone-aware datetime
    
    Example:
        # timezone-naive를 UTC로
        dt = datetime(2025, 12, 11, 15, 30)
        utc_dt = to_utc(dt)  # 2025-12-11 15:30:00+00:00
        
        # KST를 UTC로
        kst = pytz.timezone('Asia/Seoul')
        dt_kst = kst.localize(datetime(2025, 12, 11, 15, 30))
        utc_dt = to_utc(dt_kst)  # 2025-12-11 06:30:00+00:00
    """
    if dt.tzinfo is None:
        # timezone-naive면 UTC로 간주하여 localize
        return pytz.UTC.localize(dt)
    else:
        # 다른 timezone이면 UTC로 변환
        return dt.astimezone(pytz.UTC)


def from_isoformat(iso_string: str) -> datetime:
    """
    ISO 8601 형식 문자열을 UTC timezone-aware datetime으로 변환
    
    Args:
        iso_string: ISO 8601 형식 문자열
                   예: "2025-12-11T15:30:00+09:00", "2025-12-11T06:30:00Z"
    
    Returns:
        datetime: UTC timezone-aware datetime
    
    Raises:
        ValueError: 잘못된 ISO 8601 형식
    
    Example:
        dt = from_isoformat("2025-12-11T15:30:00+09:00")
        # 2025-12-11 06:30:00+00:00 (UTC)
    """
    try:
        # 'Z'를 '+00:00'으로 변환
        iso_string = iso_string.replace('Z', '+00:00')
        dt = datetime.fromisoformat(iso_string)
        return to_utc(dt)
    except Exception as e:
        raise ValueError(f"잘못된 ISO 8601 형식: {iso_string}") from e


def validate_schedule_time(
    scheduled_at: datetime,
    min_minutes: int = 5,
    max_days: int = 730
) -> tuple[bool, Optional[str]]:
    """
    예약 시간이 유효한지 검증
    
    Args:
        scheduled_at: 검증할 시간 (UTC timezone-aware)
        min_minutes: 최소 몇 분 후 (기본: 5분)
        max_days: 최대 몇 일 이내 (기본: 730일 = 2년)
    
    Returns:
        tuple[bool, Optional[str]]: (유효 여부, 에러 메시지)
    
    Example:
        is_valid, error = validate_schedule_time(scheduled_at)
        if not is_valid:
            raise ValueError(error)
    """
    now = now_utc()
    min_time = now + timedelta(minutes=min_minutes)
    max_time = now + timedelta(days=max_days)
    
    # UTC로 변환
    scheduled_utc = to_utc(scheduled_at)
    
    if scheduled_utc < min_time:
        return False, f"예약 시간은 최소 {min_minutes}분 후여야 합니다."
    
    if scheduled_utc > max_time:
        return False, f"예약 시간은 최대 {max_days}일 이내여야 합니다."
    
    return True, None


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """
    datetime이 None이 아니면 UTC timezone-aware로 변환
    
    Args:
        dt: 변환할 datetime 또는 None
    
    Returns:
        datetime or None: UTC timezone-aware datetime 또는 None
    
    Example:
        # DB에서 읽은 naive datetime 처리
        dt = ensure_utc(postcard.scheduled_at)
    """
    if dt is None:
        return None
    return to_utc(dt)


def to_naive_utc(dt: datetime) -> datetime:
    """
    timezone-aware datetime을 naive UTC datetime으로 변환
    (SQLite 저장용 - SQLite는 timezone 정보를 저장하지 않음)
    
    Args:
        dt: timezone-aware datetime
    
    Returns:
        datetime: timezone-naive UTC datetime
    
    Example:
        # DB 저장 전
        naive_dt = to_naive_utc(scheduled_at)
    """
    utc_dt = to_utc(dt)
    return utc_dt.replace(tzinfo=None)
