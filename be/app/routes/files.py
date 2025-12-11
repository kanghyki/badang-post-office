"""
보안 파일 접근 API 라우터

사용자가 본인 소유의 파일만 접근할 수 있도록 제어합니다.
- uploads: 사용자가 업로드한 사진
- generated: 생성된 엽서 이미지  
- templates: 공개 템플릿 (모든 사용자 접근 가능)
"""

import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.database import get_db
from app.database.models import User, Postcard
from app.dependencies.auth import get_current_user, get_optional_user
import logging

router = APIRouter(prefix="/v1/files", tags=["Files"])
logger = logging.getLogger(__name__)


async def verify_file_access(
    file_path: str,
    current_user: User,
    db: AsyncSession
) -> bool:
    """
    사용자가 특정 파일에 접근 권한이 있는지 확인합니다.
    
    Args:
        file_path: 접근하려는 파일 경로 (예: static/uploads/2025/12/08/uuid.jpg)
        current_user: 현재 로그인한 사용자
        db: 데이터베이스 세션
        
    Returns:
        bool: 접근 권한 여부
    """
    # 파일 경로 정규화
    normalized_path = file_path.replace("\\", "/")
    
    # templates는 모든 사용자 접근 가능
    if normalized_path.startswith("static/templates/"):
        return True
    
    # uploads와 generated는 소유자만 접근 가능
    if normalized_path.startswith("static/uploads/") or normalized_path.startswith("static/generated/"):
        # 해당 파일 경로를 포함한 포스트카드 조회
        stmt = select(Postcard).where(
            Postcard.user_id == current_user.id
        )
        result = await db.execute(stmt)
        postcards = result.scalars().all()
        
        # 각 포스트카드를 확인하여 해당 파일이 있는지 검사
        for postcard in postcards:
            # postcard_image_path 확인
            if postcard.postcard_image_path == normalized_path:
                return True
            
            # user_photo_paths (JSON) 확인
            if postcard.user_photo_paths:
                # user_photo_paths는 {"photo_config_id": "path", ...} 형태
                for photo_path in postcard.user_photo_paths.values():
                    if photo_path == normalized_path:
                        return True
        
        return False
    
    # 그 외의 경로는 접근 불가
    return False


@router.get("/static/{file_path:path}")
async def get_file(
    file_path: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    보안이 적용된 파일 접근 엔드포인트
    
    - templates: 모든 인증된 사용자 접근 가능
    - uploads, generated: 파일 소유자만 접근 가능
    
    Args:
        file_path: static/ 이후의 파일 경로
        
    Returns:
        FileResponse: 파일 응답
        
    Raises:
        HTTPException 403: 접근 권한 없음
        HTTPException 404: 파일을 찾을 수 없음
    """
    # 전체 파일 경로 생성
    full_path = f"static/{file_path}"
    
    # 파일 존재 여부 확인
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
    
    # 파일이 디렉토리인 경우 거부
    if os.path.isdir(full_path):
        raise HTTPException(status_code=400, detail="디렉토리 접근은 불가능합니다")
    
    # 접근 권한 확인
    has_access = await verify_file_access(full_path, current_user, db)
    
    if not has_access:
        logger.warning(f"User {current_user.id} attempted unauthorized access to {full_path}")
        raise HTTPException(status_code=403, detail="이 파일에 접근할 권한이 없습니다")
    
    # 파일 응답 반환
    return FileResponse(
        path=full_path,
        media_type="application/octet-stream",
        filename=os.path.basename(full_path)
    )


@router.get("/templates/{file_path:path}")
async def get_template_file_public(
    file_path: str,
    current_user: User = Depends(get_optional_user)
):
    """
    템플릿 파일 접근 (인증 선택)
    
    템플릿은 공개 리소스이므로 인증 없이도 접근 가능합니다.
    
    Args:
        file_path: templates/ 이후의 파일 경로
        
    Returns:
        FileResponse: 파일 응답
        
    Raises:
        HTTPException 404: 파일을 찾을 수 없음
    """
    full_path = f"static/templates/{file_path}"
    
    # 파일 존재 여부 확인
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="템플릿 파일을 찾을 수 없습니다")
    
    # 파일이 디렉토리인 경우 거부
    if os.path.isdir(full_path):
        raise HTTPException(status_code=400, detail="디렉토리 접근은 불가능합니다")
    
    # 파일 응답 반환
    return FileResponse(
        path=full_path,
        media_type="application/octet-stream",
        filename=os.path.basename(full_path)
    )
