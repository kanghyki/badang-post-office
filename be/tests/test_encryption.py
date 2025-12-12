"""
암호화 기능 테스트

DB 필드 암호화 및 파일 암호화 기능을 검증합니다.
"""

import pytest
from cryptography.fernet import Fernet
from app.utils.encryption import FieldEncryptor, FileEncryptor, EncryptedString, EncryptedJSON


class TestFieldEncryptor:
    """FieldEncryptor 테스트"""

    def test_encrypt_decrypt_english(self):
        """영문 텍스트 암호화/복호화"""
        key = Fernet.generate_key()
        encryptor = FieldEncryptor(key)

        plain_text = "test@example.com"
        encrypted = encryptor.encrypt(plain_text)
        decrypted = encryptor.decrypt(encrypted)

        assert encrypted != plain_text, "암호화되어야 합니다"
        assert decrypted == plain_text, "복호화 결과가 원본과 일치해야 합니다"

    def test_encrypt_decrypt_korean(self):
        """한글 텍스트 암호화/복호화"""
        key = Fernet.generate_key()
        encryptor = FieldEncryptor(key)

        korean_text = "홍길동"
        encrypted = encryptor.encrypt(korean_text)
        decrypted = encryptor.decrypt(encrypted)

        assert encrypted != korean_text, "암호화되어야 합니다"
        assert decrypted == korean_text, "복호화 결과가 원본과 일치해야 합니다"

    def test_null_handling(self):
        """NULL 값 처리"""
        key = Fernet.generate_key()
        encryptor = FieldEncryptor(key)

        assert encryptor.encrypt(None) is None
        assert encryptor.decrypt(None) is None
        assert encryptor.encrypt("") == ""
        assert encryptor.decrypt("") == ""


class TestFileEncryptor:
    """FileEncryptor 테스트"""

    def test_encrypt_decrypt_file(self):
        """파일 바이너리 암호화/복호화"""
        key = Fernet.generate_key()
        file_encryptor = FileEncryptor(key)

        # 가짜 이미지 바이트 (실제로는 바이너리 데이터)
        original_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        encrypted_bytes = file_encryptor.encrypt_file(original_bytes)
        decrypted_bytes = file_encryptor.decrypt_file(encrypted_bytes)

        assert encrypted_bytes != original_bytes, "암호화되어야 합니다"
        assert decrypted_bytes == original_bytes, "복호화 결과가 원본과 일치해야 합니다"

    def test_large_file(self):
        """대용량 파일 처리 (100KB)"""
        key = Fernet.generate_key()
        file_encryptor = FileEncryptor(key)

        # 100KB 데이터 생성
        large_data = b"x" * (100 * 1024)
        encrypted_bytes = file_encryptor.encrypt_file(large_data)
        decrypted_bytes = file_encryptor.decrypt_file(encrypted_bytes)

        assert decrypted_bytes == large_data, "대용량 파일도 정확히 복호화되어야 합니다"

    def test_null_handling(self):
        """NULL 바이트 처리"""
        key = Fernet.generate_key()
        file_encryptor = FileEncryptor(key)

        assert file_encryptor.encrypt_file(None) is None
        assert file_encryptor.decrypt_file(None) is None
        assert file_encryptor.encrypt_file(b"") == b""
        assert file_encryptor.decrypt_file(b"") == b""


class TestEncryptedTypes:
    """SQLAlchemy TypeDecorator 테스트"""

    def test_encrypted_string(self):
        """EncryptedString TypeDecorator"""
        key = Fernet.generate_key()
        encryptor = FieldEncryptor(key)
        encrypted_string = EncryptedString(encryptor)

        # DB 저장 시 (process_bind_param)
        plain_value = "test@example.com"
        encrypted_value = encrypted_string.process_bind_param(plain_value, None)
        assert encrypted_value != plain_value, "저장 시 암호화되어야 합니다"

        # DB 조회 시 (process_result_value)
        decrypted_value = encrypted_string.process_result_value(encrypted_value, None)
        assert decrypted_value == plain_value, "조회 시 복호화되어야 합니다"

    def test_encrypted_json(self):
        """EncryptedJSON TypeDecorator"""
        key = Fernet.generate_key()
        encryptor = FieldEncryptor(key)
        encrypted_json = EncryptedJSON(encryptor)

        # JSON 데이터
        json_data = {"name": "홍길동", "email": "test@example.com"}

        # DB 저장 시 (process_bind_param)
        encrypted_value = encrypted_json.process_bind_param(json_data, None)
        assert isinstance(encrypted_value, str), "JSON이 문자열로 암호화되어야 합니다"

        # DB 조회 시 (process_result_value)
        decrypted_value = encrypted_json.process_result_value(encrypted_value, None)
        assert decrypted_value == json_data, "조회 시 JSON으로 복호화되어야 합니다"

    def test_encrypted_json_null(self):
        """EncryptedJSON NULL 처리"""
        key = Fernet.generate_key()
        encryptor = FieldEncryptor(key)
        encrypted_json = EncryptedJSON(encryptor)

        assert encrypted_json.process_bind_param(None, None) is None
        assert encrypted_json.process_result_value(None, None) is None


def test_encryption_key_consistency():
    """같은 키를 사용하면 동일한 복호화 결과를 얻어야 함"""
    key = Fernet.generate_key()
    encryptor1 = FieldEncryptor(key)
    encryptor2 = FieldEncryptor(key)

    plain_text = "consistent test"
    encrypted = encryptor1.encrypt(plain_text)

    # 다른 인스턴스지만 같은 키를 사용하므로 복호화 가능
    decrypted = encryptor2.decrypt(encrypted)
    assert decrypted == plain_text, "같은 키로 복호화 가능해야 합니다"


def test_different_keys_fail():
    """다른 키로는 복호화 실패해야 함"""
    key1 = Fernet.generate_key()
    key2 = Fernet.generate_key()

    encryptor1 = FieldEncryptor(key1)
    encryptor2 = FieldEncryptor(key2)

    plain_text = "secret message"
    encrypted = encryptor1.encrypt(plain_text)

    # 다른 키로 복호화 시도
    decrypted = encryptor2.decrypt(encrypted)
    assert decrypted == "[DECRYPTION_ERROR]", "다른 키로는 복호화 실패해야 합니다"
