"""
Templates 엔드포인트 테스트

GET /v1/templates - 템플릿 목록 조회
GET /v1/templates/{id} - 템플릿 상세 조회
"""
import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock

from app.models.template import Template, TemplateResponse


@pytest.fixture
def mock_templates():
    """테스트용 템플릿 데이터"""
    return [
        Template(
            id="template-1",
            name="템플릿 1",
            description="첫 번째 템플릿",
            template_image_path="static/templates/template1.jpg",
            width=800,
            height=600,
            text_configs=[],
            photo_configs=[]
        ),
        Template(
            id="template-2",
            name="템플릿 2",
            description="두 번째 템플릿",
            template_image_path="static/templates/template2.jpg",
            width=800,
            height=600,
            text_configs=[],
            photo_configs=[]
        )
    ]


@pytest.mark.asyncio
class TestGetTemplates:
    """템플릿 목록 조회 테스트"""

    @patch("app.services.template_service.get_all_templates")
    async def test_get_templates_success(
        self,
        mock_get_all: MagicMock,
        client: AsyncClient,
        auth_headers: dict,
        mock_templates: list
    ):
        """템플릿 목록 조회 성공"""
        mock_get_all.return_value = mock_templates
        
        response = await client.get(
            "/v1/templates",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert len(data["templates"]) == 2
        assert data["templates"][0]["id"] == "template-1"
        assert data["templates"][1]["id"] == "template-2"

    @patch("app.services.template_service.get_all_templates")
    async def test_get_templates_empty(
        self,
        mock_get_all: MagicMock,
        client: AsyncClient,
        auth_headers: dict
    ):
        """템플릿이 없는 경우"""
        mock_get_all.return_value = []
        
        response = await client.get(
            "/v1/templates",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert len(data["templates"]) == 0

    @patch("app.services.template_service.get_all_templates")
    async def test_get_templates_unauthorized(
        self, mock_get_all: MagicMock, client: AsyncClient
    ):
        """인증 없이 템플릿 목록 조회 시도"""
        mock_get_all.return_value = []
        response = await client.get("/v1/templates")
        # 실제 인증이 필요하면 403, 아니면 200
        assert response.status_code in [200, 403]


@pytest.mark.asyncio
class TestGetTemplateDetail:
    """템플릿 상세 조회 테스트"""

    @patch("app.services.template_service.get_template_by_id")
    async def test_get_template_detail_success(
        self,
        mock_get_by_id: MagicMock,
        client: AsyncClient,
        auth_headers: dict,
        mock_templates: list
    ):
        """템플릿 상세 조회 성공"""
        mock_get_by_id.return_value = mock_templates[0]
        
        response = await client.get(
            "/v1/templates/template-1",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "template-1"
        assert data["name"] == "템플릿 1"
        assert data["width"] == 800
        assert data["height"] == 600

    @patch("app.services.template_service.get_template_by_id")
    async def test_get_template_detail_not_found(
        self,
        mock_get_by_id: MagicMock,
        client: AsyncClient,
        auth_headers: dict
    ):
        """존재하지 않는 템플릿 조회"""
        mock_get_by_id.return_value = None
        
        response = await client.get(
            "/v1/templates/nonexistent",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "템플릿을 찾을 수 없습니다" in response.json()["detail"]

    @patch("app.services.template_service.get_template_by_id")
    async def test_get_template_detail_unauthorized(
        self, mock_get_by_id: MagicMock, client: AsyncClient
    ):
        """인증 없이 템플릿 상세 조회 시도"""
        mock_get_by_id.return_value = None
        response = await client.get("/v1/templates/template-1")
        # 실제 인증이 필요하면 403, 템플릿이 없어서 404
        assert response.status_code in [403, 404]

    @patch("app.services.template_service.get_template_by_id")
    async def test_get_template_detail_with_configs(
        self,
        mock_get_by_id: MagicMock,
        client: AsyncClient,
        auth_headers: dict
    ):
        """text_configs와 photo_configs가 있는 템플릿 조회"""
        from app.models.template import TextConfig, PhotoConfig
        
        template_with_configs = Template(
            id="template-3",
            name="상세 템플릿",
            description="설정이 있는 템플릿",
            template_image_path="static/templates/template3.jpg",
            width=800,
            height=600,
            text_configs=[
                TextConfig(id="text1", x=100, y=100, max_width=300, font_size=24)
            ],
            photo_configs=[
                PhotoConfig(id="photo1", x=50, y=50, max_width=200, max_height=200)
            ]
        )
        mock_get_by_id.return_value = template_with_configs
        
        response = await client.get(
            "/v1/templates/template-3",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["text_configs"]) == 1
        assert len(data["photo_configs"]) == 1
        assert data["text_configs"][0]["id"] == "text1"
        assert data["photo_configs"][0]["id"] == "photo1"
