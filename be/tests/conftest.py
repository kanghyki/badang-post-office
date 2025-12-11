"""
Pytest 공통 fixtures 및 설정
"""
import os
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.database import Base, get_db
from app.database.models import User
from app.utils.jwt import create_access_token
from app.utils.password import hash_password


# 테스트용 인메모리 SQLite 데이터베이스
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """이벤트 루프 생성"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_engine():
    """테스트용 데이터베이스 엔진 생성"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    
    # 테이블 생성
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # 테이블 삭제
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """테스트용 데이터베이스 세션"""
    async_session = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """테스트용 HTTP 클라이언트"""
    
    # 데이터베이스 의존성 오버라이드
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    # AsyncClient 생성
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    # 오버라이드 정리
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """테스트용 사용자 생성"""
    user = User(
        email="test@example.com",
        name="테스트 사용자",
        hashed_password=hash_password("testpassword123")
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_user2(db_session: AsyncSession) -> User:
    """두 번째 테스트용 사용자 생성"""
    user = User(
        email="test2@example.com",
        name="테스트 사용자2",
        hashed_password=hash_password("testpassword456")
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """인증 헤더 생성"""
    token = create_access_token(user_id=test_user.id, email=test_user.email)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_user2(test_user2: User) -> dict:
    """두 번째 사용자의 인증 헤더 생성"""
    token = create_access_token(user_id=test_user2.id, email=test_user2.email)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def setup_test_directories():
    """테스트용 디렉토리 설정"""
    os.makedirs("static/templates", exist_ok=True)
    os.makedirs("static/fonts", exist_ok=True)
    os.makedirs("static/uploads", exist_ok=True)
    os.makedirs("static/generated", exist_ok=True)
    yield
