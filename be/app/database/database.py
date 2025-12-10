"""
데이터베이스 연결 및 세션 관리

SQLAlchemy 엔진과 세션을 설정하고 의존성 주입을 제공합니다.
"""

from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.database.models import Base
from app.config import settings

engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """데이터베이스 테이블 생성"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """
    DB 세션 의존성

    FastAPI 의존성 주입으로 사용됩니다.

    Example:
        @app.get("/example")
        async def example(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Template))
            return result.scalars().all()
    """
    async with async_session_maker() as session:
        yield session


@asynccontextmanager
async def get_db_session():
    """
    독립 실행용 DB 세션 컨텍스트 매니저

    스케줄러 등 FastAPI 요청 외부에서 DB 접근 시 사용합니다.

    Example:
        async with get_db_session() as db:
            result = await db.execute(select(Postcard))
    """
    async with async_session_maker() as session:
        yield session
