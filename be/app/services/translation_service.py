from pathlib import Path
from llama_cpp import Llama
from typing import Literal

class JejumaTranslator:
    """표준어와 제주 방언 간 번역을 수행하는 클래스"""
    
    PROMPT_TEMPLATE = """<|start_header_id|>system<|end_header_id|>

You are a helpful assistant for translating between standard Korean and regional dialects.
<|eot_id|><|start_header_id|>user<|end_header_id|>

{prompt}
<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
    
    REGIONS = {
        'jeju': '제주',
        'chungcheong': '충청',
        'gangwon': '강원',
        'gyeongsang': '경상',
        'jeonla': '전라'
    }
    
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
            n_ctx: 컨텍스트 윈도우 크기 (기본값: 512, 짧은 번역에 충분)
            n_gpu_layers: GPU에 올릴 레이어 수 (0이면 CPU만 사용)
            temperature: 샘플링 temperature (기본값: 0.3, 낮을수록 더 결정적)
            top_p: nucleus sampling threshold (기본값: 0.95)
            top_k: top-k sampling (기본값: 40)
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
            region: 목표 방언 지역 (jeju, chungcheong, gangwon, gyeongsang, jeonla)
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
            감지된 방언 종류 (standard, jeju, chungcheong, gangwon, gyeongsang, jeonla)
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


def translate_to_jeju(text):
    """
    제주 방언 번역기

    Args:
        text: 번역할 문장

    Returns:
        str: 제주 방언으로 번역된 문장
    """
    # 모델 파일 경로 설정
    MODEL_PATH = "static/models/jeju-dialect-model.gguf"
    
    # 번역기 초기화
    translator = JejumaTranslator(
        model_path=MODEL_PATH,
        n_ctx=2048,
        n_gpu_layers=0,  # GPU 사용시 적절한 값으로 변경
        temperature=0.3,
        top_p=0.9
    )

    jeju_result = translator.standard_to_dialect(text, region='jeju')

    return jeju_result


async def translate_to_jeju_async(text: str) -> str:
    """
    제주어 번역 (비동기 래퍼)

    동기 함수인 translate_to_jeju()를 asyncio.to_thread()로 래핑하여
    async 컨텍스트에서 안전하게 호출할 수 있도록 합니다.

    Args:
        text: 번역할 문장

    Returns:
        str: 제주어로 번역된 문장
    """
    import asyncio
    return await asyncio.to_thread(translate_to_jeju, text)
