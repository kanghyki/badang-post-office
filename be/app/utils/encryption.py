"""
암호화 유틸리티

DB 필드 및 파일 암호화를 위한 Fernet (AES-128-CBC + HMAC) 기반 암호화
"""

from cryptography.fernet import Fernet
from sqlalchemy import TypeDecorator, Text
from typing import Optional
import json
import logging

logger = logging.getLogger(__name__)


class FieldEncryptor:
    """문자열 필드 암호화/복호화를 위한 Fernet 래퍼"""

    def __init__(self, key: bytes):
        """
        Args:
            key: Fernet 키 (Base64 인코딩된 32바이트)
        """
        self.fernet = Fernet(key)

    def encrypt(self, plain_text: str) -> str:
        """
        평문을 암호화하여 Base64 문자열로 반환

        Args:
            plain_text: 암호화할 평문 문자열

        Returns:
            암호화된 Base64 문자열
        """
        if not plain_text:
            return plain_text

        try:
            encrypted_bytes = self.fernet.encrypt(plain_text.encode('utf-8'))
            return encrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt(self, encrypted_text: str) -> str:
        """
        암호화된 Base64 문자열을 복호화

        Args:
            encrypted_text: 암호화된 Base64 문자열

        Returns:
            복호화된 평문 문자열
        """
        if not encrypted_text:
            return encrypted_text

        try:
            decrypted_bytes = self.fernet.decrypt(encrypted_text.encode('utf-8'))
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            # 복호화 실패 시 에러 표시 반환 (또는 예외 발생)
            return "[DECRYPTION_ERROR]"


class FileEncryptor:
    """파일 바이너리 암호화/복호화를 위한 Fernet 래퍼"""

    def __init__(self, key: bytes):
        """
        Args:
            key: Fernet 키 (Base64 인코딩된 32바이트)
        """
        self.fernet = Fernet(key)

    def encrypt_file(self, file_bytes: bytes) -> bytes:
        """
        파일 바이트를 암호화

        Args:
            file_bytes: 암호화할 파일 바이트

        Returns:
            암호화된 바이트
        """
        if not file_bytes:
            return file_bytes

        try:
            return self.fernet.encrypt(file_bytes)
        except Exception as e:
            logger.error(f"File encryption failed: {e}")
            raise

    def decrypt_file(self, encrypted_bytes: bytes) -> bytes:
        """
        암호화된 파일 바이트를 복호화

        Args:
            encrypted_bytes: 암호화된 바이트

        Returns:
            복호화된 파일 바이트
        """
        if not encrypted_bytes:
            return encrypted_bytes

        try:
            return self.fernet.decrypt(encrypted_bytes)
        except Exception as e:
            logger.error(f"File decryption failed: {e}")
            raise


class EncryptedString(TypeDecorator):
    """
    문자열 필드 암호화 SQLAlchemy TypeDecorator

    DB 저장 시 자동 암호화, 조회 시 자동 복호화
    """

    impl = Text  # DB 저장 시 Text 타입 사용
    cache_ok = True

    def __init__(self, encryptor: FieldEncryptor, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.encryptor = encryptor

    def process_bind_param(self, value: Optional[str], dialect) -> Optional[str]:
        """DB 저장 전 암호화"""
        if value is not None:
            return self.encryptor.encrypt(value)
        return value

    def process_result_value(self, value: Optional[str], dialect) -> Optional[str]:
        """DB 조회 후 복호화"""
        if value is not None:
            return self.encryptor.decrypt(value)
        return value


class EncryptedJSON(TypeDecorator):
    """
    JSON 필드 암호화 SQLAlchemy TypeDecorator

    JSON을 문자열로 변환 후 암호화하여 DB에 저장
    조회 시 복호화 후 JSON으로 파싱
    """

    impl = Text
    cache_ok = True

    def __init__(self, encryptor: FieldEncryptor, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.encryptor = encryptor

    def process_bind_param(self, value: Optional[dict], dialect) -> Optional[str]:
        """DB 저장 전: JSON → 문자열 → 암호화"""
        if value is not None:
            try:
                json_str = json.dumps(value, ensure_ascii=False)
                return self.encryptor.encrypt(json_str)
            except Exception as e:
                logger.error(f"JSON encryption failed: {e}")
                raise
        return value

    def process_result_value(self, value: Optional[str], dialect) -> Optional[dict]:
        """DB 조회 후: 복호화 → JSON 파싱"""
        if value is not None:
            try:
                json_str = self.encryptor.decrypt(value)
                if json_str == "[DECRYPTION_ERROR]":
                    return None
                return json.loads(json_str)
            except Exception as e:
                logger.error(f"JSON decryption failed: {e}")
                return None
        return value


# 싱글톤 encryptor 인스턴스
_field_encryptor: Optional[FieldEncryptor] = None
_file_encryptor: Optional[FileEncryptor] = None


def get_field_encryptor() -> FieldEncryptor:
    """
    싱글톤 패턴으로 FieldEncryptor 인스턴스 반환

    Returns:
        FieldEncryptor 인스턴스

    Raises:
        ValueError: ENCRYPTION_KEY 환경 변수가 설정되지 않은 경우
    """
    global _field_encryptor

    if _field_encryptor is None:
        from app.config import settings

        if not settings.encryption_key:
            raise ValueError("ENCRYPTION_KEY environment variable is required")

        _field_encryptor = FieldEncryptor(settings.encryption_key.encode('utf-8'))

    return _field_encryptor


def get_file_encryptor() -> FileEncryptor:
    """
    싱글톤 패턴으로 FileEncryptor 인스턴스 반환

    Returns:
        FileEncryptor 인스턴스

    Raises:
        ValueError: ENCRYPTION_KEY 환경 변수가 설정되지 않은 경우
    """
    global _file_encryptor

    if _file_encryptor is None:
        from app.config import settings

        if not settings.encryption_key:
            raise ValueError("ENCRYPTION_KEY environment variable is required")

        _file_encryptor = FileEncryptor(settings.encryption_key.encode('utf-8'))

    return _file_encryptor
