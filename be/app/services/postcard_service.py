"""
엽서 생성 서비스

템플릿, 사진, 텍스트를 조합하여 엽서를 생성하고 로컬에 저장하는 핵심 비즈니스 로직을 제공합니다.
"""

import os
import uuid as uuid_lib
import logging
import pytz
from typing import Optional, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.database.models import Postcard
from app.services.storage_service import LocalStorageService
from app.services import template_service, font_service
from app.services.postcards.postcard_maker import PostcardMaker
from app.services.postcards.text_wrapper import TextWrapper
from app.models.postcard import PostcardResponse
from app.config import settings
from app.utils.url import convert_static_path_to_url
from app.utils.postcard_helpers import extract_main_text

logger = logging.getLogger(__name__)


class PostcardService:
    """엽서 생성 및 관리 서비스"""

    def __init__(self, db: AsyncSession):
        """
        PostcardService 초기화

        Args:
            db: SQLAlchemy AsyncSession 인스턴스 (Postcard 저장을 위해 필요)
        """
        self.db = db
        self.storage = LocalStorageService()

    @staticmethod
    def _generate_auto_field(config_id: str) -> Optional[str]:
        """
        특수 ID에 대한 자동 생성 값 반환

        Args:
            config_id: text_config의 ID

        Returns:
            자동 생성된 텍스트 또는 None (자동 생성 대상 아님)
        """
        from datetime import datetime

        # 날짜 관련 자동 생성
        if config_id.lower() == "date":
            return datetime.now().strftime("%Y.%m.%d")
        elif config_id.lower() == "datetime":
            return datetime.now().strftime("%Y.%m.%d %H:%M")
        elif config_id.lower() == "time":
            return datetime.now().strftime("%H:%M")
        elif config_id.lower() in ["year", "yyyy"]:
            return datetime.now().strftime("%Y")
        elif config_id.lower() in ["month", "mm"]:
            return datetime.now().strftime("%m")
        elif config_id.lower() in ["day", "dd"]:
            return datetime.now().strftime("%d")

        # 자동 생성 대상 아님
        return None

    @staticmethod
    def _map_simple_text(template, user_text: str) -> Dict[str, str]:
        """
        사용자 텍스트 하나를 템플릿의 text_configs에 매핑

        매핑 규칙:
        1. 자동 생성 필드 (date, datetime 등) → 자동 생성
        2. "main_text" ID를 가진 영역 → 사용자 입력 본문 (우선)
        3. "main_text"가 없으면 첫 번째 일반 영역 → 사용자 입력 본문
        4. 나머지 → 빈 문자열

        Args:
            template: 템플릿 객체
            user_text: 사용자가 입력한 본문 텍스트

        Returns:
            {config_id: text} 딕셔너리
        """
        result = {}

        # 먼저 "main_text" ID를 가진 영역이 있는지 확인
        has_main_text = any(cfg.id == "main_text" for cfg in template.text_configs)
        user_text_assigned = False

        for text_cfg in template.text_configs:
            config_id = text_cfg.id

            # 1. 자동 생성 필드 확인
            auto_value = PostcardService._generate_auto_field(config_id)
            if auto_value is not None:
                result[config_id] = auto_value
                continue

            # 2. "main_text" ID에 우선적으로 할당
            if config_id == "main_text":
                result[config_id] = user_text
                user_text_assigned = True
            # 3. "main_text"가 없으면 첫 번째 일반 영역에 할당
            elif not has_main_text and not user_text_assigned:
                result[config_id] = user_text
                user_text_assigned = True
            else:
                # 4. 나머지는 빈 문자열
                result[config_id] = ""

        return result

    @staticmethod
    async def _translate_user_text_to_jeju(
        template,
        original_texts: Dict[str, str]
    ) -> Dict[str, str]:
        """
        사용자 입력 텍스트를 제주어로 번역

        자동 생성 필드, 발신자 이름 등은 번역하지 않고,
        오직 사용자가 입력한 본문만 번역합니다.

        Args:
            template: 템플릿 객체
            original_texts: 원본 텍스트 딕셔너리 (config_id -> text)

        Returns:
            제주어로 번역된 텍스트 딕셔너리
        """
        from app.services.translation_service import translate_to_jeju_async
        translated_texts = {}

        for text_cfg in template.text_configs:
            config_id = text_cfg.id
            original_text = original_texts.get(config_id, "")

            # 빈 텍스트는 그대로
            if not original_text.strip():
                translated_texts[config_id] = original_text
                continue

            # 자동 생성 필드는 번역하지 않음
            if PostcardService._generate_auto_field(config_id) is not None:
                translated_texts[config_id] = original_text
                continue

            # 발신자 이름은 번역하지 않음
            if config_id == "sender":
                translated_texts[config_id] = original_text
                continue

            # 사용자 입력 본문만 번역
            try:
                logger.info(f"Translating text for config_id={config_id}: {original_text[:50]}...")
                translated_text = await translate_to_jeju_async(original_text)
                translated_texts[config_id] = translated_text
                logger.info(f"Translation success: {translated_text[:50]}...")
            except Exception as e:
                logger.error(f"Translation failed for config_id={config_id}: {str(e)}")
                # Fallback: 원본 사용
                translated_texts[config_id] = original_text

        return translated_texts

    @staticmethod
    def _map_simple_photo(template) -> Optional[str]:
        """
        사용자 이미지를 매핑할 photo_config의 ID 반환

        규칙:
        1. "user_photo" ID를 가진 영역 우선 사용
        2. "user_photo"가 없으면 첫 번째 photo_config 사용

        Args:
            template: 템플릿 객체

        Returns:
            photo_config의 ID 또는 None (photo_config가 없는 경우)
        """
        if not template.photo_configs or len(template.photo_configs) == 0:
            return None

        # 1. "user_photo" ID를 가진 영역 우선 검색
        for photo_cfg in template.photo_configs:
            if photo_cfg.id == "user_photo":
                return photo_cfg.id

        # 2. "user_photo"가 없으면 첫 번째 photo_config 사용
        return template.photo_configs[0].id

    async def create_postcard(
        self,
        template_id: str,
        texts: Dict[str, str],  # {text_config_id: text}
        photos: Optional[Dict[str, bytes]] = None,  # {photo_config_id: bytes}
        sender_name: Optional[str] = None,  # 발신자 이름
        user_id: Optional[str] = None,  # 사용자 ID
        recipient_email: Optional[str] = None,  # 수신자 이메일 (새 스키마용)
    ) -> PostcardResponse:
        """
        다중 텍스트/이미지를 지원하는 엽서 생성
        """
        # 1. 템플릿 조회 (메모리에서)
        template = template_service.get_template_by_id(template_id)
        if not template:
            raise ValueError("템플릿을 찾을 수 없습니다.")

        # 2. 이미지 저장 (여러 개)
        user_photo_paths = {}
        user_photo_temp_paths = {}

        if photos:
            logger.info(f"Processing {len(photos)} user photos for template {template_id}")
            for config_id, photo_bytes in photos.items():
                # 영구 저장
                saved_path = await self.storage.save_user_photo(photo_bytes, "jpg")
                user_photo_paths[config_id] = saved_path

                # 임시 파일 (PostcardMaker 사용) - tempfile 모듈로 안전한 임시 파일 생성
                import tempfile
                temp_fd, temp_path = tempfile.mkstemp(suffix=".jpg", prefix="postcard_")
                try:
                    with os.fdopen(temp_fd, "wb") as f:
                        f.write(photo_bytes)
                    user_photo_temp_paths[config_id] = temp_path
                    logger.info(f"Saved user photo for config_id={config_id}: temp={temp_path}, saved={saved_path}")
                except Exception as e:
                    # 파일 생성 실패 시 즉시 삭제 시도
                    os.close(temp_fd)
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    raise
        else:
            logger.warning(f"No photos provided for postcard creation")

        # 3. PostcardMaker 초기화
        template_path = self.storage.get_template_image_path(
            template.template_image_path
        )
        maker = PostcardMaker(
            width=template.width, height=template.height
        )
        maker.add_background_image(template_path, opacity=1.0)

        # 5. 이미지 영역 추가 (반복문)
        logger.info(f"Template has {len(template.photo_configs)} photo configs")
        for photo_cfg in template.photo_configs:
            config_id = photo_cfg.id
            logger.info(f"Processing photo_cfg: id={config_id}, available photos={list(user_photo_temp_paths.keys())}")
            if config_id in user_photo_temp_paths:
                logger.info(f"Adding user photo to postcard: config_id={config_id}, path={user_photo_temp_paths[config_id]}")
                maker.add_photo(
                    user_photo_temp_paths[config_id],
                    x=photo_cfg.x,
                    y=photo_cfg.y,
                    max_width=photo_cfg.max_width,
                    max_height=photo_cfg.max_height,
                    effects=photo_cfg.effects,  # 템플릿에 정의된 효과 적용
                )
            else:
                logger.warning(f"No user photo found for photo_cfg id={config_id}")

        # 6. 텍스트 영역 추가 (반복문)
        for text_cfg in template.text_configs:
            config_id = text_cfg.id
            text_content = texts.get(config_id, "")

            if not text_content.strip():
                continue  # 빈 텍스트는 스킵

            # 폰트 결정: 개별 font_id > 템플릿 기본 > None (시스템 기본)
            font_id = text_cfg.font_id or template.default_font_id

            # 폰트 로드 (줄바꿈 계산용)
            font = maker.font_manager.get_font(font_id=font_id, size=text_cfg.font_size)

            # 텍스트 줄바꿈 (실제 픽셀 너비 및 높이 기반)
            if text_cfg.max_width:
                # line_height 비율 계산
                line_height_ratio = getattr(text_cfg, 'line_height', 1.2)
                actual_line_height = int(text_cfg.font_size * line_height_ratio)
                
                wrapper = TextWrapper(
                    font=font,
                    max_width=text_cfg.max_width,
                    max_height=text_cfg.max_height,
                    line_height=actual_line_height
                )
                wrapped_text = wrapper.wrap(text_content)
            else:
                wrapped_text = text_content

            # 각 줄 그리기
            y_offset = text_cfg.y
            # line_height 비율 계산 (기본값 1.2)
            line_height_ratio = getattr(text_cfg, 'line_height', 1.2)
            actual_line_height = int(text_cfg.font_size * line_height_ratio)
            
            for line in wrapped_text.split("\n"):
                maker.add_text(
                    line,
                    x=text_cfg.x,
                    y=y_offset,
                    font_id=font_id,
                    font_size=text_cfg.font_size,
                    color=text_cfg.color,
                    align=text_cfg.align,
                    max_width=text_cfg.max_width,
                    max_height=text_cfg.max_height,
                )
                y_offset += actual_line_height

        # 7. 엽서 저장
        postcard_image = maker.get_canvas()
        postcard_path = await self.storage.save_generated_postcard(postcard_image)

        # 8. DB에 메타데이터 저장
        postcard = Postcard(
            template_id=template_id,
            text_contents=texts,  # JSON으로 저장
            user_photo_paths=user_photo_paths,  # JSON으로 저장
            postcard_image_path=postcard_path,
            sender_name=sender_name,  # 발신자 이름
            user_id=user_id,  # 사용자 ID
            recipient_email=recipient_email or "unknown@example.com",  # 임시 기본값
            status="pending",  # 기본 상태
        )
        self.db.add(postcard)
        await self.db.commit()
        await self.db.refresh(postcard)

        # 9. 임시 파일 삭제 (리소스 누수 방지)
        for config_id, temp_path in user_photo_temp_paths.items():
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    logger.debug(f"Deleted temporary file for config_id={config_id}: {temp_path}")
            except Exception as e:
                # 삭제 실패를 로깅 (디버깅 및 모니터링용)
                logger.warning(f"Failed to delete temporary file {temp_path}: {str(e)}")

        # 10. 응답 반환
        return PostcardResponse(
            id=postcard.id,
            postcard_path=postcard_path,
            template_id=template_id,
            text=str(texts),  # Dict를 문자열로 변환 (임시)
            recipient_email=postcard.recipient_email,
            recipient_name=postcard.recipient_name,
            sender_name=sender_name,
            status=postcard.status,
            scheduled_at=postcard.scheduled_at,
            sent_at=postcard.sent_at,
            error_message=postcard.error_message,
            created_at=postcard.created_at,
            updated_at=postcard.updated_at,
        )

    async def list_postcards(
        self,
        user_id: str,
        status_filter: Optional[str] = None
    ) -> List[PostcardResponse]:
        """
        사용자의 엽서 목록 조회
        
        Args:
            user_id: 사용자 ID
            status_filter: 상태 필터 (writing, pending, sent, failed, cancelled)
            
        Returns:
            엽서 목록
        """
        stmt = select(Postcard).where(Postcard.user_id == user_id)
        
        if status_filter:
            valid_statuses = ["writing", "pending", "sent", "failed", "cancelled"]
            if status_filter not in valid_statuses:
                raise ValueError(f"status는 {', '.join(valid_statuses)} 중 하나여야 합니다.")
            stmt = stmt.where(Postcard.status == status_filter)
        
        stmt = stmt.order_by(Postcard.created_at.desc())
        
        result = await self.db.execute(stmt)
        postcards = result.scalars().all()
        
        responses = []
        for postcard in postcards:
            responses.append(PostcardResponse(
                id=postcard.id,
                template_id=postcard.template_id,
                text=extract_main_text(postcard.text_contents),
                original_text=extract_main_text(postcard.original_text_contents),
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

    async def get_postcard_by_id(
        self,
        postcard_id: str,
        user_id: str
    ) -> Optional[PostcardResponse]:
        """
        엽서 상세 조회 (권한 체크 포함)
        
        Args:
            postcard_id: 엽서 ID
            user_id: 사용자 ID (권한 체크용)
            
        Returns:
            엽서 정보 또는 None (없거나 권한 없음)
        """
        stmt = select(Postcard).where(
            and_(
                Postcard.id == postcard_id,
                Postcard.user_id == user_id
            )
        )
        result = await self.db.execute(stmt)
        postcard = result.scalar_one_or_none()
        
        if not postcard:
            return None
        
        return PostcardResponse(
            id=postcard.id,
            template_id=postcard.template_id,
            text=extract_main_text(postcard.text_contents),
            original_text=extract_main_text(postcard.original_text_contents),
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

    async def update_postcard(
        self,
        postcard_id: str,
        user_id: str,
        text: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
        recipient_email: Optional[str] = None,
        recipient_name: Optional[str] = None,
        sender_name: Optional[str] = None,
        scheduled_at: Optional[str] = None
    ) -> PostcardResponse:
        """
        엽서 수정 (writing 또는 pending 상태만 가능)
        
        Args:
            postcard_id: 엽서 ID
            user_id: 사용자 ID (권한 체크용)
            text: 새로운 텍스트
            image_bytes: 새로운 이미지 바이트
            recipient_email: 수신자 이메일
            recipient_name: 수신자 이름
            sender_name: 발신자 이름
            scheduled_at: 발송 예정 시간 (ISO 8601 형식)
            
        Returns:
            수정된 엽서 정보
            
        Raises:
            ValueError: 엽서를 찾을 수 없거나 수정 불가능한 상태인 경우
        """
        from datetime import datetime
        from app.models.postcard import PostcardUpdateRequest
        
        # 엽서 조회 및 권한 체크
        stmt = select(Postcard).where(
            and_(
                Postcard.id == postcard_id,
                Postcard.user_id == user_id
            )
        )
        result = await self.db.execute(stmt)
        postcard = result.scalar_one_or_none()
        
        if not postcard:
            raise ValueError("엽서를 찾을 수 없습니다.")

        if postcard.status not in ["writing", "pending"]:
            raise ValueError(f"writing 또는 pending 상태의 엽서만 수정 가능합니다. (현재 상태: {postcard.status})")
        
        # 업데이트할 필드
        from sqlalchemy import update as sql_update
        update_values = {"updated_at": datetime.utcnow()}
        
        # 이미지 업로드 처리
        if image_bytes:
            template = template_service.get_template_by_id(postcard.template_id)
            if template:
                target_photo_id = PostcardService._map_simple_photo(template)
                logger.info(f"Target photo_id for user image: {target_photo_id}")
                if target_photo_id:
                    saved_path = await self.storage.save_user_photo(image_bytes, "jpg")
                    user_photo_paths = postcard.user_photo_paths or {}
                    user_photo_paths[target_photo_id] = saved_path
                    update_values["user_photo_paths"] = user_photo_paths
                    logger.info(f"Updated user photo: photo_id={target_photo_id}, saved_path={saved_path}")
        
        # 예약 시간 처리
        if scheduled_at:
            try:
                new_scheduled_at = datetime.fromisoformat(scheduled_at.replace('Z', '+00:00'))
                # UTC로 변환 (timezone-naive면 UTC로 가정)
                if new_scheduled_at.tzinfo is None:
                    new_scheduled_at = pytz.UTC.localize(new_scheduled_at)
                else:
                    new_scheduled_at = new_scheduled_at.astimezone(pytz.UTC)
                # 검증
                update_data = PostcardUpdateRequest(scheduled_at=new_scheduled_at)
                update_values["scheduled_at"] = update_data.scheduled_at
            except ValueError:
                raise ValueError("scheduled_at은 ISO 8601 형식이어야 합니다")
        
        # 텍스트 수정 시 번역 수행
        if text:
            template = template_service.get_template_by_id(postcard.template_id)
            if template:
                # 원본 텍스트 매핑
                original_texts = PostcardService._map_simple_text(template, text)
                if sender_name or postcard.sender_name:
                    sender_config = next(
                        (cfg for cfg in template.text_configs if cfg.id in ["sender"]),
                        None
                    )
                    if sender_config:
                        original_texts[sender_config.id] = sender_name or postcard.sender_name

                # 제주어 번역
                texts = await PostcardService._translate_user_text_to_jeju(template, original_texts)
                if sender_name or postcard.sender_name:
                    sender_config = next(
                        (cfg for cfg in template.text_configs if cfg.id in ["sender"]),
                        None
                    )
                    if sender_config:
                        texts[sender_config.id] = sender_name or postcard.sender_name

                update_values["text_contents"] = texts
                update_values["original_text_contents"] = original_texts
        
        # 수신자 정보 업데이트
        if recipient_email:
            update_values["recipient_email"] = recipient_email
        if recipient_name is not None:
            update_values["recipient_name"] = recipient_name
        if sender_name is not None:
            update_values["sender_name"] = sender_name
        
        # 엽서 이미지 생성 (텍스트 또는 이미지 변경 시)
        if text or image_bytes:
            template = template_service.get_template_by_id(postcard.template_id)
            if template:
                # 최신 텍스트 사용
                texts = update_values.get("text_contents") or postcard.text_contents

                if texts:
                    # 최신 사진 경로 사용
                    user_photo_paths = update_values.get("user_photo_paths") or postcard.user_photo_paths

                    photos = {}
                    if user_photo_paths:
                        for photo_id, photo_path in user_photo_paths.items():
                            photo_bytes = await self.storage.read_file(photo_path)
                            if photo_bytes:
                                photos[photo_id] = photo_bytes

                    # 엽서 이미지 생성 (임시 레코드)
                    postcard_result = await self.create_postcard(
                        template_id=postcard.template_id,
                        texts=texts,
                        photos=photos if photos else None,
                        sender_name=update_values.get("sender_name") or postcard.sender_name,
                        user_id=user_id,
                        recipient_email=update_values.get("recipient_email") or postcard.recipient_email,
                    )

                    # 생성된 이미지 경로 저장
                    update_values["postcard_image_path"] = postcard_result.postcard_path

                    # 임시 레코드 삭제
                    temp_postcard = await self.db.get(Postcard, postcard_result.id)
                    if temp_postcard:
                        await self.db.delete(temp_postcard)
        
        # DB 업데이트
        stmt = (
            sql_update(Postcard)
            .where(Postcard.id == postcard_id)
            .values(**update_values)
        )
        await self.db.execute(stmt)
        await self.db.commit()
        
        # 스케줄러 업데이트 (예약 시간 변경 시)
        if scheduled_at and postcard.scheduled_at:
            from app.scheduler_instance import get_scheduler
            scheduler = get_scheduler()
            scheduler.reschedule_postcard(
                postcard_id,
                update_values["scheduled_at"]
            )
        
        # 업데이트된 데이터 조회
        await self.db.refresh(postcard)

        return PostcardResponse(
            id=postcard.id,
            template_id=postcard.template_id,
            text=extract_main_text(postcard.text_contents),
            original_text=extract_main_text(postcard.original_text_contents),
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

    async def cancel_postcard(self, postcard_id: str, user_id: str) -> None:
        """
        엽서 취소 (writing 또는 pending 상태만 가능)
        
        Args:
            postcard_id: 엽서 ID
            user_id: 사용자 ID (권한 체크용)
            
        Raises:
            ValueError: 엽서를 찾을 수 없거나 취소 불가능한 상태인 경우
        """
        from datetime import datetime
        from sqlalchemy import update as sql_update
        
        # 엽서 조회 및 권한 체크
        stmt = select(Postcard).where(
            and_(
                Postcard.id == postcard_id,
                Postcard.user_id == user_id
            )
        )
        result = await self.db.execute(stmt)
        postcard = result.scalar_one_or_none()
        
        if not postcard:
            raise ValueError("엽서를 찾을 수 없습니다.")

        if postcard.status not in ["writing", "pending"]:
            raise ValueError(f"writing 또는 pending 상태의 엽서만 취소/삭제 가능합니다. (현재 상태: {postcard.status})")
        
        # 스케줄러에서 제거 (예약된 경우)
        if postcard.scheduled_at:
            from app.scheduler_instance import get_scheduler
            scheduler = get_scheduler()
            scheduler.cancel_schedule(postcard_id)
        
        # DB 상태 업데이트
        stmt = (
            sql_update(Postcard)
            .where(Postcard.id == postcard_id)
            .values(status="cancelled", updated_at=datetime.utcnow())
        )
        await self.db.execute(stmt)
        await self.db.commit()
        
        logger.info(f"Cancelled postcard {postcard_id}")

    async def send_postcard(self, postcard_id: str, user_id: str) -> PostcardResponse:
        """
        엽서 발송 (즉시 또는 예약)
        
        Args:
            postcard_id: 엽서 ID
            user_id: 사용자 ID (권한 체크용)
            
        Returns:
            발송/예약된 엽서 정보
            
        Raises:
            ValueError: 엽서를 찾을 수 없거나 발송 불가능한 경우
        """
        from datetime import datetime
        from sqlalchemy import update as sql_update
        from app.services.email_service import EmailService
        from app.scheduler_instance import get_scheduler
        
        # 엽서 조회 및 권한 체크
        stmt = select(Postcard).where(
            and_(
                Postcard.id == postcard_id,
                Postcard.user_id == user_id
            )
        )
        result = await self.db.execute(stmt)
        postcard = result.scalar_one_or_none()

        if not postcard:
            raise ValueError("엽서를 찾을 수 없습니다.")

        if postcard.status not in ["writing", "pending"]:
            raise ValueError(f"writing 또는 pending 상태의 엽서만 발송 가능합니다. (현재 상태: {postcard.status})")

        if not postcard.postcard_image_path:
            raise ValueError("엽서 이미지가 생성되지 않았습니다. 먼저 엽서를 수정하여 이미지를 생성하세요.")

        if not postcard.recipient_email:
            raise ValueError("수신자 이메일이 설정되지 않았습니다.")

        # 즉시 발송 (scheduled_at이 없는 경우)
        if not postcard.scheduled_at:
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
                    sql_update(Postcard)
                    .where(Postcard.id == postcard_id)
                    .values(status="sent", sent_at=datetime.utcnow())
                )
                await self.db.execute(stmt)
                await self.db.commit()
                await self.db.refresh(postcard)

                logger.info(f"Postcard {postcard_id} sent immediately to {postcard.recipient_email}")

            except Exception as e:
                # 이메일 발송 실패
                stmt = (
                    sql_update(Postcard)
                    .where(Postcard.id == postcard_id)
                    .values(status="failed", error_message=str(e))
                )
                await self.db.execute(stmt)
                await self.db.commit()
                await self.db.refresh(postcard)

                logger.error(f"Failed to send postcard {postcard_id}: {str(e)}")
                raise ValueError(f"엽서는 생성되었으나 이메일 발송에 실패했습니다: {str(e)}")

        # 예약 발송 (scheduled_at이 설정된 경우)
        else:
            # pending 상태로 변경
            stmt = (
                sql_update(Postcard)
                .where(Postcard.id == postcard_id)
                .values(status="pending", updated_at=datetime.utcnow())
            )
            await self.db.execute(stmt)
            await self.db.commit()
            await self.db.refresh(postcard)

            # 스케줄러에 등록 (UTC timezone-aware 확인)
            scheduler = get_scheduler()
            scheduled_time = postcard.scheduled_at
            if scheduled_time.tzinfo is None:
                scheduled_time = pytz.UTC.localize(scheduled_time)
            success = scheduler.schedule_postcard(postcard_id, scheduled_time)

            if not success:
                # 스케줄러 등록 실패 시 상태를 다시 writing으로 되돌림
                stmt = (
                    sql_update(Postcard)
                    .where(Postcard.id == postcard_id)
                    .values(status="writing")
                )
                await self.db.execute(stmt)
                await self.db.commit()
                raise ValueError("스케줄러 등록에 실패했습니다.")

            logger.info(f"Scheduled postcard {postcard_id} for {postcard.scheduled_at}")

        return PostcardResponse(
            id=postcard.id,
            template_id=postcard.template_id,
            text=extract_main_text(postcard.text_contents),
            original_text=extract_main_text(postcard.original_text_contents),
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

    async def create_empty_postcard(self, user_id: str) -> PostcardResponse:
        """
        빈 엽서 생성 (writing 상태)
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            생성된 엽서 정보
            
        Raises:
            ValueError: 사용 가능한 템플릿이 없는 경우
        """
        # 사용 가능한 템플릿 중 첫 번째 자동 선택
        available_templates = template_service.get_all_templates()
        if not available_templates:
            raise ValueError("사용 가능한 템플릿이 없습니다.")
        
        template_id = available_templates[0].id
        logger.info(f"Auto-selected template: {template_id}")

        # 빈 엽서 레코드 생성
        postcard = Postcard(
            user_id=user_id,
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

        self.db.add(postcard)
        await self.db.commit()
        await self.db.refresh(postcard)

        logger.info(f"Created empty postcard {postcard.id} in writing state")

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
