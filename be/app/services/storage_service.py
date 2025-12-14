"""
로컬 파일 시스템 스토리지 서비스

파일 저장, 경로 생성 등의 Storage 관련 기능을 제공합니다.
"""

import os
import uuid
from datetime import datetime
from PIL import Image


class LocalStorageService:
    """로컬 파일 시스템 스토리지"""

    def __init__(self):
        """
        LocalStorageService 초기화

        static 디렉토리 구조를 생성합니다.
        """
        self.base_dir = "static"
        self.uploads_dir = f"{self.base_dir}/uploads"
        self.templates_dir = f"{self.base_dir}/templates"
        self.generated_dir = f"{self.base_dir}/generated"

        # 디렉토리 생성
        for dir_path in [self.uploads_dir, self.templates_dir, self.generated_dir]:
            os.makedirs(dir_path, exist_ok=True)

    async def save_user_photo(self, file_bytes: bytes, file_extension: str) -> str:
        """
        사용자 업로드 사진을 로컬에 저장합니다.

        Args:
            file_bytes: 파일 바이너리 데이터
            file_extension: 파일 확장자 (예: 'jpg', 'png')

        Returns:
            str: 저장된 파일 경로

        Example:
            path = await storage.save_user_photo(photo_bytes, "jpg")
            # 'static/uploads/2025/12/08/{uuid}.jpg'
        """
        date_path = datetime.now().strftime("%Y/%m/%d")
        dir_path = f"{self.uploads_dir}/{date_path}"
        os.makedirs(dir_path, exist_ok=True)

        file_id = str(uuid.uuid4())
        file_path = f"{dir_path}/{file_id}.{file_extension}"

        with open(file_path, "wb") as f:
            f.write(file_bytes)

        return file_path

    async def save_generated_postcard(self, image: Image.Image) -> str:
        """
        생성된 엽서를 PNG로 로컬에 저장합니다.

        Args:
            image: PIL Image 객체

        Returns:
            str: 저장된 파일 경로

        Example:
            path = await storage.save_generated_postcard(postcard_image)
            # 'static/generated/2025/12/08/{uuid}.png'
        """
        date_path = datetime.now().strftime("%Y/%m/%d")
        dir_path = f"{self.generated_dir}/{date_path}"
        os.makedirs(dir_path, exist_ok=True)

        file_id = str(uuid.uuid4())
        file_path = f"{dir_path}/{file_id}.png"

        image.save(file_path, format='PNG', quality=95)

        return file_path

    def get_template_image_path(self, template_path: str) -> str:
        """
        템플릿 이미지 경로를 반환합니다.

        Args:
            template_path: 템플릿 이미지 경로

        Returns:
            str: 템플릿 이미지 경로

        Example:
            path = storage.get_template_image_path("static/templates/ocean.jpg")
            # 'static/templates/ocean.jpg'
        """
        return template_path

    async def read_file(self, file_path: str) -> bytes:
        """
        파일을 읽어서 바이트로 반환합니다.

        Args:
            file_path: 읽을 파일 경로

        Returns:
            bytes: 파일 내용

        Example:
            content = await storage.read_file("static/uploads/2025/12/08/uuid.jpg")
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

        with open(file_path, "rb") as f:
            return f.read()

    async def delete_file(self, file_path: str) -> bool:
        """
        파일을 삭제합니다.

        Args:
            file_path: 삭제할 파일 경로

        Returns:
            bool: 삭제 성공 여부

        Example:
            success = await storage.delete_file("static/uploads/2025/12/08/uuid.jpg")
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            # 삭제 실패를 로깅 (디버깅 및 모니터링용)
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to delete file {file_path}: {str(e)}")
            return False
