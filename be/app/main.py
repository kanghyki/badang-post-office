from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from app.config import settings
from app.routes import postcards


# Bearer Token Security Scheme 정의 (Swagger UI용)
security = HTTPBearer()

app = FastAPI(
    title="Jeju API",
    description="제주 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
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
app.include_router(postcards.router)


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
