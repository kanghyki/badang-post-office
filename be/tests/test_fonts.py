"""
Fonts 엔드포인트 테스트

GET /v1/fonts - 폰트 목록 조회
GET /v1/fonts/{id} - 폰트 상세 조회
"""
import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock

from app.models.font import Font


@pytest.fixture
def mock_fonts():
    """테스트용 폰트 데이터"""
    return [
        Font(
            id="font-1",
            name="나눔고딕",
            font_path="static/fonts/nanumgothic.ttf"
        ),
        Font(
            id="font-2",
            name="나눔명조",
            font_path="static/fonts/nanummyeongjo.ttf"
        )
    ]


@pytest.mark.asyncio
class TestGetFonts:
    """폰트 목록 조회 테스트"""

    @patch("app.services.font_service.get_all_fonts")
    async def test_get_fonts_success(
        self,
        mock_get_all: MagicMock,
        client: AsyncClient,
        mock_fonts: list
    ):
        """폰트 목록 조회 성공 (인증 불필요)"""
        mock_get_all.return_value = mock_fonts
        
        response = await client.get("/v1/fonts")
        
        assert response.status_code == 200
        data = response.json()
        assert "fonts" in data
        assert len(data["fonts"]) == 2
        assert data["fonts"][0]["id"] == "font-1"
        assert data["fonts"][0]["name"] == "나눔고딕"
        assert data["fonts"][1]["id"] == "font-2"

    @patch("app.services.font_service.get_all_fonts")
    async def test_get_fonts_empty(
        self,
        mock_get_all: MagicMock,
        client: AsyncClient
    ):
        """폰트가 없는 경우"""
        mock_get_all.return_value = []
        
        response = await client.get("/v1/fonts")
        
        assert response.status_code == 200
        data = response.json()
        assert "fonts" in data
        assert len(data["fonts"]) == 0

    @patch("app.services.font_service.get_all_fonts")
    async def test_get_fonts_with_auth(
        self,
        mock_get_all: MagicMock,
        client: AsyncClient,
        auth_headers: dict,
        mock_fonts: list
    ):
        """인증 헤더가 있어도 폰트 목록 조회 가능"""
        mock_get_all.return_value = mock_fonts
        
        response = await client.get(
            "/v1/fonts",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["fonts"]) == 2


@pytest.mark.asyncio
class TestGetFont:
    """폰트 상세 조회 테스트"""

    @patch("app.services.font_service.get_font_by_id")
    async def test_get_font_success(
        self,
        mock_get_by_id: MagicMock,
        client: AsyncClient,
        mock_fonts: list
    ):
        """폰트 상세 조회 성공"""
        mock_get_by_id.return_value = mock_fonts[0]
        
        response = await client.get("/v1/fonts/font-1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "font-1"
        assert data["name"] == "나눔고딕"

    @patch("app.services.font_service.get_font_by_id")
    async def test_get_font_not_found(
        self,
        mock_get_by_id: MagicMock,
        client: AsyncClient
    ):
        """존재하지 않는 폰트 조회"""
        mock_get_by_id.return_value = None
        
        response = await client.get("/v1/fonts/nonexistent")
        
        assert response.status_code == 404
        assert "폰트를 찾을 수 없습니다" in response.json()["detail"]

    @patch("app.services.font_service.get_font_by_id")
    async def test_get_font_with_auth(
        self,
        mock_get_by_id: MagicMock,
        client: AsyncClient,
        auth_headers: dict,
        mock_fonts: list
    ):
        """인증 헤더가 있어도 폰트 조회 가능"""
        mock_get_by_id.return_value = mock_fonts[0]
        
        response = await client.get(
            "/v1/fonts/font-1",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "font-1"

    @patch("app.services.font_service.get_font_by_id")
    async def test_get_custom_font(
        self,
        mock_get_by_id: MagicMock,
        client: AsyncClient
    ):
        """커스텀 폰트 조회"""
        custom_font = Font(
            id="custom-font",
            name="Custom Font",
            font_path="static/fonts/custom.ttf"
        )
        mock_get_by_id.return_value = custom_font
        
        response = await client.get("/v1/fonts/custom-font")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "custom-font"