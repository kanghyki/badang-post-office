"""
인증 API 라우터

회원가입 및 로그인 엔드포인트를 제공합니다.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.database import get_db
from app.database.models import User
from app.models.user import SignupRequest, LoginRequest, TokenResponse, UserResponse
from app.utils.password import hash_password, verify_password
from app.utils.jwt import create_access_token

router = APIRouter(prefix="/v1/auth", tags=["Authentication"])


@router.post("/signup", response_model=UserResponse, status_code=201)
async def signup(request: SignupRequest, db: AsyncSession = Depends(get_db)):
    """
    회원가입

    - 이메일 중복 검사
    - 비밀번호 bcrypt 해싱
    - User 테이블에 저장

    Args:
        request: 회원가입 요청 (이메일, 이름, 비밀번호)
        db: 데이터베이스 세션

    Returns:
        생성된 사용자 정보

    Raises:
        HTTPException: 이메일이 이미 가입되어 있는 경우
    """
    # 이메일 중복 확인
    result = await db.execute(select(User).where(User.email == request.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=400, detail="이미 가입된 이메일입니다.")

    # 사용자 생성
    user = User(
        email=request.email,
        name=request.name,
        hashed_password=hash_password(request.password)
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        created_at=user.created_at
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    로그인

    - 이메일로 사용자 조회
    - 비밀번호 검증
    - JWT 토큰 발급

    Args:
        request: 로그인 요청 (이메일, 비밀번호)
        db: 데이터베이스 세션

    Returns:
        JWT 액세스 토큰 및 사용자 정보

    Raises:
        HTTPException: 이메일 또는 비밀번호가 올바르지 않은 경우
    """
    # 사용자 조회
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")

    # 비밀번호 검증
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")

    # JWT 토큰 생성
    access_token = create_access_token(user_id=user.id, email=user.email)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            created_at=user.created_at
        )
    )
