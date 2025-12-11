"""
제주 방언 번역 API 요청/응답 모델
"""

from pydantic import BaseModel, Field, ConfigDict


class TranslationRequest(BaseModel):
    """제주 방언 번역 요청"""

    text: str = Field(
        ...,
        description="번역할 텍스트",
        min_length=1,
        examples=["안녕하세요, 오늘 날씨가 정말 좋네요!"]
    )


class TranslationResponse(BaseModel):
    """제주 방언 번역 응답"""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "original_text": "안녕하세요, 오늘 날씨가 정말 좋네요!",
                "translated_text": "안녕하우꽈, 오늘 날씨가 정말 곱습니다게!",
                "model_used": "gpt-4o-mini"
            }
        }
    )

    original_text: str = Field(
        ...,
        description="원본 텍스트"
    )
    translated_text: str = Field(
        ...,
        description="제주 방언으로 번역된 텍스트"
    )
    model_used: str = Field(
        ...,
        description="사용된 모델명"
    )
