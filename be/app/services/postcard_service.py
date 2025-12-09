"""
엽서 생성 서비스

템플릿, 사진, 텍스트를 조합하여 엽서를 생성하고 로컬에 저장하는 핵심 비즈니스 로직을 제공합니다.
"""

import os
import uuid as uuid_lib
from typing import Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Postcard
from app.services.storage_service import LocalStorageService
from app.services import template_service, font_service
from app.services.postcards.postcard_maker import PostcardMaker
from app.services.postcards.text_wrapper import TextWrapper
from app.models.postcard import PostcardResponse
from app.config import settings


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
            for config_id, photo_bytes in photos.items():
                # 영구 저장
                saved_path = await self.storage.save_user_photo(photo_bytes, "jpg")
                user_photo_paths[config_id] = saved_path

                # 임시 파일 (PostcardMaker 사용)
                temp_path = f"/tmp/{uuid_lib.uuid4()}.jpg"
                with open(temp_path, "wb") as f:
                    f.write(photo_bytes)
                user_photo_temp_paths[config_id] = temp_path

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
                wrapper = TextWrapper(
                    font=font,
                    max_width=text_cfg.max_width,
                    max_height=text_cfg.max_height,
                    line_spacing=text_cfg.line_spacing
                )
                wrapped_text = wrapper.wrap(text_content)
            else:
                wrapped_text = text_content

            # 각 줄 그리기
            y_offset = text_cfg.y
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
                y_offset += text_cfg.font_size + text_cfg.line_spacing

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
        )
        self.db.add(postcard)
        await self.db.commit()
        await self.db.refresh(postcard)

        # 9. 임시 파일 삭제
        for temp_path in user_photo_temp_paths.values():
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception:
                pass

        # 10. 응답 반환
        return PostcardResponse(
            postcard_id=postcard.id,
            postcard_path=postcard_path,
            template_id=template_id,
            text=str(texts),  # Dict를 문자열로 변환 (임시)
            sender_name=sender_name,
            created_at=postcard.created_at,
        )
