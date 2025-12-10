"""
폰트 API 라우터 (개발/운영용)

메모리에 로드된 폰트 목록 조회 엔드포인트를 제공합니다.

⚠️ 주의: 이 API는 프로덕션 환경에서 사용하지 않습니다 (env=dev일 때만 활성화).
"""

from fastapi import APIRouter, HTTPException
from app.services import font_service
from app.models.font import FontListResponse, FontResponse

router = APIRouter(
    prefix="/v1/fonts",
    tags=["Fonts (개발/운영용)"]
)


@router.get("", response_model=FontListResponse)
def get_fonts():
    """
    메모리에 로드된 폰트 목록을 조회합니다.
    """
    fonts = font_service.get_all_fonts()

    # Font 모델을 API 응답용 FontResponse 모델로 변환
    fonts_response = [FontResponse.from_font(f) for f in fonts]

    return FontListResponse(fonts=fonts_response)


@router.get("/{font_id}", response_model=FontResponse)
def get_font(font_id: str):
    """
    특정 폰트를 ID로 조회합니다.
    """
    font = font_service.get_font_by_id(font_id)

    if not font:
        raise HTTPException(status_code=404, detail="폰트를 찾을 수 없습니다.")

    return FontResponse.from_font(font)
