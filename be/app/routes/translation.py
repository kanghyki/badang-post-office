"""
제주 방언 번역 API 라우터 (개발/테스트용)

제주 방언 번역 기능을 테스트할 수 있는 엔드포인트를 제공합니다.
"""

from fastapi import APIRouter, HTTPException, Depends
from app.services.translation_service import translate_to_jeju
from app.models.translation import TranslationRequest, TranslationResponse
from app.database.models import User
from app.dependencies.auth import get_current_user

router = APIRouter(
    prefix="/v1/translation",
    tags=["Translation"]
)


@router.post("/jeju", response_model=TranslationResponse)
async def translate_text_to_jeju(
    request: TranslationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    표준어를 제주 방언으로 번역합니다.

    **사용 예시:**
    ```json
    {
        "text": "안녕하세요, 오늘 날씨가 정말 좋네요!"
    }
    ```

    **응답 예시:**
    ```json
    {
        "original_text": "안녕하세요, 오늘 날씨가 정말 좋네요!",
        "translated_text": "안녕하우꽈, 오늘 날씨가 정말 곱습니다게!",
        "model_used": "gpt-4o-mini"
    }
    ```

    **주의사항:**
    - 환경변수 OPENAI_API_KEY가 설정되어 있어야 합니다
    - 환경변수로 OPENAI_MODEL과 OPENAI_TEMPERATURE를 설정할 수 있습니다
    """
    try:
        from app.config import settings
        
        # 제주 방언으로 번역
        translated = translate_to_jeju(text=request.text)

        return TranslationResponse(
            original_text=request.text,
            translated_text=translated,
            model_used=settings.openai_model
        )

    except Exception as e:
        # OpenAI API 에러 처리
        raise HTTPException(
            status_code=500,
            detail=f"번역 중 오류가 발생했습니다: {str(e)}"
        )
