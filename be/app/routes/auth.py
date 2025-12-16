"""
인증 API 라우터

회원가입 및 로그인 엔드포인트를 제공합니다.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.models.user import SignupRequest, LoginRequest, TokenResponse, UserResponse, UpdateUserRequest
from app.utils.jwt import create_access_token
from app.services.user_service import UserService
from app.services.email_service import EmailService
from app.dependencies.auth import get_current_user
from app.database.models import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/auth", tags=["Authentication"])


@router.post("/signup", response_model=UserResponse, status_code=201)
async def signup(request: SignupRequest, db: AsyncSession = Depends(get_db)):
    """
    회원가입

    - 이메일 중복 검사
    - 비밀번호 bcrypt 해싱
    - User 테이블에 저장
    - 이메일 인증 메일 발송

    Args:
        request: 회원가입 요청 (이메일, 이름, 비밀번호)
        db: 데이터베이스 세션

    Returns:
        생성된 사용자 정보

    Raises:
        HTTPException: 이메일이 이미 가입되어 있는 경우
    """
    try:
        # 사용자 생성
        user = await UserService.create_user(
            db=db,
            email=request.email,
            name=request.name,
            password=request.password
        )

        # 이메일 인증 토큰 생성
        verification_token = await UserService.create_verification_token(
            db=db,
            user_id=user.id
        )

        # 이메일 인증 메일 발송 (백그라운드에서 실행)
        try:
            email_service = EmailService()
            await email_service.send_verification_email(
                to_email=user.email,
                name=user.name,
                verification_token=verification_token
            )
            logger.info(f"Verification email sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send verification email: {str(e)}")
            # 이메일 발송 실패해도 회원가입은 성공으로 처리

        return UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            is_email_verified=user.is_email_verified,
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
            is_email_verified=user.is_email_verified,
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
        is_email_verified=current_user.is_email_verified,
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
        is_email_verified=updated_user.is_email_verified,
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


@router.get("/verify-email", response_class=HTMLResponse)
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    """
    이메일 인증 확인

    - 이메일 인증 토큰을 검증하고 사용자의 이메일을 인증 완료 상태로 변경합니다.

    Args:
        token: 이메일 인증 토큰
        db: 데이터베이스 세션

    Returns:
        인증 성공/실패 HTML 페이지

    Raises:
        HTTPException: 토큰이 유효하지 않거나 만료된 경우
    """
    user = await UserService.verify_email_token(db=db, token=token)

    if not user:
        # 실패 페이지
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>이메일 인증 실패 - 바당우체국</title>
            <style>
                body {
                    font-family: 'Malgun Gothic', '맑은 고딕', Arial, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    margin: 0;
                    padding: 20px;
                }
                .container {
                    background: white;
                    border-radius: 16px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    padding: 50px 40px;
                    max-width: 500px;
                    text-align: center;
                }
                .icon {
                    font-size: 64px;
                    margin-bottom: 20px;
                }
                h1 {
                    color: #e53e3e;
                    margin: 0 0 20px;
                    font-size: 28px;
                }
                p {
                    color: #666;
                    line-height: 1.6;
                    margin-bottom: 30px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="icon">❌</div>
                <h1>이메일 인증 실패</h1>
                <p>유효하지 않거나 만료된 인증 토큰입니다.</p>
                <p>인증 메일을 다시 요청해주세요.</p>
            </div>
        </body>
        </html>
        """

    # 성공 페이지
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>이메일 인증 완료 - 바당우체국</title>
        <style>
            body {{
                font-family: 'Malgun Gothic', '맑은 고딕', Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
                padding: 20px;
            }}
            .container {{
                background: white;
                border-radius: 16px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                padding: 50px 40px;
                max-width: 500px;
                text-align: center;
            }}
            .icon {{
                font-size: 64px;
                margin-bottom: 20px;
                animation: bounce 1s ease;
            }}
            @keyframes bounce {{
                0%, 100% {{ transform: translateY(0); }}
                50% {{ transform: translateY(-20px); }}
            }}
            h1 {{
                color: #4CAF50;
                margin: 0 0 20px;
                font-size: 28px;
            }}
            p {{
                color: #666;
                line-height: 1.6;
                margin-bottom: 10px;
            }}
            .user-info {{
                background: #f9f9f9;
                padding: 20px;
                border-radius: 8px;
                margin-top: 20px;
            }}
            .user-info p {{
                margin: 5px 0;
                color: #333;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="icon">✅</div>
            <h1>이메일 인증 완료!</h1>
            <p>{user.name}님, 환영합니다!</p>
            <p>이메일 인증이 성공적으로 완료되었습니다.</p>
            <div class="user-info">
                <p><strong>이메일:</strong> {user.email}</p>
                <p><strong>이름:</strong> {user.name}</p>
            </div>
        </div>
    </body>
    </html>
    """


@router.post("/resend-verification")
async def resend_verification_email(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    이메일 인증 메일 재발송

    - 이미 인증된 사용자는 재발송할 수 없습니다.

    Args:
        current_user: 인증된 사용자 (JWT 토큰에서 추출)
        db: 데이터베이스 세션

    Returns:
        발송 성공 메시지

    Raises:
        HTTPException: 이미 인증된 사용자이거나 이메일 발송 실패 시
    """
    # 이미 인증된 사용자인지 확인
    if current_user.is_email_verified:
        raise HTTPException(
            status_code=400,
            detail="이미 이메일 인증이 완료된 사용자입니다."
        )

    try:
        # 새 인증 토큰 생성
        verification_token = await UserService.create_verification_token(
            db=db,
            user_id=current_user.id
        )

        # 이메일 발송
        email_service = EmailService()
        await email_service.send_verification_email(
            to_email=current_user.email,
            name=current_user.name,
            verification_token=verification_token
        )

        logger.info(f"Verification email resent to {current_user.email}")

        return {"message": "인증 메일이 재발송되었습니다."}

    except Exception as e:
        logger.error(f"Failed to resend verification email: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="이메일 발송에 실패했습니다. 잠시 후 다시 시도해주세요."
        )
