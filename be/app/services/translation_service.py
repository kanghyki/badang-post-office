"""
제주 방언 번역 서비스

싱글톤 패턴을 사용하여 모델을 한 번만 로드하고 재사용합니다.
"""
import asyncio
import threading
from typing import Literal, Optional

from llama_cpp import Llama

from app.config import settings


class JejumaTranslator:
    """표준어와 제주 방언 간 번역을 수행하는 클래스"""
    
    PROMPT_TEMPLATE = """<|start_header_id|>system<|end_header_id|>

You are a helpful assistant for translating between standard Korean and regional dialects.
<|eot_id|><|start_header_id|>user<|end_header_id|>

{prompt}
<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
    
    def __init__(
        self, 
        model_path: str,
        n_ctx: int = 512,
        n_gpu_layers: int = 0,
        temperature: float = 0.3,
        top_p: float = 0.95,
        top_k: int = 40
    ):
        """
        Args:
            model_path: GGUF 모델 파일 경로
            n_ctx: 컨텍스트 윈도우 크기
            n_gpu_layers: GPU에 올릴 레이어 수 (0이면 CPU만 사용)
            temperature: 샘플링 temperature (낮을수록 더 결정적)
            top_p: nucleus sampling threshold
            top_k: top-k sampling
        """
        print(f"모델 로딩 중: {model_path}")
        self.llm = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_gpu_layers=n_gpu_layers,
            verbose=False
        )
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        print("모델 로딩 완료!")
    
    def _generate(self, prompt: str, max_tokens: int = 256) -> str:
        """내부 추론 함수"""
        full_prompt = self.PROMPT_TEMPLATE.format(prompt=prompt)
        
        output = self.llm(
            full_prompt,
            max_tokens=max_tokens,
            temperature=self.temperature,
            top_p=self.top_p,
            top_k=self.top_k,
            stop=["<|eot_id|>", "<|end_of_text|>"],
            echo=False
        )
        
        return output['choices'][0]['text'].strip()
    
    def standard_to_dialect(
        self, 
        text: str, 
        region: Literal['jeju', 'chungcheong', 'gangwon', 'gyeongsang', 'jeonla'] = 'jeju',
        max_tokens: int = 256
    ) -> str:
        """
        표준어를 방언으로 번역
        
        Args:
            text: 번역할 표준어 문장
            region: 목표 방언 지역
            max_tokens: 최대 생성 토큰 수
            
        Returns:
            번역된 방언 문장
        """
        prompt = f"Convert the following sentence or word which is standard Korean to {region}'s dialect: {text}"
        return self._generate(prompt, max_tokens)
    
    def dialect_to_standard(
        self, 
        text: str, 
        region: Literal['jeju', 'chungcheong', 'gangwon', 'gyeongsang', 'jeonla'] = 'jeju',
        max_tokens: int = 256
    ) -> str:
        """
        방언을 표준어로 번역
        
        Args:
            text: 번역할 방언 문장
            region: 원본 방언 지역
            max_tokens: 최대 생성 토큰 수
            
        Returns:
            번역된 표준어 문장
        """
        prompt = f"Convert the following sentence or word which is {region}'s dialect to standard Korean: {text}"
        return self._generate(prompt, max_tokens)
    
    def detect_dialect(self, text: str, max_tokens: int = 64) -> str:
        """
        방언 종류 탐지
        
        Args:
            text: 분석할 문장
            max_tokens: 최대 생성 토큰 수
            
        Returns:
            감지된 방언 종류
        """
        prompt = f"Detect the following sentence or word is standard, jeju, chungcheong, gangwon, gyeongsang, or jeonla's dialect: {text}"
        return self._generate(prompt, max_tokens)
    
    def detect_and_translate(self, text: str, max_tokens: int = 256) -> str:
        """
        방언 탐지 후 표준어로 번역
        
        Args:
            text: 번역할 문장
            max_tokens: 최대 생성 토큰 수
            
        Returns:
            "(방언종류->standard) 번역결과" 형식의 문자열
        """
        prompt = f"Detect the following sentence or word is which dialect and convert the following sentence or word to standard Korean: {text}"
        return self._generate(prompt, max_tokens)


class TranslatorSingleton:
    """
    JejumaTranslator 싱글톤 관리 클래스
    
    Thread-safe하게 모델 인스턴스를 한 번만 생성하고 재사용합니다.
    """
    _instance: Optional[JejumaTranslator] = None
    _lock = threading.Lock()
    
    @classmethod
    def get_instance(cls) -> JejumaTranslator:
        """
        싱글톤 인스턴스 반환
        
        Double-check locking 패턴을 사용하여 thread-safe하게 인스턴스를 생성합니다.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = JejumaTranslator(
                        model_path=settings.translation_model_path,
                        n_ctx=settings.translation_n_ctx,
                        n_gpu_layers=settings.translation_n_gpu_layers,
                        temperature=settings.translation_temperature,
                        top_p=settings.translation_top_p,
                        top_k=settings.translation_top_k
                    )
        return cls._instance
    
    @classmethod
    def reset(cls) -> None:
        """인스턴스 초기화 (테스트용)"""
        with cls._lock:
            cls._instance = None


def translate_to_jeju(text: str) -> str:
    """
    표준어를 제주 방언으로 번역
    
    싱글톤 인스턴스를 사용하여 모델 로딩 오버헤드를 제거합니다.

    Args:
        text: 번역할 표준어 문장

    Returns:
        제주 방언으로 번역된 문장
    """
    translator = TranslatorSingleton.get_instance()
    return translator.standard_to_dialect(text, region='jeju')


async def translate_to_jeju_async(text: str) -> str:
    """
    제주어 번역 (비동기 래퍼)

    동기 함수인 translate_to_jeju()를 asyncio.to_thread()로 래핑하여
    async 컨텍스트에서 안전하게 호출할 수 있도록 합니다.

    Args:
        text: 번역할 문장

    Returns:
        제주어로 번역된 문장
    """
    return await asyncio.to_thread(translate_to_jeju, text)
