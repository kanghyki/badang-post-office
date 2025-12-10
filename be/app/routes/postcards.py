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
    """
    try:
        # 1. 사용 가능한 템플릿 중 하나 자동 선택
        available_templates = template_service.get_all_templates()
        if not available_templates:
            raise HTTPException(
                status_code=500,
                detail="사용 가능한 템플릿이 없습니다."
            )
        
        # 첫 번째 템플릿 자동 선택
        template = available_templates[0]
        template_id = template.id
        
        logger.info(f"Auto-selected template: {template_id}")

        # 2. 빈 엽서 레코드 생성
        postcard = Postcard(
            user_id=current_user.id,
            template_id=template_id,
            text_contents=None,
            original_text_contents=None,
            user_photo_paths=None,
            recipient_email=None,
            recipient_name=None,
            sender_name=None,
            status="writing",
            scheduled_at=None,
            postcard_image_path=None
        )

        db.add(postcard)
        await db.commit()
        await db.refresh(postcard)

        logger.info(f"Created empty postcard {postcard.id} in writing state")

        # 3. 응답
        return PostcardResponse(
            id=postcard.id,
            template_id=postcard.template_id,
            text=None,
            original_text=None,
            recipient_email=None,
            recipient_name=None,
            sender_name=None,
            status=postcard.status,
            scheduled_at=None,
            sent_at=None,
            postcard_path=None,
            error_message=None,
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
            detail=f"엽서 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("", response_model=List[PostcardResponse])
async def list_postcards(
    status: Optional[str] = Query(None, description="상태 필터 (writing, pending, sent, failed, cancelled)"),
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
            if status not in ["writing", "pending", "sent", "failed", "cancelled"]:
                raise HTTPException(
                    status_code=400,
                    detail="status는 writing, pending, sent, failed, cancelled 중 하나여야 합니다."
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

            # 원본 텍스트 추출
            original_text = ""
            if postcard.original_text_contents:
                original_text = postcard.original_text_contents.get("main_text", "")
                if not original_text:
                    original_text = next(iter(postcard.original_text_contents.values()), "")

            responses.append(PostcardResponse(
                id=postcard.id,
                template_id=postcard.template_id,
                text=text,  # 제주어
                original_text=original_text,  # 원본
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

        # 원본 텍스트 추출
        original_text = ""
        if postcard.original_text_contents:
            original_text = postcard.original_text_contents.get("main_text", "")
            if not original_text:
                original_text = next(iter(postcard.original_text_contents.values()), "")

        return PostcardResponse(
            id=postcard.id,
            template_id=postcard.template_id,
            text=text,  # 제주어
            original_text=original_text,  # 원본
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
    image: Optional[UploadFile] = File(None, description="사용자 사진 (선택)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    엽서 수정 (writing 또는 pending 상태만 가능)

    텍스트 수정 시 제주어 번역 + 엽서 이미지 자동 생성
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

        if postcard.status not in ["writing", "pending"]:
            raise HTTPException(
                status_code=400,
                detail=f"writing 또는 pending 상태의 엽서만 수정 가능합니다. (현재 상태: {postcard.status})"
            )
        
        # 업데이트할 필드
        update_values = {"updated_at": datetime.utcnow()}
        new_scheduled_at = None
        
        # 이미지 업로드 처리
        if image:
            logger.info(f"User uploaded image: filename={image.filename}, content_type={image.content_type}")
            # 이미지 형식 검증
            if image.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"사진은 JPEG 또는 PNG 형식만 업로드 가능합니다: {image.filename}"
                )

            template = template_service.get_template_by_id(postcard.template_id)
            if template:
                # "user_photo" ID 또는 첫 번째 photo_config에 매핑
                target_photo_id = PostcardService._map_simple_photo(template)
                logger.info(f"Target photo_id for user image: {target_photo_id}")
                if target_photo_id:
                    photo_bytes = await image.read()
                    logger.info(f"Read {len(photo_bytes)} bytes from uploaded image")
                    storage = LocalStorageService()
                    saved_path = await storage.save_user_photo(photo_bytes, "jpg")
                    
                    # user_photo_paths 업데이트
                    user_photo_paths = postcard.user_photo_paths or {}
                    user_photo_paths[target_photo_id] = saved_path
                    update_values["user_photo_paths"] = user_photo_paths
                    logger.info(f"Updated user photo: photo_id={target_photo_id}, saved_path={saved_path}")
                else:
                    logger.warning(f"Template {postcard.template_id} has no photo_configs to map user image to")
        
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
        
        # 텍스트 수정 시 번역 수행
        if text:
            template = template_service.get_template_by_id(postcard.template_id)
            if template:
                # 원본 텍스트 매핑
                original_texts = PostcardService._map_simple_text(template, text)
                if postcard.sender_name:
                    sender_config = next(
                        (cfg for cfg in template.text_configs if cfg.id in ["sender"]),
                        None
                    )
                    if sender_config:
                        original_texts[sender_config.id] = postcard.sender_name

                # 제주어 번역
                texts = await PostcardService._translate_user_text_to_jeju(template, original_texts)
                if postcard.sender_name:
                    sender_config = next(
                        (cfg for cfg in template.text_configs if cfg.id in ["sender"]),
                        None
                    )
                    if sender_config:
                        texts[sender_config.id] = postcard.sender_name

                update_values["text_contents"] = texts
                update_values["original_text_contents"] = original_texts
        
        if recipient_email:
            update_values["recipient_email"] = recipient_email
        
        if recipient_name is not None:
            update_values["recipient_name"] = recipient_name
        
        if sender_name is not None:
            update_values["sender_name"] = sender_name
        
        # 엽서 이미지 생성 (텍스트 또는 이미지 변경 시)
        if text or image:
            template = template_service.get_template_by_id(postcard.template_id)
            if template:
                # 최신 텍스트 사용 (업데이트된 값 또는 기존 값)
                texts = update_values.get("text_contents") or postcard.text_contents
                
                # 텍스트가 없으면 엽서 이미지 생성 불가
                if not texts:
                    logger.warning(f"Cannot generate postcard image without text content")
                else:
                    # 최신 사진 경로 사용 (업데이트된 값 또는 기존 값)
                    user_photo_paths = update_values.get("user_photo_paths") or postcard.user_photo_paths
                    
                    photos = {}
                    if user_photo_paths:
                        storage = LocalStorageService()
                        for photo_id, photo_path in user_photo_paths.items():
                            photo_bytes = await storage.read_file(photo_path)
                            if photo_bytes:
                                photos[photo_id] = photo_bytes
                                logger.info(f"Loaded photo {photo_id} from {photo_path}")

                    service = PostcardService(db)
                    postcard_result = await service.create_postcard(
                        template_id=postcard.template_id,
                        texts=texts,
                        photos=photos if photos else None,
                        sender_name=update_values.get("sender_name") or postcard.sender_name,
                        user_id=current_user.id,
                        recipient_email=update_values.get("recipient_email") or postcard.recipient_email,
                    )

                    # 생성된 이미지 경로 저장
                    update_values["postcard_image_path"] = postcard_result.postcard_path

                    # 임시 레코드 삭제
                    temp_postcard = await db.get(Postcard, postcard_result.id)
                    if temp_postcard:
                        await db.delete(temp_postcard)
                        await db.flush()
        
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

        display_text = None
        if postcard.text_contents:
            display_text = postcard.text_contents.get("main_text", "")
            if not display_text:
                display_text = next(iter(postcard.text_contents.values()), "")

        # 원본 텍스트 추출
        original_display_text = ""
        if postcard.original_text_contents:
            original_display_text = postcard.original_text_contents.get("main_text", "")
            if not original_display_text:
                original_display_text = next(iter(postcard.original_text_contents.values()), "")

        return PostcardResponse(
            id=postcard.id,
            template_id=postcard.template_id,
            text=display_text,  # 제주어
            original_text=original_display_text,  # 원본
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
    엽서 취소 또는 삭제 (writing 또는 pending 상태만 가능)
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

        if postcard.status not in ["writing", "pending"]:
            raise HTTPException(
                status_code=400,
                detail=f"writing 또는 pending 상태의 엽서만 취소/삭제 가능합니다. (현재 상태: {postcard.status})"
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
    """
    try:
        # 1. 엽서 조회
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

        if postcard.status not in ["writing", "pending"]:
            raise HTTPException(
                status_code=400,
                detail=f"writing 또는 pending 상태의 엽서만 발송 가능합니다. (현재 상태: {postcard.status})"
            )

        # 엽서 이미지 생성 여부 확인
        if not postcard.postcard_image_path:
            raise HTTPException(
                status_code=400,
                detail="엽서 이미지가 생성되지 않았습니다. PATCH /v1/postcards/{id}로 먼저 엽서를 수정하여 이미지를 생성하세요."
            )

        # 수신자 이메일 검증
        if not postcard.recipient_email:
            raise HTTPException(
                status_code=400,
                detail="수신자 이메일이 설정되지 않았습니다. PATCH /v1/postcards/{id}로 수신자 정보를 입력하세요."
            )

        # 2. 즉시 발송 (scheduled_at이 없는 경우)
        if not postcard.scheduled_at:
            # 이메일 발송
            try:
                email_service = EmailService()
                await email_service.send_postcard_email(
                    to_email=postcard.recipient_email,
                    to_name=postcard.recipient_name,
                    postcard_image_path=postcard.postcard_image_path,
                    sender_name=postcard.sender_name
                )

                # 상태 업데이트: sent
                stmt = (
                    update(Postcard)
                    .where(Postcard.id == postcard_id)
                    .values(status="sent", sent_at=datetime.utcnow())
                )
                await db.execute(stmt)
                await db.commit()
                await db.refresh(postcard)

                logger.info(f"Postcard {postcard_id} sent immediately to {postcard.recipient_email}")

            except Exception as e:
                # 이메일 발송 실패
                stmt = (
                    update(Postcard)
                    .where(Postcard.id == postcard_id)
                    .values(status="failed", error_message=str(e))
                )
                await db.execute(stmt)
                await db.commit()
                await db.refresh(postcard)

                logger.error(f"Failed to send postcard {postcard_id}: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"엽서는 생성되었으나 이메일 발송에 실패했습니다: {str(e)}"
                )

        # 3-2. 예약 발송 (scheduled_at이 설정되어 있는 경우)
        else:
            # pending 상태로 변경
            stmt = (
                update(Postcard)
                .where(Postcard.id == postcard_id)
                .values(
                    status="pending",
                    updated_at=datetime.utcnow()
                )
            )
            await db.execute(stmt)
            await db.commit()
            await db.refresh(postcard)

            # 스케줄러에 등록
            scheduler = get_scheduler()
            success = await scheduler.schedule_postcard(
                postcard_id,
                postcard.scheduled_at
            )

            if not success:
                # 스케줄러 등록 실패 시 상태를 다시 writing으로 되돌림
                stmt = (
                    update(Postcard)
                    .where(Postcard.id == postcard_id)
                    .values(status="writing")
                )
                await db.execute(stmt)
                await db.commit()
                raise HTTPException(
                    status_code=500,
                    detail="스케줄러 등록에 실패했습니다."
                )

            logger.info(f"Scheduled postcard {postcard_id} for {postcard.scheduled_at}")

        # 4. 응답
        display_text = None
        if postcard.text_contents:
            display_text = postcard.text_contents.get("main_text", "")
            if not display_text:
                display_text = next(iter(postcard.text_contents.values()), "")

        # 원본 텍스트 추출
        original_display_text = ""
        if postcard.original_text_contents:
            original_display_text = postcard.original_text_contents.get("main_text", "")
            if not original_display_text:
                original_display_text = next(iter(postcard.original_text_contents.values()), "")

        return PostcardResponse(
            id=postcard.id,
            template_id=postcard.template_id,
            text=display_text,  # 제주어
            original_text=original_display_text,  # 원본
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
            detail=f"엽서 발송 중 오류가 발생했습니다: {str(e)}"
        )
