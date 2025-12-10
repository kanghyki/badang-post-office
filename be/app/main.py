import os
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from app.config import settings
from app.routes import postcards, templates, templates_public, fonts, translation, auth, files
from app.database.database import init_db, get_db
from app.scheduler_instance import init_scheduler, shutdown_scheduler

# 로그 디렉토리 생성
os.makedirs("logs", exist_ok=True)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        # 콘솔 출력
        logging.StreamHandler(),
        # 파일 출력 (날짜별)
        logging.FileHandler(
            f"logs/app_{datetime.now().strftime('%Y%m%d')}.log",
            encoding='utf-8'
        )
    ]
)

logger = logging.getLogger(__name__)

# Bearer Token Security Scheme 정의 (Swagger UI용)
security = HTTPBearer()

# 앱 초기화 전에 필요한 디렉토리 생성
os.makedirs("static/templates", exist_ok=True)
os.makedirs("static/fonts", exist_ok=True)
os.makedirs("static/uploads", exist_ok=True)
os.makedirs("static/generated", exist_ok=True)
os.makedirs("data", exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup/shutdown lifespan events

    On startup:
    - Create necessary directories
    - Initialize database tables
    - Initialize scheduler and restore scheduled postcards
    """
    logger.info("Starting application initialization...")

    # Initialize database (Postcard table)
    await init_db()
    logger.info("Database tables created successfully")

    # Initialize scheduler
    scheduler = init_scheduler()
    await scheduler.start()
    logger.info("Scheduler initialized and started")

    logger.info("Application initialization completed")

    yield

    # 종료 시
    await shutdown_scheduler()
    logger.info("Scheduler shutdown completed")
    logger.info("Application shutdown")


app = FastAPI(
    title="Jeju Postcard API",
    description="제주 엽서 생성 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(files.router)  # 보안 파일 접근
app.include_router(auth.router)  # 인증 (회원가입/로그인)
app.include_router(postcards.router)  # 엽서 발송 (즉시/예약 통합)
app.include_router(templates_public.router)  # 프로덕션: 템플릿 조회
app.include_router(translation.router)  # 제주 방언 번역 테스트


# 개발/운영용 관리 API (env=dev일 때만 활성화)
if settings.env == "dev":
    app.include_router(templates.router)  # 개발: 템플릿 생성/수정/삭제
    app.include_router(fonts.router)
    logger.info("Development/Admin APIs (Template Management, Fonts, Translation) enabled")


@app.get("/")
async def root():
    """API 루트"""
    return {
        "message": "Jeju API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy"}
