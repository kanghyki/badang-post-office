"""
비밀번호 해싱 및 검증 유틸리티

bcrypt를 사용하여 비밀번호를 안전하게 해싱하고 검증합니다.
"""

import bcrypt


def hash_password(password: str) -> str:
    """
    비밀번호를 bcrypt로 해싱

    Args:
        password: 평문 비밀번호

    Returns:
        해싱된 비밀번호 (문자열)
    """
    # 비밀번호를 바이트로 인코딩
    password_bytes = password.encode('utf-8')

    # bcrypt로 해싱 (자동으로 salt 생성)
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())

    # 바이트를 문자열로 디코딩하여 반환
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    비밀번호 검증

    Args:
        plain_password: 평문 비밀번호
        hashed_password: 해싱된 비밀번호

    Returns:
        비밀번호 일치 여부
    """
    # 평문 비밀번호와 해시를 바이트로 인코딩
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')

    # bcrypt로 검증
    return bcrypt.checkpw(password_bytes, hashed_bytes)
