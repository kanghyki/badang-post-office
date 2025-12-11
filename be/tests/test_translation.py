"""
Translation 엔드포인트 테스트

POST /v1/translation/jeju - 제주 방언 번역
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestTranslateToJeju:
    """제주 방언 번역 테스트"""

    async def test_translate_empty_text(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """빈 텍스트 번역 (유효성 검사 실패)"""
        response = await client.post(
            "/v1/translation/jeju",
            headers=auth_headers,
            json={"text": ""}
        )
        
        # Pydantic 모델에 따라 min_length 검증 실패 예상
        assert response.status_code == 422

    async def test_translate_missing_text_field(
        self, client: AsyncClient, auth_headers: dict
    ):
        """필수 필드 누락"""
        response = await client.post(
            "/v1/translation/jeju",
            headers=auth_headers,
            json={}
        )
        
        assert response.status_code == 422
