"""
Auth 엔드포인트 테스트

POST /v1/auth/signup - 회원가입
POST /v1/auth/login - 로그인
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User


@pytest.mark.asyncio
class TestSignup:
    """회원가입 테스트"""

    async def test_signup_success(self, client: AsyncClient, db_session: AsyncSession):
        """회원가입 성공"""
        response = await client.post(
            "/v1/auth/signup",
            json={
                "email": "newuser@example.com",
                "name": "새로운 사용자",
                "password": "securepassword123"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["name"] == "새로운 사용자"
        assert "id" in data
        assert "created_at" in data
        assert "password" not in data

    async def test_signup_duplicate_email(self, client: AsyncClient, test_user: User):
        """이메일 중복으로 회원가입 실패"""
        response = await client.post(
            "/v1/auth/signup",
            json={
                "email": test_user.email,
                "name": "다른 사용자",
                "password": "password123"
            }
        )
        
        assert response.status_code == 400
        assert "이미 가입" in response.json()["detail"]

    async def test_signup_invalid_email(self, client: AsyncClient):
        """잘못된 이메일 형식으로 회원가입 실패"""
        response = await client.post(
            "/v1/auth/signup",
            json={
                "email": "invalid-email",
                "name": "사용자",
                "password": "password123"
            }
        )
        
        assert response.status_code == 422  # Validation error

    async def test_signup_missing_fields(self, client: AsyncClient):
        """필수 필드 누락으로 회원가입 실패"""
        response = await client.post(
            "/v1/auth/signup",
            json={
                "email": "user@example.com"
                # name과 password 누락
            }
        )
        
        assert response.status_code == 422

    async def test_signup_short_password(self, client: AsyncClient):
        """짧은 비밀번호로 회원가입 실패"""
        response = await client.post(
            "/v1/auth/signup",
            json={
                "email": "user@example.com",
                "name": "사용자",
                "password": "short"
            }
        )
        
        assert response.status_code == 422


@pytest.mark.asyncio
class TestLogin:
    """로그인 테스트"""

    async def test_login_success(self, client: AsyncClient, test_user: User):
        """로그인 성공"""
        response = await client.post(
            "/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "testpassword123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == test_user.email
        assert data["user"]["name"] == test_user.name

    async def test_login_wrong_password(self, client: AsyncClient, test_user: User):
        """잘못된 비밀번호로 로그인 실패"""
        response = await client.post(
            "/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        assert "이메일 또는 비밀번호가 올바르지 않습니다" in response.json()["detail"]

    async def test_login_nonexistent_email(self, client: AsyncClient):
        """존재하지 않는 이메일로 로그인 실패"""
        response = await client.post(
            "/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 401
        assert "이메일 또는 비밀번호가 올바르지 않습니다" in response.json()["detail"]

    async def test_login_missing_fields(self, client: AsyncClient):
        """필수 필드 누락으로 로그인 실패"""
        response = await client.post(
            "/v1/auth/login",
            json={
                "email": "user@example.com"
                # password 누락
            }
        )
        
        assert response.status_code == 422

    async def test_login_invalid_email_format(self, client: AsyncClient):
        """잘못된 이메일 형식으로 로그인 실패"""
        response = await client.post(
            "/v1/auth/login",
            json={
                "email": "invalid-email",
                "password": "password123"
            }
        )
        
        assert response.status_code == 422
