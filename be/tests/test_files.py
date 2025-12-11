"""
Files 엔드포인트 테스트

GET /v1/files/templates/{file_path} - 템플릿 파일 접근
"""
import pytest
from pathlib import Path
from httpx import AsyncClient


@pytest.fixture
def setup_test_files():
    """테스트용 파일 생성"""
    # 템플릿 파일
    template_dir = Path("static/templates")
    template_dir.mkdir(parents=True, exist_ok=True)
    template_file = template_dir / "test-template.jpg"
    template_file.write_text("test template content")
    
    yield
    
    # 정리
    if template_file.exists():
        template_file.unlink()


@pytest.mark.asyncio
class TestGetTemplateFilePublic:
    """템플릿 파일 공개 접근 테스트"""

    async def test_get_template_file_public_success(
        self,
        client: AsyncClient,
        setup_test_files
    ):
        """인증 없이 템플릿 파일 접근 성공"""
        response = await client.get(
            "/v1/files/templates/test-template.jpg"
        )
        
        assert response.status_code == 200
        assert response.content == b"test template content"

    async def test_get_template_file_public_with_auth(
        self,
        client: AsyncClient,
        auth_headers: dict,
        setup_test_files
    ):
        """인증 헤더가 있어도 템플릿 파일 접근 가능"""
        response = await client.get(
            "/v1/files/templates/test-template.jpg",
            headers=auth_headers
        )
        
        assert response.status_code == 200

    async def test_get_template_file_public_not_found(
        self, client: AsyncClient
    ):
        """존재하지 않는 템플릿 파일"""
        response = await client.get(
            "/v1/files/templates/nonexistent.jpg"
        )
        
        assert response.status_code == 404

    async def test_get_nested_template_file(
        self, client: AsyncClient, setup_test_files
    ):
        """중첩된 디렉토리의 템플릿 파일 접근"""
        # 중첩 디렉토리 생성
        nested_dir = Path("static/templates/subdir")
        nested_dir.mkdir(parents=True, exist_ok=True)
        nested_file = nested_dir / "nested-template.jpg"
        nested_file.write_text("nested template content")
        
        try:
            response = await client.get(
                "/v1/files/templates/subdir/nested-template.jpg"
            )
            
            assert response.status_code == 200
            assert response.content == b"nested template content"
        finally:
            if nested_file.exists():
                nested_file.unlink()
            if nested_dir.exists():
                nested_dir.rmdir()
