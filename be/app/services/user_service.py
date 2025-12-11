"""
User Service

사용자 관련 비즈니스 로직을 처리하는 서비스
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.models import User
from app.utils.password import hash_password, verify_password


class UserService:
    """사용자 관련 비즈니스 로직"""

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """
        이메일로 사용자 조회
        
        Args:
            db: 데이터베이스 세션
            email: 사용자 이메일
            
        Returns:
            사용자 객체 또는 None
        """
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
        """
        ID로 사용자 조회
        
        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            
        Returns:
            사용자 객체 또는 None
        """
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create_user(
        db: AsyncSession,
        email: str,
        name: str,
        password: str
    ) -> User:
        """
        새 사용자 생성
        
        Args:
            db: 데이터베이스 세션
            email: 사용자 이메일
            name: 사용자 이름
            password: 평문 비밀번호
            
        Returns:
            생성된 사용자 객체
            
        Raises:
            ValueError: 이메일이 이미 존재하는 경우
        """
        # 이메일 중복 확인
        existing_user = await UserService.get_user_by_email(db, email)
        if existing_user:
            raise ValueError("이미 가입된 이메일입니다.")

        # 사용자 생성
        user = User(
            email=email,
            name=name,
            hashed_password=hash_password(password)
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        return user

    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        email: str,
        password: str
    ) -> Optional[User]:
        """
        사용자 인증
        
        Args:
            db: 데이터베이스 세션
            email: 사용자 이메일
            password: 평문 비밀번호
            
        Returns:
            인증 성공 시 사용자 객체, 실패 시 None
        """
        user = await UserService.get_user_by_email(db, email)
        
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        return user
