"""
JWT 토큰 생성 및 검증 유틸리티

python-jose를 사용하여 JWT 액세스 토큰을 생성하고 검증합니다.
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from app.config import settings


def create_access_token(user_id: str, email: str) -> str:
    """
    JWT 액세스 토큰 생성

    Args:
        user_id: 사용자 ID
        email: 사용자 이메일

    Returns:
        JWT 액세스 토큰
    """
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    to_encode = {
        "sub": user_id,  # subject (사용자 ID)
        "email": email,
        "exp": expire
    }
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    JWT 토큰 검증 및 페이로드 반환

    Args:
        token: JWT 토큰

    Returns:
        토큰 페이로드 (검증 실패 시 None)
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None
