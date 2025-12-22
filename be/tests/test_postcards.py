"""
Postcards 엔드포인트 테스트

POST /v1/postcards/create - 편지 생성
GET /v1/postcards - 편지 목록 조회
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User, Postcard


@pytest.fixture
async def test_postcard(db_session: AsyncSession, test_user: User) -> Postcard:
    """테스트용 편지 생성"""
    postcard = Postcard(
        user_id=test_user.id,
        template_id="test-template",
        status="writing"
    )
    db_session.add(postcard)
    await db_session.commit()
    await db_session.refresh(postcard)
    return postcard


@pytest.mark.asyncio
class TestListPostcards:
    """편지 목록 조회 테스트"""

    async def test_list_postcards_success(
        self, client: AsyncClient, auth_headers: dict, test_postcard: Postcard
    ):
        """편지 목록 조회 성공"""
        response = await client.get(
            "/v1/postcards",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_list_postcards_with_status_filter(
        self, client: AsyncClient, auth_headers: dict, test_postcard: Postcard
    ):
        """상태 필터링으로 편지 목록 조회"""
        response = await client.get(
            "/v1/postcards?status=writing",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for postcard in data:
            assert postcard["status"] == "writing"

    async def test_list_postcards_only_own_postcards(
        self, 
        client: AsyncClient, 
        auth_headers: dict,
        auth_headers_user2: dict,
        test_postcard: Postcard,
        db_session: AsyncSession,
        test_user2: User
    ):
        """다른 사용자의 편지는 조회되지 않음"""
        # test_user2의 편지 생성
        postcard2 = Postcard(
            user_id=test_user2.id,
            template_id="test-template",
            status="writing"
        )
        db_session.add(postcard2)
        await db_session.commit()
        
        # test_user로 조회
        response = await client.get(
            "/v1/postcards",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        postcard_ids = [p["id"] for p in data]
        assert test_postcard.id in postcard_ids
        assert postcard2.id not in postcard_ids
