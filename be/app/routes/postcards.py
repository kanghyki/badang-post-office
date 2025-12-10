"""
엽서 API 라우터

엽서 생성 및 예약 발송 엔드포인트를 제공합니다.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Body, Query
from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from app.database.database import get_db
from app.database.models import User, Postcard
from app.services.postcard_service import PostcardService
from app.services.email_service import EmailService
from app.services.storage_service import LocalStorageService
from app.models.postcard import PostcardResponse, PostcardCreateRequest, PostcardUpdateRequest
from app.services import template_service
from app.dependencies.auth import get_current_user
from app.scheduler_instance import get_scheduler
from app.utils.url import convert_static_path_to_url
import logging

router = APIRouter(prefix="/v1/postcards", tags=["Postcards"])
logger = logging.getLogger(__name__)


@router.post("/send", response_model=PostcardResponse)
async def create_and_send_postcard(
    template_id: str = Form(..., description="사용할 템플릿 ID"),
    text: str = Form(..., description="엽서에 들어갈 본문 텍스트"),
    recipient_email: str = Form(..., description="수신자 이메일 (필수)"),
    sender_name: Optional[str] = Form(None, description="발신자 이름 (선택)"),
    recipient_name: Optional[str] = Form(None, description="수신자 이름 (선택)"),
    scheduled_at: Optional[str] = Form(None, description="발송 예정 시간 (ISO 8601 형식, 없으면 즉시 발송, ex: 2025-12-10T16:08:30+09:00)"),
    image: Optional[UploadFile] = File(None, description="사용자 사진 (선택)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    포스트카드 생성 및 발송 (즉시/예약)

    - scheduled_at이 없으면: 즉시 발송 (엽서 생성 → 이메일 발송)
    - scheduled_at이 있으면: 예약 발송 (예약 등록 → 시간 되면 자동 발송)
    """
    try:
        # scheduled_at 파싱
        scheduled_datetime = None
        if scheduled_at:
            try:
                scheduled_datetime = datetime.fromisoformat(scheduled_at.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="scheduled_at은 ISO 8601 형식이어야 합니다 (예: 2025-12-15T14:00:00+09:00)"
                )
        
        # 검증
        request_data = PostcardCreateRequest(
            template_id=template_id,
            text=text,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            sender_name=sender_name,
            scheduled_at=scheduled_datetime
        )
        # 발신자 이름 기본값: 사용자 이름
        if not sender_name:
            sender_name = current_user.name

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
        user_photo_paths = {}
        photos = None

        if image:
            logger.info(f"User uploaded image: filename={image.filename}, content_type={image.content_type}")
            # 이미지 형식 검증
            if image.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"사진은 JPEG 또는 PNG 형식만 업로드 가능합니다: {image.filename}"
                )

            # "user_photo" ID 또는 첫 번째 photo_config에 매핑
            target_photo_id = PostcardService._map_simple_photo(template)
            logger.info(f"Target photo_id for user image: {target_photo_id}")
            if target_photo_id:
                photo_bytes = await image.read()
                logger.info(f"Read {len(photo_bytes)} bytes from uploaded image")
                storage = LocalStorageService()
                saved_path = await storage.save_user_photo(photo_bytes, "jpg")
                user_photo_paths[target_photo_id] = saved_path
                photos = {target_photo_id: photo_bytes}
                logger.info(f"Mapped user photo: photo_id={target_photo_id}, saved_path={saved_path}")
            else:
                logger.warning(f"Template {template_id} has no photo_configs to map user image to")
        else:
            logger.info("No image uploaded by user")

        # 즉시 발송
        if not scheduled_datetime:
            # 엽서 이미지 생성 및 DB 저장
            service = PostcardService(db)
            postcard_result = await service.create_postcard(
                template_id=template_id,
                texts=texts,
                photos=photos,
                sender_name=sender_name,
                user_id=current_user.id,
                recipient_email=recipient_email,
            )
            
            # 생성된 Postcard 조회
            stmt = select(Postcard).where(Postcard.id == postcard_result.id)
            result = await db.execute(stmt)
            postcard = result.scalar_one()
            
            # recipient_name 업데이트
            if recipient_name:
                stmt = (
                    update(Postcard)
                    .where(Postcard.id == postcard.id)
                    .values(recipient_name=recipient_name)
                )
                await db.execute(stmt)
                await db.commit()
                await db.refresh(postcard)

            # 5. 이메일 발송
            try:
                email_service = EmailService()
                await email_service.send_postcard_email(
                    to_email=recipient_email,
                    to_name=recipient_name,
                    postcard_image_path=postcard.postcard_image_path,
                    sender_name=sender_name
                )
                
                # 상태 업데이트: sent
                stmt = (
                    update(Postcard)
                    .where(Postcard.id == postcard.id)
                    .values(status="sent", sent_at=datetime.utcnow())
                )
                await db.execute(stmt)
                await db.commit()
                await db.refresh(postcard)
                
                logger.info(f"Postcard {postcard.id} sent immediately to {recipient_email}")
                
            except Exception as e:
                # 이메일 발송 실패
                stmt = (
                    update(Postcard)
                    .where(Postcard.id == postcard.id)
                    .values(status="failed", error_message=str(e))
                )
                await db.execute(stmt)
                await db.commit()
                await db.refresh(postcard)
                
                logger.error(f"Failed to send postcard {postcard.id}: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"엽서는 생성되었으나 이메일 발송에 실패했습니다: {str(e)}"
                )
        
        # 예약 발송
        else:
            # DB에 예약 정보 저장 (pending 상태)
            postcard = Postcard(
                user_id=current_user.id,
                template_id=template_id,
                text_contents=texts,
                user_photo_paths=user_photo_paths if user_photo_paths else None,
                recipient_email=recipient_email,
                recipient_name=recipient_name,
                sender_name=sender_name,
                status="pending",
                scheduled_at=request_data.scheduled_at,
                postcard_image_path=None  # 아직 생성 안됨
            )
            
            db.add(postcard)
            await db.commit()
            await db.refresh(postcard)
            
            # 스케줄러에 등록
            scheduler = get_scheduler()
            success = await scheduler.schedule_postcard(
                postcard.id,
                request_data.scheduled_at
            )
            
            if not success:
                # 스케줄러 등록 실패 시 DB에서도 삭제
                await db.delete(postcard)
                await db.commit()
                raise HTTPException(
                    status_code=500,
                    detail="스케줄러 등록에 실패했습니다."
                )
            
            logger.info(f"Scheduled postcard {postcard.id} for {scheduled_at}")

        # 6. 응답
        display_text = postcard.text_contents.get("main_text", "")
        if not display_text and postcard.text_contents:
            display_text = next(iter(postcard.text_contents.values()), "")

        return PostcardResponse(
            id=postcard.id,
            template_id=postcard.template_id,
            text=display_text,
            recipient_email=postcard.recipient_email,
            recipient_name=postcard.recipient_name,
            sender_name=postcard.sender_name,
            status=postcard.status,
            scheduled_at=postcard.scheduled_at,
            sent_at=postcard.sent_at,
            postcard_path=convert_static_path_to_url(postcard.postcard_image_path),
            error_message=postcard.error_message,
            created_at=postcard.created_at,
            updated_at=postcard.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"포스트카드 처리 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("", response_model=List[PostcardResponse])
async def list_postcards(
    status: Optional[str] = Query(None, description="상태 필터 (pending, sent, failed, cancelled)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    엽서 목록 조회
    
    사용자가 보낸/예약한 엽서 목록을 조회합니다. 상태별로 필터링 가능합니다.
    """
    try:
        stmt = select(Postcard).where(Postcard.user_id == current_user.id)
        
        if status:
            if status not in ["pending", "sent", "failed", "cancelled"]:
                raise HTTPException(
                    status_code=400,
                    detail="status는 pending, sent, failed, cancelled 중 하나여야 합니다."
                )
            stmt = stmt.where(Postcard.status == status)
        
        stmt = stmt.order_by(Postcard.created_at.desc())
        
        result = await db.execute(stmt)
        postcards = result.scalars().all()
        
        responses = []
        for postcard in postcards:
            text = postcard.text_contents.get("main_text", "")
            if not text and postcard.text_contents:
                text = next(iter(postcard.text_contents.values()), "")
            
            responses.append(PostcardResponse(
                id=postcard.id,
                template_id=postcard.template_id,
                text=text,
                recipient_email=postcard.recipient_email,
                recipient_name=postcard.recipient_name,
                sender_name=postcard.sender_name,
                status=postcard.status,
                scheduled_at=postcard.scheduled_at,
                sent_at=postcard.sent_at,
                postcard_path=convert_static_path_to_url(postcard.postcard_image_path),
                error_message=postcard.error_message,
                created_at=postcard.created_at,
                updated_at=postcard.updated_at
            ))
        
        return responses
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list postcards: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"엽서 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/{postcard_id}", response_model=PostcardResponse)
async def get_postcard(
    postcard_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """엽서 상세 조회"""
    try:
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
        
        text = postcard.text_contents.get("main_text", "")
        if not text and postcard.text_contents:
            text = next(iter(postcard.text_contents.values()), "")
        
        return PostcardResponse(
            id=postcard.id,
            template_id=postcard.template_id,
            text=text,
            recipient_email=postcard.recipient_email,
            recipient_name=postcard.recipient_name,
            sender_name=postcard.sender_name,
            status=postcard.status,
            scheduled_at=postcard.scheduled_at,
            sent_at=postcard.sent_at,
            postcard_path=convert_static_path_to_url(postcard.postcard_image_path),
            error_message=postcard.error_message,
            created_at=postcard.created_at,
            updated_at=postcard.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get postcard {postcard_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"엽서 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.patch("/{postcard_id}", response_model=PostcardResponse)
async def update_postcard(
    postcard_id: str,
    scheduled_at: Optional[str] = Form(None, description="새로운 발송 예정 시간 (ISO 8601 형식)"),
    text: Optional[str] = Form(None, description="새로운 텍스트"),
    recipient_email: Optional[str] = Form(None, description="새로운 수신자 이메일"),
    recipient_name: Optional[str] = Form(None, description="새로운 수신자 이름"),
    sender_name: Optional[str] = Form(None, description="새로운 발신자 이름"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    엽서 수정 (pending 상태만 가능)
    """
    try:
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
        
        if postcard.status != "pending":
            raise HTTPException(
                status_code=400,
                detail=f"pending 상태의 엽서만 수정 가능합니다. (현재 상태: {postcard.status})"
            )
        
        # 업데이트할 필드
        update_values = {"updated_at": datetime.utcnow()}
        new_scheduled_at = None
        
        if scheduled_at:
            try:
                new_scheduled_at = datetime.fromisoformat(scheduled_at.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="scheduled_at은 ISO 8601 형식이어야 합니다"
                )
            
            # 검증
            update_data = PostcardUpdateRequest(scheduled_at=new_scheduled_at)
            update_values["scheduled_at"] = update_data.scheduled_at
        
        if text:
            template = template_service.get_template_by_id(postcard.template_id)
            if template:
                texts = PostcardService._map_simple_text(template, text)
                if postcard.sender_name:
                    sender_config = next(
                        (cfg for cfg in template.text_configs if cfg.id in ["sender"]),
                        None
                    )
                    if sender_config:
                        texts[sender_config.id] = postcard.sender_name
                update_values["text_contents"] = texts
        
        if recipient_email:
            update_values["recipient_email"] = recipient_email
        
        if recipient_name is not None:
            update_values["recipient_name"] = recipient_name
        
        if sender_name is not None:
            update_values["sender_name"] = sender_name
        
        # DB 업데이트
        stmt = (
            update(Postcard)
            .where(Postcard.id == postcard_id)
            .values(**update_values)
        )
        await db.execute(stmt)
        await db.commit()
        
        # 스케줄러 업데이트 (예약 시간 변경 시)
        if new_scheduled_at and postcard.scheduled_at:
            scheduler = get_scheduler()
            success = await scheduler.reschedule_postcard(
                postcard_id,
                update_values["scheduled_at"]
            )
            if not success:
                logger.warning(f"Failed to reschedule {postcard_id} in scheduler")
        
        # 업데이트된 데이터 조회
        await db.refresh(postcard)
        
        display_text = postcard.text_contents.get("main_text", "")
        if not display_text and postcard.text_contents:
            display_text = next(iter(postcard.text_contents.values()), "")
        
        return PostcardResponse(
            id=postcard.id,
            template_id=postcard.template_id,
            text=display_text,
            recipient_email=postcard.recipient_email,
            recipient_name=postcard.recipient_name,
            sender_name=postcard.sender_name,
            status=postcard.status,
            scheduled_at=postcard.scheduled_at,
            sent_at=postcard.sent_at,
            postcard_path=convert_static_path_to_url(postcard.postcard_image_path),
            error_message=postcard.error_message,
            created_at=postcard.created_at,
            updated_at=postcard.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"엽서 수정 중 오류가 발생했습니다: {str(e)}"
        )


@router.delete("/{postcard_id}", status_code=204)
async def cancel_postcard(
    postcard_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    엽서 취소 (pending 상태만 가능)
    """
    try:
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
        
        if postcard.status != "pending":
            raise HTTPException(
                status_code=400,
                detail=f"pending 상태의 엽서만 취소 가능합니다. (현재 상태: {postcard.status})"
            )
        
        # 스케줄러에서 제거 (예약된 경우)
        if postcard.scheduled_at:
            scheduler = get_scheduler()
            await scheduler.cancel_schedule(postcard_id)
        
        # DB 상태 업데이트
        stmt = (
            update(Postcard)
            .where(Postcard.id == postcard_id)
            .values(status="cancelled", updated_at=datetime.utcnow())
        )
        await db.execute(stmt)
        await db.commit()
        
        logger.info(f"Cancelled postcard {postcard_id}")
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel postcard {postcard_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"엽서 취소 중 오류가 발생했습니다: {str(e)}"
        )
