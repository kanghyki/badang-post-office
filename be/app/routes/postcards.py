"""
엽서 API 라우터

엽서 생성 엔드포인트를 제공합니다.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.database.models import User
from app.services.postcard_service import PostcardService
from app.models.postcard import PostcardResponse
from app.services import template_service
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/v1/postcards", tags=["Postcards"])


@router.post("/create", response_model=PostcardResponse)
async def create_postcard(
    template_id: str = Form(..., description="사용할 템플릿 ID"),
    text: str = Form(..., description="엽서에 들어갈 본문 텍스트"),
    sender_name: Optional[str] = Form(None, description="발신자 이름 (선택)"),
    image: Optional[UploadFile] = File(None, description="사용자 사진 (선택)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    포스트카드 생성 API

    사용자가 텍스트 하나와 이미지 하나만 제공하면,
    자동으로 템플릿의 적절한 영역에 매핑하여 엽서를 생성합니다.

    매핑 규칙:
    - 텍스트: "main_text" ID 또는 첫 번째 일반 영역에 본문 배치
    - 이미지: "user_photo" ID 또는 첫 번째 photo_config에 배치
    - 자동 생성: "date", "datetime", "time" 등 특수 ID는 자동으로 현재 날짜/시간 생성
    - 발신자: sender_name이 제공되면 DB에 저장

    Args:
        template_id: 템플릿 ID (예: "jeju_sea")
        text: 본문 텍스트
        sender_name: 발신자 이름 (선택)
        image: 사용자 사진 파일 (선택)
        db: 데이터베이스 세션

    Returns:
        생성된 엽서 정보 (PostcardResponse)
    """
    try:
        # 1. 템플릿 조회
        template = template_service.get_template_by_id(template_id)
        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"템플릿 '{template_id}'를 찾을 수 없습니다."
            )

        # 2. 텍스트 매핑 (자동 생성 + 사용자 입력)
        texts = PostcardService._map_simple_text(template, text)

        # 2-1. 발신자 이름 추가 (sender 영역이 있고 sender_name이 제공된 경우)
        if sender_name:
            # "sender" 또는 "from" ID를 가진 text_config가 있으면 자동 매핑
            sender_config = next(
                (cfg for cfg in template.text_configs if cfg.id in ["sender"]),
                None
            )
            if sender_config:
                texts[sender_config.id] = sender_name

        # 3. 이미지 매핑
        photos = None

        if image:
            # 이미지 형식 검증
            if image.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"사진은 JPEG 또는 PNG 형식만 업로드 가능합니다: {image.filename}"
                )

            # "user_photo" ID 또는 첫 번째 photo_config에 매핑
            target_photo_id = PostcardService._map_simple_photo(template)
            if target_photo_id:
                photo_bytes = await image.read()
                photos = {target_photo_id: photo_bytes}

        # 4. 엽서 생성
        service = PostcardService(db)
        postcard = await service.create_postcard(
            template_id=template_id,
            texts=texts,
            photos=photos,
            sender_name=sender_name,
            user_id=current_user.id,
        )

        return postcard

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"포스트카드 생성 중 오류가 발생했습니다: {str(e)}"
        )
