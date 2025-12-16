"""
User Pydantic 스키마

회원가입, 로그인, 사용자 응답 등을 위한 데이터 검증 스키마
"""

from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from datetime import datetime
from typing import Optional


class SignupRequest(BaseModel):
    """회원가입 요청"""
    email: EmailStr
    name: str
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("비밀번호는 최소 6자 이상이어야 합니다.")
        return v


class LoginRequest(BaseModel):
    """로그인 요청"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """사용자 응답"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    name: str
    is_email_verified: bool
    created_at: datetime


class TokenResponse(BaseModel):
    """로그인 응답 (토큰 포함)"""
    access_token: str
    token_type: str
    user: UserResponse


class UpdateUserRequest(BaseModel):
    """사용자 정보 수정 요청"""
    name: Optional[str] = None
    password: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) < 6:
            raise ValueError("비밀번호는 최소 6자 이상이어야 합니다.")
        return v
