import os
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.routes import postcards, templates_dev, templates_public, fonts, translation, auth, files, postcards_dev
from app.database.database import init_db, get_db
from app.scheduler_instance import init_scheduler, shutdown_scheduler

# 로그 디렉토리 생성
os.makedirs("logs", exist_ok=True)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
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

# SQLAlchemy 로그 레벨을 WARNING으로 설정 (INFO 로그 숨김)
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)

# APScheduler 로그 레벨을 WARNING으로 설정
logging.getLogger('apscheduler').setLevel(logging.WARNING)

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
    # Initialize database (Postcard table)
    await init_db()
    logger.info("✓ Database initialized")

    # Initialize scheduler
    scheduler = init_scheduler()
    await scheduler.start()

    logger.info("✓ Application ready")

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

# 개발/운영용 관리 API (env=dev일 때만 활성화)
if settings.env == "dev":
    # Static 파일 마운트 (개발 모드에서만)
    app.mount("/admin", StaticFiles(directory="static/admin"), name="admin")
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # templates_dev를 templates_public보다 먼저 등록 (개발 환경에서 우선)
    app.include_router(templates_dev.router)  # 개발: 템플릿 생성/수정/삭제
    app.include_router(fonts.router)
    app.include_router(postcards_dev.router)  # 개발: 엽서 스케줄러 모니터링
    logger.info("Development/Admin APIs, Static Files enabled")

# 프로덕션 템플릿 API (인증 필요)
app.include_router(templates_public.router)  # 프로덕션: 템플릿 조회
app.include_router(translation.router)  # 제주 방언 번역 테스트


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
