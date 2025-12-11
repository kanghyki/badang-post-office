"""
인증 API 라우터

회원가입 및 로그인 엔드포인트를 제공합니다.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.models.user import SignupRequest, LoginRequest, TokenResponse, UserResponse, UpdateUserRequest
from app.utils.jwt import create_access_token
from app.services.user_service import UserService
from app.dependencies.auth import get_current_user
from app.database.models import User

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
    try:
        user = await UserService.create_user(
            db=db,
            email=request.email,
            name=request.name,
            password=request.password
        )
        
        return UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            created_at=user.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


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
    user = await UserService.authenticate_user(
        db=db,
        email=request.email,
        password=request.password
    )

    if not user:
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


@router.get("/me", response_model=UserResponse)
async def get_my_info(current_user: User = Depends(get_current_user)):
    """
    내 정보 조회

    - 현재 로그인한 사용자의 정보를 반환합니다.

    Args:
        current_user: 인증된 사용자 (JWT 토큰에서 추출)

    Returns:
        사용자 정보
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        created_at=current_user.created_at
    )


@router.patch("/me", response_model=UserResponse)
async def update_my_info(
    request: UpdateUserRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    내 정보 수정

    - 현재 로그인한 사용자의 이름 또는 비밀번호를 수정합니다.
    - 수정하려는 필드만 요청에 포함하면 됩니다.

    Args:
        request: 수정할 사용자 정보 (이름, 비밀번호 선택적)
        current_user: 인증된 사용자 (JWT 토큰에서 추출)
        db: 데이터베이스 세션

    Returns:
        수정된 사용자 정보

    Raises:
        HTTPException: 사용자 수정 실패 시
    """
    updated_user = await UserService.update_user(
        db=db,
        user_id=current_user.id,
        name=request.name,
        password=request.password
    )

    if not updated_user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    return UserResponse(
        id=updated_user.id,
        email=updated_user.email,
        name=updated_user.name,
        created_at=updated_user.created_at
    )


@router.delete("/withdrawal", status_code=204)
async def withdraw(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    회원 탈퇴

    - 인증된 사용자의 계정을 삭제합니다.
    - 삭제 시 관련된 모든 데이터가 함께 삭제됩니다.

    Args:
        current_user: 인증된 사용자 (JWT 토큰에서 추출)
        db: 데이터베이스 세션

    Returns:
        204 No Content

    Raises:
        HTTPException: 사용자 삭제 실패 시
    """
    success = await UserService.delete_user(db=db, user_id=current_user.id)

    if not success:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    return None
