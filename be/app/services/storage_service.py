"""
로컬 파일 시스템 스토리지 서비스

파일 저장, 경로 생성 등의 Storage 관련 기능을 제공합니다.
"""

import os
import uuid
from datetime import datetime
from PIL import Image
from app.utils.encryption import get_file_encryptor


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

        # 암호화 유틸 초기화
        self.file_encryptor = get_file_encryptor()

        # 디렉토리 생성
        for dir_path in [self.uploads_dir, self.templates_dir, self.generated_dir]:
            os.makedirs(dir_path, exist_ok=True)

    async def save_user_photo(self, file_bytes: bytes, file_extension: str) -> str:
        """
        사용자 업로드 사진을 암호화하여 로컬에 저장합니다.

        Args:
            file_bytes: 파일 바이너리 데이터
            file_extension: 파일 확장자 (예: 'jpg', 'png')

        Returns:
            str: 저장된 파일 경로

        Example:
            path = await storage.save_user_photo(photo_bytes, "jpg")
            # 'static/uploads/2025/12/08/{uuid}.jpg'
        """
        # 1. 파일 암호화
        encrypted_bytes = self.file_encryptor.encrypt_file(file_bytes)

        # 2. 파일 저장 경로 생성
        date_path = datetime.now().strftime("%Y/%m/%d")
        dir_path = f"{self.uploads_dir}/{date_path}"
        os.makedirs(dir_path, exist_ok=True)

        file_id = str(uuid.uuid4())
        file_path = f"{dir_path}/{file_id}.{file_extension}"

        # 3. 암호화된 바이트 저장
        with open(file_path, "wb") as f:
            f.write(encrypted_bytes)

        return file_path

    async def save_generated_postcard(self, image: Image.Image) -> str:
        """
        생성된 엽서를 암호화하여 PNG로 로컬에 저장합니다.

        Args:
            image: PIL Image 객체

        Returns:
            str: 저장된 파일 경로

        Example:
            path = await storage.save_generated_postcard(postcard_image)
            # 'static/generated/2025/12/08/{uuid}.png'
        """
        # 1. PIL Image를 바이트로 변환
        import io
        buffer = io.BytesIO()
        image.save(buffer, format='PNG', quality=95)
        image_bytes = buffer.getvalue()

        # 2. 이미지 바이트 암호화
        encrypted_bytes = self.file_encryptor.encrypt_file(image_bytes)

        # 3. 파일 저장 경로 생성
        date_path = datetime.now().strftime("%Y/%m/%d")
        dir_path = f"{self.generated_dir}/{date_path}"
        os.makedirs(dir_path, exist_ok=True)

        file_id = str(uuid.uuid4())
        file_path = f"{dir_path}/{file_id}.png"

        # 4. 암호화된 바이트 저장
        with open(file_path, "wb") as f:
            f.write(encrypted_bytes)

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
        uploads 디렉토리의 파일은 자동으로 복호화됩니다.

        Args:
            file_path: 읽을 파일 경로

        Returns:
            bytes: 파일 내용 (uploads는 복호화된 원본)

        Example:
            content = await storage.read_file("static/uploads/2025/12/08/uuid.jpg")
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

        with open(file_path, "rb") as f:
            file_bytes = f.read()

        # uploads, generated 디렉토리는 암호화되어 있으므로 복호화
        if "uploads/" in file_path or "generated/" in file_path:
            try:
                file_bytes = self.file_encryptor.decrypt_file(file_bytes)
            except Exception as e:
                raise ValueError(f"파일 복호화 실패: {e}")

        return file_bytes
