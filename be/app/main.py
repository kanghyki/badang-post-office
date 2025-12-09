import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.routes import postcards, templates, templates_public, fonts
from app.database.database import init_db, get_db
from app.template_store import load_templates
from app.font_store import load_fonts

# 로거 설정
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
    앱 시작/종료 시 실행되는 lifespan 이벤트

    시작 시:
    - 필요한 디렉토리 생성
    - JSON 템플릿/폰트 파일 메모리 로드
    - 데이터베이스 테이블 생성
    """
    logger.info("Starting application initialization...")

    # JSON 템플릿 및 폰트 로드
    load_templates()
    load_fonts()

    # 데이터베이스 초기화 (Postcard 테이블)
    await init_db()
    logger.info("Database tables created successfully")

    logger.info("Application initialization completed")

    yield

    # 종료 시
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

# 정적 파일 서빙
app.mount("/static", StaticFiles(directory="static"), name="static")

# 라우터 등록
app.include_router(postcards.router)
app.include_router(templates_public.router)  # 프로덕션: 템플릿 조회

# 개발/운영용 관리 API (env=dev일 때만 활성화)
if settings.env == "dev":
    app.include_router(templates.router)  # 개발: 템플릿 생성/수정/삭제
    app.include_router(fonts.router)
    logger.info("✅ Development/Admin APIs (Template Management, Fonts) enabled")


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
