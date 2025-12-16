"""
엽서 API 라우터

엽서 생성 및 예약 발송 엔드포인트를 제공합니다.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Query
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.database.models import User
from app.services.postcard_service import PostcardService
from app.models.postcard import PostcardResponse
from app.dependencies.auth import get_current_user
import logging

router = APIRouter(prefix="/v1/postcards", tags=["Postcards"])
logger = logging.getLogger(__name__)


@router.post("/create", response_model=PostcardResponse)
async def create_postcard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    빈 엽서 생성

    "엽서 작성" 버튼 클릭 시 호출됩니다.
    템플릿이 자동으로 선택되며, 빈 엽서가 writing 상태로 생성됩니다.
    PATCH /v1/postcards/{id}로 내용을 입력하고,
    POST /v1/postcards/{id}/send로 발송할 수 있습니다.

    ⚠️ 이메일 인증이 필요합니다.
    """
    # 이메일 인증 확인
    if not current_user.is_email_verified:
        raise HTTPException(
            status_code=403,
            detail="엽서를 작성하려면 이메일 인증이 필요합니다. 프로필 페이지에서 인증 메일을 받을 수 있습니다."
        )

    try:
        service = PostcardService(db)
        return await service.create_empty_postcard(user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create postcard: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="엽서 생성 중 오류가 발생했습니다."
        )


@router.get("", response_model=List[PostcardResponse])
async def list_postcards(
    status: Optional[str] = Query(None, description="상태 필터 (writing, pending, sent, failed)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    엽서 목록 조회
    
    사용자가 보낸/예약한 엽서 목록을 조회합니다. 상태별로 필터링 가능합니다.
    """
    try:
        service = PostcardService(db)
        return await service.list_postcards(
            user_id=current_user.id,
            status_filter=status
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to list postcards: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="엽서 목록 조회 중 오류가 발생했습니다."
        )


@router.get("/{postcard_id}", response_model=PostcardResponse)
async def get_postcard(
    postcard_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """엽서 상세 조회"""
    try:
        service = PostcardService(db)
        postcard = await service.get_postcard_by_id(
            postcard_id=postcard_id,
            user_id=current_user.id
        )
        
        if not postcard:
            raise HTTPException(status_code=404, detail="엽서를 찾을 수 없습니다.")
        
        return postcard
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get postcard: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="엽서 조회 중 오류가 발생했습니다."
        )





@router.patch("/{postcard_id}", response_model=PostcardResponse)
async def update_postcard(
    postcard_id: str,
    scheduled_at: Optional[str] = Form(None, description="새로운 발송 예정 시간 (ISO 8601 형식)"),
    text: Optional[str] = Form(None, description="새로운 텍스트"),
    recipient_email: Optional[str] = Form(None, description="새로운 수신자 이메일"),
    recipient_name: Optional[str] = Form(None, description="새로운 수신자 이름"),
    sender_name: Optional[str] = Form(None, description="새로운 발신자 이름"),
    template_id: Optional[str] = Form(None, description="새로운 템플릿 ID"),
    image: Optional[UploadFile] = File(None, description="사용자 사진 (선택)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    엽서 수정 (writing 또는 pending 상태만 가능)

    텍스트 수정 시 제주어 번역 + 엽서 이미지 자동 생성
    """
    try:
        # 이미지 검증 및 변환
        image_bytes = None
        if image:
            logger.info(f"User uploaded image: filename={image.filename}, content_type={image.content_type}")
            if image.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"사진은 JPEG 또는 PNG 형식만 업로드 가능합니다: {image.filename}"
                )
            image_bytes = await image.read()
            logger.info(f"Read {len(image_bytes)} bytes from uploaded image")
        
        # Service 호출
        service = PostcardService(db)
        return await service.update_postcard(
            postcard_id=postcard_id,
            user_id=current_user.id,
            text=text,
            image_bytes=image_bytes,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            sender_name=sender_name,
            template_id=template_id,
            scheduled_at=scheduled_at
        )
        
    except ValueError as e:
        # Service에서 발생한 비즈니스 로직 에러
        error_msg = str(e)
        if "찾을 수 없습니다" in error_msg:
            raise HTTPException(status_code=404, detail=error_msg)
        else:
            raise HTTPException(status_code=400, detail=error_msg)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update postcard: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="엽서 수정 중 오류가 발생했습니다."
        )


@router.delete("/{postcard_id}", status_code=204)
async def delete_postcard(
    postcard_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    엽서 삭제 (DB에서 완전히 제거)
    """
    try:
        service = PostcardService(db)
        await service.delete_postcard(postcard_id=postcard_id, user_id=current_user.id)
        return None
    except ValueError as e:
        error_msg = str(e)
        if "찾을 수 없습니다" in error_msg:
            raise HTTPException(status_code=404, detail=error_msg)
        else:
            raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        logger.error(f"Failed to delete postcard {postcard_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="엽서 삭제 중 오류가 발생했습니다."
        )


@router.post("/{postcard_id}/cancel", status_code=204)
async def cancel_postcard(
    postcard_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    예약된 엽서 취소 (pending 상태만 가능)

    예약을 취소하면 상태가 writing으로 되돌아가며,
    예약 시간이 제거되고 스케줄러에서 제거됩니다.
    사용자는 다시 수정하고 재발송할 수 있습니다.
    """
    try:
        service = PostcardService(db)
        await service.cancel_postcard(postcard_id=postcard_id, user_id=current_user.id)
        return None
    except ValueError as e:
        error_msg = str(e)
        if "찾을 수 없습니다" in error_msg:
            raise HTTPException(status_code=404, detail=error_msg)
        else:
            raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        logger.error(f"Failed to cancel postcard {postcard_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="엽서 취소 중 오류가 발생했습니다."
        )


@router.post("/{postcard_id}/send", response_model=PostcardResponse)
async def send_postcard(
    postcard_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    엽서 발송 (writing 또는 pending 상태의 엽서만 가능)

    PATCH /v1/postcards/{id}로 엽서 이미지를 먼저 생성한 후 이 API를 호출하세요.
    - scheduled_at이 없으면: 즉시 발송 (이메일 발송 → sent 상태)
    - scheduled_at이 설정되어 있으면: pending 상태로 변경 → 스케줄러 등록

    ⚠️ 이메일 인증이 필요합니다.
    """
    # 이메일 인증 확인
    if not current_user.is_email_verified:
        raise HTTPException(
            status_code=403,
            detail="엽서를 발송하려면 이메일 인증이 필요합니다. 프로필 페이지에서 인증 메일을 다시 받을 수 있습니다."
        )

    try:
        service = PostcardService(db)
        return await service.send_postcard(postcard_id=postcard_id, user_id=current_user.id)
    except ValueError as e:
        error_msg = str(e)
        if "찾을 수 없습니다" in error_msg:
            raise HTTPException(status_code=404, detail=error_msg)
        elif "이메일 발송에 실패했습니다" in error_msg:
            raise HTTPException(status_code=500, detail=error_msg)
        else:
            raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        logger.error(f"Failed to send postcard: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="엽서 발송 중 오류가 발생했습니다."
        )
