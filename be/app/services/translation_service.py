"""
제주 방언 번역 서비스

LLM + RAG 기반 번역 서비스를 제공합니다.
"""
import asyncio
import logging
import threading
from typing import Literal, Optional

from openai import OpenAI

from app.config import settings

logger = logging.getLogger(__name__)

async def translate_to_jeju_async(text: str) -> str:
    """
    제주어 번역 (비동기 래퍼)

    LLM + RAG를 사용하여 번역합니다.

    Args:
        text: 번역할 문장

    Returns:
        제주어로 번역된 문장
    """
    # LLM + RAG 사용
    return await translate_to_jeju_gpt_async(text)


# ============================================================================
# LLM + RAG 기반 번역 (새로운 방식)
# ============================================================================

class JejuTranslator:
    """LLM + RAG 기반 제주어 번역"""

    SYSTEM_PROMPT = """You are a Jeju language translation expert.

**Role**:

* Translate Standard Korean into natural and accurate Jeju language
* Fully understand and reflect the cultural nuances and dialectal characteristics of Jeju

**Translation Principles**:

1. Naturalness first: Prioritize conveying meaning and natural flow over literal translation
2. Context awareness: Refer to any provided reference information, but apply it appropriately based on context
3. Honorific consistency: Preserve the honorific or casual speech level of the source text in Jeju
4. Conciseness: Output only the translation without unnecessary explanation

**Output Format**:

* Output only the translated Jeju language text
* No additional explanations, annotations, or meta information
"""

    def __init__(self):
        """OpenAI 클라이언트 및 RAG 서비스 초기화"""
        logger.info("JejuGPTTranslator 초기화 중...")
        self.client = OpenAI(api_key=settings.openai_api_key)

        # RAG 서비스 초기화 (지연 로드)
        self.rag_service = None
        if settings.rag_enabled:
            try:
                from app.services.jeju_rag_service import JejuRAGServiceSingleton
                self.rag_service = JejuRAGServiceSingleton.get_instance()
                logger.info("RAG 서비스 초기화 완료")
            except Exception as e:
                logger.error(f"RAG 서비스 초기화 실패: {str(e)}")
                logger.warning("RAG 없이 LLM만 사용합니다")

        logger.info("JejuGPTTranslator 초기화 완료")

    def _get_rag_context(self, text: str) -> str:
        """RAG 검색으로 관련 제주어 사전 항목 추출"""
        if not self.rag_service:
            return ""

        try:
            results = self.rag_service.search(text, top_k=settings.rag_top_k)

            if not results:
                logger.debug(f"RAG 검색 결과 없음: '{text}'")
                return ""

            context = "**참고 사전 정보**:\n"
            for i, result in enumerate(results, 1):
                context += f"{i}. {result['standard']} → {result['jeju']}"
                if result.get('category'):
                    context += f" (카테고리: {result['category']})"
                context += "\n"

            logger.debug(f"RAG 컨텍스트 생성 완료: {len(results)}개 항목")
            return context

        except Exception as e:
            logger.error(f"RAG 검색 중 오류: {str(e)}")
            return ""

    def _build_user_prompt(self, text: str, rag_context: str) -> str:
        """사용자 프롬프트 생성"""
        if rag_context:
            return f"""{rag_context}

**번역 요청**:
{text}

위 사전 정보를 참고하여 자연스러운 제주어로 번역하세요."""
        else:
            return f"""**번역 요청**:
{text}

자연스러운 제주어로 번역하세요."""

    def standard_to_dialect(self, text: str, region: str = 'jeju') -> str:
        """
        LLM API 호출 및 번역

        Args:
            text: 번역할 표준어 문장
            region: 목표 방언 지역 (현재 'jeju'만 지원)

        Returns:
            번역된 제주어 문장
        """
        try:
            # 1. RAG 컨텍스트 추출
            rag_context = self._get_rag_context(text)

            # 2. 프롬프트 생성
            user_prompt = self._build_user_prompt(text, rag_context)

            # 3. LLM API 호출
            logger.debug(f"LLM API 호출: '{text[:50]}...'")
            response = self.client.chat.completions.create(
                model=settings.translation_model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                max_completion_tokens=settings.translation_max_completion_tokens,
            )

            translated = response.choices[0].message.content.strip()
            logger.info(f"번역 완료: '{text}' → '{translated}'")
            return translated

        except Exception as e:
            logger.error(f"LLM 번역 실패: {str(e)}")
            # 폴백: 원문 반환
            logger.warning(f"폴백: 원문 반환 - '{text}'")
            return text


class JejuGPTTranslatorSingleton:
    """싱글톤 관리 (thread-safe)"""
    _instance: Optional[JejuTranslator] = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> JejuTranslator:
        """
        싱글톤 인스턴스 반환

        Double-check locking 패턴을 사용하여 thread-safe하게 인스턴스를 생성합니다.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = JejuTranslator()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """인스턴스 초기화 (테스트용)"""
        with cls._lock:
            cls._instance = None


# ============================================================================
# 기존 인터페이스 (LLM 사용하도록 변경)
# ============================================================================

def translate_to_jeju_gpt(text: str) -> str:
    """
    표준어를 제주 방언으로 번역 (LLM + RAG)

    Args:
        text: 번역할 표준어 문장

    Returns:
        제주 방언으로 번역된 문장
    """
    translator = JejuGPTTranslatorSingleton.get_instance()
    return translator.standard_to_dialect(text)


async def translate_to_jeju_gpt_async(text: str) -> str:
    """
    제주어 번역 (비동기 래퍼, LLM + RAG)

    Args:
        text: 번역할 문장

    Returns:
        제주어로 번역된 문장
    """
    return await asyncio.to_thread(translate_to_jeju_gpt, text)
