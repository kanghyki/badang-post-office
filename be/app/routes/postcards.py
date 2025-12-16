"""
엽서 API 라우터

엽서 생성 및 예약 발송 엔드포인트를 제공합니다.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Query, BackgroundTasks
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.database.database import get_db
from app.database.models import User, Postcard
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
    background_tasks: BackgroundTasks,
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

    텍스트는 원본으로 저장되며, 제주어 번역은 발송 시점에 수행됩니다.
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
            scheduled_at=scheduled_at,
            background_tasks=background_tasks
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
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    엽서 발송 (writing 또는 pending 상태의 엽서만 가능)

    엽서 이미지가 자동으로 생성되고 발송됩니다.
    - scheduled_at이 없으면: 백그라운드에서 비동기 발송 (processing → sent 상태)
      * 진행 상태는 SSE 엔드포인트 (/stream)로 실시간 확인 가능
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
        return await service.send_postcard(
            postcard_id=postcard_id,
            user_id=current_user.id,
            background_tasks=background_tasks
        )
    except ValueError as e:
        error_msg = str(e)

        # 발송 제한 체크
        if "발송 제한에 도달했습니다" in error_msg:
            raise HTTPException(
                status_code=429,
                detail={
                    "message": error_msg,
                    "error_code": "POSTCARD_LIMIT_EXCEEDED"
                }
            )

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


@router.get("/{postcard_id}/stream")
async def stream_postcard_status(
    postcard_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    엽서 변환 상태를 SSE로 실시간 스트리밍

    클라이언트는 EventSource로 연결하여 변환 상태를 실시간으로 받습니다.
    """
    from fastapi.responses import StreamingResponse
    from app.services.redis_service import redis_service
    import json

    # 엽서 소유권 확인
    service = PostcardService(db)
    stmt = select(Postcard).where(
        and_(
            Postcard.id == postcard_id,
            Postcard.user_id == current_user.id
        )
    )
    result = await db.execute(stmt)
    postcard = result.scalar_one_or_none()

    if not postcard:
        raise HTTPException(status_code=404, detail="엽서를 찾을 수 없습니다.")

    async def event_generator():
        """SSE 이벤트 제너레이터"""
        try:
            # 현재 엽서 발송 상태 즉시 전송
            current_status = postcard.status

            # processing 상태가 아니면 초기 상태 전송하고 종료
            if current_status != "processing":
                if current_status == "sent":
                    yield f"data: {json.dumps({'status': 'completed'})}\n\n"
                elif current_status == "failed":
                    yield f"data: {json.dumps({'status': 'failed', 'error': postcard.error_message or '발송 실패'})}\n\n"
                return

            # processing 상태: Redis Pub/Sub 구독하여 실시간 상태 전송
            async for message in redis_service.subscribe(f"postcard:{postcard_id}"):
                yield f"data: {message}\n\n"

                # 완료/실패 시 연결 종료
                data = json.loads(message)
                if data.get("status") in ["completed", "failed"]:
                    break

        except Exception as e:
            logger.error(f"SSE stream error: {str(e)}")
            yield f"data: {json.dumps({'status': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Nginx 버퍼링 비활성화
        }
    )
