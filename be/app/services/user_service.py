"""
User Service

사용자 관련 비즈니스 로직을 처리하는 서비스
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.database.models import User, Postcard
from app.utils.password import hash_password, verify_password
import logging

logger = logging.getLogger(__name__)


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

    @staticmethod
    async def delete_user(
        db: AsyncSession,
        user_id: str
    ) -> bool:
        """
        사용자 계정 삭제
        
        - 스케줄러에서 예약된 엽서 작업 취소
        - 사용자의 모든 엽서 데이터 삭제
        - 사용자 계정 삭제
        
        Args:
            db: 데이터베이스 세션
            user_id: 삭제할 사용자 ID
            
        Returns:
            삭제 성공 시 True, 사용자가 존재하지 않으면 False
        """
        user = await UserService.get_user_by_id(db, user_id)
        
        if not user:
            return False
        
        # 1. 사용자의 예약된 엽서 조회 (pending 상태)
        result = await db.execute(
            select(Postcard.id).where(
                Postcard.user_id == user_id,
                Postcard.status == "pending"
            )
        )
        pending_postcard_ids = [row[0] for row in result.all()]
        
        # 2. 스케줄러에서 예약 작업 취소
        if pending_postcard_ids:
            try:
                from app.scheduler_instance import get_scheduler
                scheduler = get_scheduler()
                cancelled_count = scheduler.cancel_user_schedules(pending_postcard_ids)
                logger.info(f"Cancelled {cancelled_count} scheduled postcards for user {user_id}")
            except Exception as e:
                logger.warning(f"Failed to cancel schedules for user {user_id}: {str(e)}")
        
        # 3. 사용자의 모든 엽서 삭제
        await db.execute(
            delete(Postcard).where(Postcard.user_id == user_id)
        )
        logger.info(f"Deleted all postcards for user {user_id}")
        
        # 4. 사용자 계정 삭제
        await db.delete(user)
        await db.commit()
        
        logger.info(f"Successfully deleted user {user_id} with all associated data")
        return True
