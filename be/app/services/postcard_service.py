"""
편지 생성 서비스

템플릿, 사진, 텍스트를 조합하여 편지를 생성하고 로컬에 저장하는 핵심 비즈니스 로직을 제공합니다.
"""

import os
import uuid as uuid_lib
import logging
from typing import Optional, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from app.utils.timezone import from_isoformat, ensure_utc

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
    """편지 생성 및 관리 서비스"""

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

            # 수신자 이름은 번역하지 않음
            if config_id == "recipient":
                translated_texts[config_id] = original_text
                continue

            # 사용자 입력 본문만 번역
            try:
                translated_text = await translate_to_jeju_async(original_text)
                translated_texts[config_id] = translated_text
            except Exception as e:
                logger.error(f"번역 실패 (원본 사용): {str(e)}")
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
        다중 텍스트/이미지를 지원하는 편지 생성
        """
        # 1. 템플릿 조회 (메모리에서)
        template = template_service.get_template_by_id(template_id)
        if not template:
            raise ValueError("템플릿을 찾을 수 없습니다.")

        # 2. 이미지 저장 (여러 개)
        user_photo_paths = {}
        user_photo_temp_paths = {}

        if photos:
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
                except Exception as e:
                    # 파일 생성 실패 시 즉시 삭제 시도
                    os.close(temp_fd)
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    raise

        # 3. PostcardMaker 초기화
        template_path = self.storage.get_template_image_path(
            template.template_image_path
        )
        maker = PostcardMaker(
            width=template.width, height=template.height
        )
        maker.add_background_image(template_path, opacity=1.0)

        # 5. 이미지 영역 추가 (반복문)
        for photo_cfg in template.photo_configs:
            config_id = photo_cfg.id
            if config_id in user_photo_temp_paths:
                maker.add_photo(
                    user_photo_temp_paths[config_id],
                    x=photo_cfg.x,
                    y=photo_cfg.y,
                    max_width=photo_cfg.max_width,
                    max_height=photo_cfg.max_height,
                    effects=photo_cfg.effects,  # 템플릿에 정의된 효과 적용
                )

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

        # 7. 편지 저장
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
        # 사용자 업로드 사진 경로를 URL로 변환 (첫 번째 사진만)
        user_photo_url = None
        if postcard.user_photo_paths:
            first_photo_path = next(iter(postcard.user_photo_paths.values()), None)
            if first_photo_path:
                user_photo_url = convert_static_path_to_url(first_photo_path)

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
            user_photo_url=user_photo_url,
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
        사용자의 편지 목록 조회
        
        Args:
            user_id: 사용자 ID
            status_filter: 상태 필터 (writing, pending, sent, failed)

        Returns:
            편지 목록
        """
        stmt = select(Postcard).where(Postcard.user_id == user_id)

        if status_filter:
            valid_statuses = ["writing", "pending", "processing", "sent", "failed"]
            if status_filter not in valid_statuses:
                raise ValueError(f"status는 {', '.join(valid_statuses)} 중 하나여야 합니다.")
            stmt = stmt.where(Postcard.status == status_filter)
        
        stmt = stmt.order_by(Postcard.created_at.desc())
        
        result = await self.db.execute(stmt)
        postcards = result.scalars().all()
        
        responses = []
        for postcard in postcards:
            # 사용자 업로드 사진 경로를 URL로 변환 (첫 번째 사진만)
            user_photo_url = None
            if postcard.user_photo_paths:
                first_photo_path = next(iter(postcard.user_photo_paths.values()), None)
                if first_photo_path:
                    user_photo_url = convert_static_path_to_url(first_photo_path)

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
                user_photo_url=user_photo_url,
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
        편지 상세 조회 (권한 체크 포함)
        
        Args:
            postcard_id: 편지 ID
            user_id: 사용자 ID (권한 체크용)
            
        Returns:
            편지 정보 또는 None (없거나 권한 없음)
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

        # 사용자 업로드 사진 경로를 URL로 변환 (첫 번째 사진만)
        user_photo_url = None
        if postcard.user_photo_paths:
            first_photo_path = next(iter(postcard.user_photo_paths.values()), None)
            if first_photo_path:
                user_photo_url = convert_static_path_to_url(first_photo_path)

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
            user_photo_url=user_photo_url,
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
        template_id: Optional[str] = None,
        scheduled_at: Optional[str] = None,
        background_tasks = None
    ) -> PostcardResponse:
        """
        편지 수정 (writing 또는 pending 상태만 가능)

        Args:
            postcard_id: 편지 ID
            user_id: 사용자 ID (권한 체크용)
            text: 새로운 텍스트
            image_bytes: 새로운 이미지 바이트
            recipient_email: 수신자 이메일
            recipient_name: 수신자 이름
            sender_name: 발신자 이름
            template_id: 새로운 템플릿 ID
            scheduled_at: 발송 예정 시간 (ISO 8601 형식)

        Returns:
            수정된 편지 정보

        Raises:
            ValueError: 편지를 찾을 수 없거나 수정 불가능한 상태인 경우
        """
        from datetime import datetime
        from app.models.postcard import PostcardUpdateRequest
        
        # 편지 조회 및 권한 체크
        stmt = select(Postcard).where(
            and_(
                Postcard.id == postcard_id,
                Postcard.user_id == user_id
            )
        )
        result = await self.db.execute(stmt)
        postcard = result.scalar_one_or_none()
        
        if not postcard:
            raise ValueError("편지를 찾을 수 없습니다.")

        if postcard.status not in ["writing", "pending"]:
            raise ValueError(f"writing 또는 pending 상태의 편지만 수정 가능합니다. (현재 상태: {postcard.status})")
        
        # 업데이트할 필드
        from sqlalchemy import update as sql_update
        update_values = {"updated_at": datetime.utcnow()}

        # 템플릿 변경 처리
        if template_id:
            # 템플릿 존재 여부 확인
            new_template = template_service.get_template_by_id(template_id)
            if not new_template:
                raise ValueError(f"템플릿 ID '{template_id}'를 찾을 수 없습니다.")

            update_values["template_id"] = template_id
            logger.info(f"Template changed from {postcard.template_id} to {template_id}")

            # 템플릿 변경 시 기존 데이터 초기화 (선택 사항)
            # 사용자가 새 템플릿에 맞춰 다시 입력해야 함
            if postcard.template_id != template_id:
                # 기존 텍스트와 이미지 경로는 유지하되, 새 템플릿에 맞춰 재생성 필요
                # postcard_image_path는 재생성 시 자동으로 업데이트됨
                logger.info(f"Template changed - postcard image will be regenerated")

        # 이미지 업로드 처리
        if image_bytes:
            # 새 템플릿 ID가 있으면 사용, 없으면 기존 템플릿 사용
            current_template_id = template_id if template_id else postcard.template_id
            template = template_service.get_template_by_id(current_template_id)
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
        scheduled_at_changed = False
        old_scheduled_at = postcard.scheduled_at
        new_scheduled_at_value = None

        if scheduled_at is not None:  # None이 아니면 처리 (빈 문자열 포함)
            if scheduled_at == "":
                # 빈 문자열: 예약 해제 (즉시 발송으로 변경)
                update_values["scheduled_at"] = None
                scheduled_at_changed = True
                logger.info(f"예약 해제: {postcard_id}")
            else:
                # ISO 8601 문자열: 예약 시간 설정/변경
                try:
                    new_scheduled_at = from_isoformat(scheduled_at)
                    # 검증
                    update_data = PostcardUpdateRequest(scheduled_at=new_scheduled_at)
                    update_values["scheduled_at"] = update_data.scheduled_at
                    new_scheduled_at_value = update_data.scheduled_at
                    scheduled_at_changed = True
                    logger.info(f"예약 시간 설정: {postcard_id} -> {new_scheduled_at_value}")
                except ValueError as e:
                    raise ValueError(f"scheduled_at 처리 실패: {str(e)}")
        
        # 텍스트 수정 시 원본만 저장 (번역은 send 시점에 수행)
        if text:
            # 새 템플릿 ID가 있으면 사용, 없으면 기존 템플릿 사용
            current_template_id = template_id if template_id else postcard.template_id
            template = template_service.get_template_by_id(current_template_id)
            if template:
                # 원본 텍스트 매핑
                original_texts = PostcardService._map_simple_text(template, text)
                
                # sender 처리: "{sender}가" 형식
                if sender_name or postcard.sender_name:
                    sender_config = next(
                        (cfg for cfg in template.text_configs if cfg.id == "sender"),
                        None
                    )
                    if sender_config:
                        original_texts[sender_config.id] = f"{sender_name or postcard.sender_name}가"

                # recipient 처리: "{recipient}에게" 형식
                effective_recipient_name = recipient_name if recipient_name is not None else postcard.recipient_name
                if effective_recipient_name:
                    recipient_config = next(
                        (cfg for cfg in template.text_configs if cfg.id == "recipient"),
                        None
                    )
                    if recipient_config:
                        original_texts[recipient_config.id] = f"{effective_recipient_name}에게"

                # 원본 텍스트만 저장 (제주어 번역은 send 시점에 수행)
                update_values["original_text_contents"] = original_texts
                # text_contents는 null로 설정 (발송 시 번역됨)
                update_values["text_contents"] = None
                # postcard_image_path도 초기화 (텍스트 변경 시 이미지 재생성 필요)
                update_values["postcard_image_path"] = None
        
        # 수신자 정보 업데이트
        if recipient_email:
            update_values["recipient_email"] = recipient_email
        if recipient_name is not None:
            update_values["recipient_name"] = recipient_name
        if sender_name is not None:
            update_values["sender_name"] = sender_name

        # DB 업데이트
        stmt = (
            sql_update(Postcard)
            .where(Postcard.id == postcard_id)
            .values(**update_values)
        )
        await self.db.execute(stmt)
        await self.db.commit()

        # 스케줄러 동기화 (예약 시간 변경 시)
        if scheduled_at_changed:
            from app.scheduler_instance import get_scheduler
            scheduler = get_scheduler()

            if old_scheduled_at and new_scheduled_at_value is None:
                # 예약 해제: 스케줄러에서 제거
                scheduler.cancel_schedule(postcard_id)
                logger.info(f"스케줄러에서 제거: {postcard_id}")
            elif old_scheduled_at is None and new_scheduled_at_value:
                # 예약 추가: 스케줄러에 등록
                from app.utils.timezone_utils import ensure_utc
                scheduled_time = ensure_utc(new_scheduled_at_value)
                success = scheduler.schedule_postcard(postcard_id, scheduled_time)
                if not success:
                    logger.error(f"스케줄러 등록 실패: {postcard_id}")
                else:
                    logger.info(f"스케줄러에 등록: {postcard_id} at {scheduled_time}")
            elif old_scheduled_at and new_scheduled_at_value:
                # 예약 변경: 스케줄러 재스케줄
                scheduler.reschedule_postcard(postcard_id, new_scheduled_at_value)
                logger.info(f"스케줄러 재스케줄: {postcard_id} -> {new_scheduled_at_value}")
        
        # 업데이트된 데이터 조회
        await self.db.refresh(postcard)

        # 사용자 업로드 사진 경로를 URL로 변환 (첫 번째 사진만)
        user_photo_url = None
        if postcard.user_photo_paths:
            first_photo_path = next(iter(postcard.user_photo_paths.values()), None)
            if first_photo_path:
                user_photo_url = convert_static_path_to_url(first_photo_path)

        # 제주 스타일 이미지 경로를 URL로 변환 (첫 번째 사진만)
        jeju_photo_url = None
        if postcard.jeju_photo_paths:
            first_jeju_path = next(iter(postcard.jeju_photo_paths.values()), None)
            if first_jeju_path:
                jeju_photo_url = convert_static_path_to_url(first_jeju_path)

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
            user_photo_url=user_photo_url,
            jeju_photo_url=jeju_photo_url,
            error_message=postcard.error_message,
            created_at=postcard.created_at,
            updated_at=postcard.updated_at
        )

    async def delete_postcard(self, postcard_id: str, user_id: str) -> None:
        """
        편지 삭제 (DB에서 완전히 제거)

        관련된 모든 리소스를 삭제합니다:
        - 스케줄러에서 제거 (예약된 경우)
        - 사용자 업로드 사진 파일 삭제
        - 생성된 편지 이미지 파일 삭제
        - DB 레코드 삭제

        Args:
            postcard_id: 편지 ID
            user_id: 사용자 ID (권한 체크용)

        Raises:
            ValueError: 편지를 찾을 수 없는 경우
        """
        from sqlalchemy import delete as sql_delete

        # 편지 조회 및 권한 체크
        stmt = select(Postcard).where(
            and_(
                Postcard.id == postcard_id,
                Postcard.user_id == user_id
            )
        )
        result = await self.db.execute(stmt)
        postcard = result.scalar_one_or_none()

        if not postcard:
            raise ValueError("편지를 찾을 수 없습니다.")

        # 1. 스케줄러에서 제거 (예약된 경우)
        if postcard.scheduled_at and postcard.status == "pending":
            from app.scheduler_instance import get_scheduler
            scheduler = get_scheduler()
            scheduler.cancel_schedule(postcard_id)
            logger.info(f"Removed postcard {postcard_id} from scheduler")

        # 2. 사용자 업로드 사진 삭제
        if postcard.user_photo_paths:
            for photo_id, photo_path in postcard.user_photo_paths.items():
                deleted = await self.storage.delete_file(photo_path)
                if deleted:
                    logger.info(f"Deleted user photo: {photo_path}")
                else:
                    logger.warning(f"Failed to delete user photo or file not found: {photo_path}")

        # 3. 생성된 편지 이미지 삭제
        if postcard.postcard_image_path:
            deleted = await self.storage.delete_file(postcard.postcard_image_path)
            if deleted:
                logger.info(f"Deleted postcard image: {postcard.postcard_image_path}")
            else:
                logger.warning(f"Failed to delete postcard image or file not found: {postcard.postcard_image_path}")

        # 4. DB에서 완전히 삭제
        stmt = (
            sql_delete(Postcard)
            .where(Postcard.id == postcard_id)
        )
        await self.db.execute(stmt)
        await self.db.commit()

        logger.info(f"Deleted postcard {postcard_id} from database")

    async def cancel_postcard(self, postcard_id: str, user_id: str) -> None:
        """
        예약된 편지 취소 (pending 상태만 가능)

        예약을 취소하면 상태가 writing으로 되돌아가며,
        사용자가 다시 수정하고 재발송할 수 있습니다.

        Args:
            postcard_id: 편지 ID
            user_id: 사용자 ID (권한 체크용)

        Raises:
            ValueError: 편지를 찾을 수 없거나 취소 불가능한 상태인 경우
        """
        from datetime import datetime
        from sqlalchemy import update as sql_update

        # 편지 조회 및 권한 체크
        stmt = select(Postcard).where(
            and_(
                Postcard.id == postcard_id,
                Postcard.user_id == user_id
            )
        )
        result = await self.db.execute(stmt)
        postcard = result.scalar_one_or_none()

        if not postcard:
            raise ValueError("편지를 찾을 수 없습니다.")

        if postcard.status != "pending":
            raise ValueError(f"pending 상태의 예약된 편지만 취소 가능합니다. (현재 상태: {postcard.status})")

        # 스케줄러에서 제거
        if postcard.scheduled_at:
            from app.scheduler_instance import get_scheduler
            scheduler = get_scheduler()
            scheduler.cancel_schedule(postcard_id)

        # DB 상태 업데이트 (writing으로 되돌림)
        stmt = (
            sql_update(Postcard)
            .where(Postcard.id == postcard_id)
            .values(
                status="writing",
                scheduled_at=None,  # 예약 시간도 제거
                updated_at=datetime.utcnow()
            )
        )
        await self.db.execute(stmt)
        await self.db.commit()

        logger.info(f"Cancelled scheduled postcard {postcard_id}, reverted to writing state")

    async def _send_postcard_background(self, postcard_id: str, user_id: str):
        """
        편지 발송 백그라운드 작업

        각 단계마다 Redis로 진행 상태를 발행합니다:
        - translating: 제주어 번역 중
        - converting: 이미지 변환 중
        - generating: 편지 생성 중
        - sending: 이메일 발송 중
        - completed: 완료
        - failed: 실패

        재발송 최적화:
        - postcard_image_path가 이미 있으면 이메일만 재전송 (번역/변환/생성 스킵)
        """
        from datetime import datetime
        from sqlalchemy import update as sql_update
        from app.services.email_service import EmailService
        from app.services.redis_service import redis_service
        from app.services.postcard_event_service import PostcardEventService
        import json

        try:
            # 편지 조회
            stmt = select(Postcard).where(Postcard.id == postcard_id)
            result = await self.db.execute(stmt)
            postcard = result.scalar_one_or_none()

            if not postcard:
                await redis_service.publish(
                    f"postcard:{postcard_id}",
                    json.dumps({"status": "failed", "error": "편지를 찾을 수 없습니다."})
                )
                return

            # 이미 편지 이미지가 생성되어 있으면 이메일만 재전송 (재발송 최적화)
            if postcard.postcard_image_path:
                logger.info(f"🔄 [재발송] 이미 생성된 편지 이미지 발견, 이메일만 재전송: {postcard_id}")
                
                await PostcardEventService.publish_and_save(
                    self.db,
                    postcard_id,
                    "sending"
                )
                logger.info(f"📧 [재발송] 이메일 발송 시작: {postcard_id}")

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

                logger.info(f"✅ [재발송] 이메일 발송 완료: {postcard_id}")

                await PostcardEventService.publish_and_save(
                    self.db,
                    postcard_id,
                    "completed"
                )
                return

            # 템플릿 조회
            template = template_service.get_template_by_id(postcard.template_id)
            if not template:
                await redis_service.publish(
                    f"postcard:{postcard_id}",
                    json.dumps({"status": "failed", "error": "템플릿을 찾을 수 없습니다."})
                )
                return

            # 1. 제주어 번역
            await PostcardEventService.publish_and_save(
                self.db,
                postcard_id,
                "translating"
            )
            logger.info(f"📝 제주어 번역 시작: {postcard_id}")

            translated_texts = await PostcardService._translate_user_text_to_jeju(
                template,
                postcard.original_text_contents
            )

            stmt = (
                sql_update(Postcard)
                .where(Postcard.id == postcard_id)
                .values(text_contents=translated_texts)
            )
            await self.db.execute(stmt)
            await self.db.commit()
            await self.db.refresh(postcard)
            logger.info(f"✅ 제주어 번역 완료: {postcard_id}")

            # 2. 제주 스타일 이미지 변환
            if postcard.user_photo_paths and not postcard.jeju_photo_paths:
                await PostcardEventService.publish_and_save(
                    self.db,
                    postcard_id,
                    "converting"
                )
                logger.info(f"🎨 제주 스타일 이미지 변환 시작: {postcard_id}")

                try:
                    from app.services.jeju_image_service import JejuImageService

                    # 첫 번째 사용자 사진에 대해 변환 수행
                    first_photo_id = next(iter(postcard.user_photo_paths.keys()))
                    first_photo_path = postcard.user_photo_paths[first_photo_id]
                    
                    # 원본 이미지 읽기
                    original_image_bytes = await self.storage.read_file(first_photo_path)
                    if not original_image_bytes:
                        raise ValueError("원본 이미지를 읽을 수 없습니다.")

                    # AI 전송용 이미지 압축 (적극적 압축: 512px, 품질 75%)
                    logger.info(f"📦 원본 이미지 크기: {len(original_image_bytes)} bytes")
                    compressed_image_bytes = self.storage.compress_image_for_ai(
                        image_bytes=original_image_bytes,
                        max_long_edge=512,
                        jpeg_quality=75
                    )
                    logger.info(f"📦 압축 후 크기: {len(compressed_image_bytes)} bytes (압축률: {len(compressed_image_bytes)/len(original_image_bytes)*100:.1f}%)")

                    # 템플릿의 photo_config에서 크기 정보 추출
                    photo_config = next(
                        (cfg for cfg in template.photo_configs if cfg.id == first_photo_id),
                        None
                    )

                    # OpenAI API 지원 크기 계산 (1024x1024, 1024x1536, 1536x1024, auto)
                    ai_size = "1024x1024"  # 기본값
                    if photo_config and photo_config.max_width and photo_config.max_height:
                        # 가로/세로 비율로 판단
                        if photo_config.max_width > photo_config.max_height:
                            # 가로형: 1536x1024
                            ai_size = "1536x1024"
                        elif photo_config.max_height > photo_config.max_width:
                            # 세로형: 1024x1536
                            ai_size = "1024x1536"
                        else:
                            # 정사각형: 1024x1024
                            ai_size = "1024x1024"

                    logger.info(f"🎨 AI 이미지 생성 크기: {ai_size} (템플릿: {photo_config.max_width if photo_config else 'N/A'}x{photo_config.max_height if photo_config else 'N/A'})")

                    # 제주 스타일 변환 (압축된 이미지 사용)
                    jeju_service = JejuImageService()
                    jeju_bytes = await jeju_service.generate_jeju_style_image(
                        image_bytes=compressed_image_bytes,
                        custom_prompt="",
                        size=ai_size  # 계산된 크기 전달
                    )

                    # 변환된 이미지 저장
                    jeju_path = await self.storage.save_jeju_photo(jeju_bytes, "jpg")
                    logger.info(f"💾 제주 스타일 이미지 저장 완료: {jeju_path}")

                    # DB 업데이트: jeju_photo_paths 저장
                    stmt = (
                        sql_update(Postcard)
                        .where(Postcard.id == postcard_id)
                        .values(jeju_photo_paths={first_photo_id: jeju_path})
                    )
                    await self.db.execute(stmt)
                    await self.db.commit()
                    await self.db.refresh(postcard)

                    logger.info(f"✅ 제주 스타일 이미지 변환 완료: {postcard_id}")

                except Exception as e:
                    # 변환 실패 시 원본 사용
                    logger.error(f"❌ 제주 스타일 변환 실패 (원본 사용): {postcard_id} - {str(e)}")
                    await self.db.refresh(postcard)

            # 3. 편지 이미지 생성
            await PostcardEventService.publish_and_save(
                self.db,
                postcard_id,
                "generating"
            )
            logger.info(f"🖼️ 편지 이미지 생성 시작: {postcard_id}")

            # 사진 준비 (제주 스타일 우선, 없으면 원본)
            photos = {}
            if postcard.jeju_photo_paths:
                for photo_id, photo_path in postcard.jeju_photo_paths.items():
                    photo_bytes = await self.storage.read_file(photo_path)
                    if photo_bytes:
                        photos[photo_id] = photo_bytes
            elif postcard.user_photo_paths:
                for photo_id, photo_path in postcard.user_photo_paths.items():
                    photo_bytes = await self.storage.read_file(photo_path)
                    if photo_bytes:
                        photos[photo_id] = photo_bytes

            postcard_result = await self.create_postcard(
                template_id=postcard.template_id,
                texts=postcard.text_contents,
                photos=photos if photos else None,
                sender_name=postcard.sender_name,
                user_id=user_id,
                recipient_email=postcard.recipient_email,
            )

            stmt = (
                sql_update(Postcard)
                .where(Postcard.id == postcard_id)
                .values(postcard_image_path=postcard_result.postcard_path)
            )
            await self.db.execute(stmt)
            await self.db.commit()
            await self.db.refresh(postcard)

            # 임시 레코드 삭제
            temp_postcard = await self.db.get(Postcard, postcard_result.id)
            if temp_postcard:
                await self.db.delete(temp_postcard)
                await self.db.commit()

            logger.info(f"✅ 편지 이미지 생성 완료: {postcard_id}")

            # 4. 이메일 발송
            await PostcardEventService.publish_and_save(
                self.db,
                postcard_id,
                "sending"
            )
            logger.info(f"📧 이메일 발송 시작: {postcard_id}")

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

            logger.info(f"✅ 이메일 발송 완료: {postcard_id}")

            # 5. 완료 이벤트 발행
            await PostcardEventService.publish_and_save(
                self.db,
                postcard_id,
                "completed"
            )

        except Exception as e:
            # 실패 처리
            logger.error(f"❌ 편지 발송 실패: {postcard_id} - {str(e)}")

            stmt = (
                sql_update(Postcard)
                .where(Postcard.id == postcard_id)
                .values(status="failed", error_message=str(e))
            )
            await self.db.execute(stmt)
            await self.db.commit()

            await PostcardEventService.publish_and_save(
                self.db,
                postcard_id,
                "failed",
                {"error": str(e)}
            )

    async def send_postcard(self, postcard_id: str, user_id: str, background_tasks=None) -> PostcardResponse:
        """
        편지 발송 (즉시 또는 예약)

        즉시 발송: 백그라운드에서 비동기 처리 (202 Accepted)
        예약 발송: 스케줄러에 등록

        Args:
            postcard_id: 편지 ID
            user_id: 사용자 ID (권한 체크용)
            background_tasks: FastAPI BackgroundTasks (즉시 발송 시 필요)

        Returns:
            발송/예약된 편지 정보

        Raises:
            ValueError: 편지를 찾을 수 없거나 발송 불가능한 경우
        """
        from datetime import datetime
        from sqlalchemy import update as sql_update
        from app.scheduler_instance import get_scheduler
        
        # 편지 조회 및 권한 체크
        stmt = select(Postcard).where(
            and_(
                Postcard.id == postcard_id,
                Postcard.user_id == user_id
            )
        )
        result = await self.db.execute(stmt)
        postcard = result.scalar_one_or_none()

        if not postcard:
            raise ValueError("편지를 찾을 수 없습니다.")

        if postcard.status not in ["writing", "pending"]:
            raise ValueError(f"writing 또는 pending 상태의 편지만 발송 가능합니다. (현재 상태: {postcard.status})")

        if not postcard.recipient_email:
            raise ValueError("수신자 이메일이 설정되지 않았습니다.")

        # 텍스트 필수 확인
        if not postcard.original_text_contents:
            raise ValueError("텍스트를 입력해야 편지를 발송할 수 있습니다.")

        # 즉시 발송 (scheduled_at이 없는 경우)
        if not postcard.scheduled_at:
            # 상태를 processing으로 변경, error_message 초기화 (재발송 시)
            stmt = (
                sql_update(Postcard)
                .where(Postcard.id == postcard_id)
                .values(status="processing", error_message=None, updated_at=datetime.utcnow())
            )
            await self.db.execute(stmt)
            await self.db.commit()
            await self.db.refresh(postcard)

            # 백그라운드 작업 시작 (Celery 워커 사용)
            from app.worker import celery_app
            celery_app.send_task(
                "process_postcard_send",
                args=[postcard_id, user_id]
            )
            logger.info(f"🚀 편지 발송 작업을 Celery 큐에 추가: {postcard_id}")

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
            scheduled_time = ensure_utc(postcard.scheduled_at)
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

        # 사용자 업로드 사진 경로를 URL로 변환 (첫 번째 사진만)
        user_photo_url = None
        if postcard.user_photo_paths:
            first_photo_path = next(iter(postcard.user_photo_paths.values()), None)
            if first_photo_path:
                user_photo_url = convert_static_path_to_url(first_photo_path)

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
            user_photo_url=user_photo_url,
            error_message=postcard.error_message,
            created_at=postcard.created_at,
            updated_at=postcard.updated_at
        )

    async def create_empty_postcard(self, user_id: str) -> PostcardResponse:
        """
        빈 편지 생성 (writing 상태)
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            생성된 편지 정보
            
        Raises:
            ValueError: 사용 가능한 템플릿이 없는 경우
        """
        # 사용 가능한 템플릿 중 첫 번째 자동 선택
        available_templates = template_service.get_all_templates()
        if not available_templates:
            raise ValueError("사용 가능한 템플릿이 없습니다.")
        
        template_id = available_templates[0].id
        logger.info(f"Auto-selected template: {template_id}")

        # 빈 편지 레코드 생성
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
            user_photo_url=None,
            jeju_photo_url=None,
            error_message=None,
            created_at=postcard.created_at,
            updated_at=postcard.updated_at
        )
