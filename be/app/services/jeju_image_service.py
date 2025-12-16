"""
제주 스타일 애니메이션 이미지 생성 서비스
- gpt-image-1 모델 사용 (이미지 직접 입력)
- 원본 이미지 + 프롬프트로 제주 스타일 변환
"""

import base64
import aiohttp
import io
import time
import logging
from typing import Optional
from openai import OpenAI
from app.config import settings

logger = logging.getLogger(__name__)


class JejuImageService:
    """gpt-image-1 기반 제주 스타일 이미지 생성 서비스"""

    def __init__(self):
        """OpenAI 클라이언트 초기화"""
        if not settings.openai_api_key:
            raise ValueError("OpenAI API 키가 필요합니다.")

        self.client = OpenAI(api_key=settings.openai_api_key)
        self.image_model = "gpt-image-1"

    def _create_jeju_style_prompt(self, custom_prompt: str = "") -> str:
        """제주 스타일 프롬프트 생성"""

        jeju_style = """Transform this image into a warm, soft, high-quality Japanese animation-style illustration with Jeju Island theme.

STYLE REQUIREMENTS:
- Render in cozy Studio Ghibli-inspired style
- Use gentle lighting and heartwarming pastel colors
- Apply soft gradients and detailed brushwork
- Create peaceful, serene Jeju atmosphere

JEJU ELEMENTS TO ADD:
- 한라산 (Hallasan mountain) silhouette in background if outdoor
- 돌하르방 (Stone grandfather statues) in empty spaces
- 유채꽃 (Canola flowers) - bright yellow fields
- 감귤/한라봉 (Jeju tangerines) decorations
- 동백꽃 (Camellia flowers) accents
- 돌담길 (Traditional stone walls)
- 푸른 제주 바다 (Jeju blue ocean) if fits context

STRICT RULES:
1. Keep ALL original composition, poses, people, animals exactly as they appear
2. Every living being must be wearing a cute tangerine hat (small Jeju-style citrus hat)
3. Do NOT change layout, number, or identity of any living being
4. Only change visual STYLE and add small Jeju-themed decorative details
5. Maintain original background structure, just stylize it
6. Add cute tangerine (감귤) elements near living beings
"""

        if custom_prompt.strip():
            jeju_style += f"\n\nADDITIONAL INSTRUCTIONS:\n{custom_prompt}"

        return jeju_style

    async def generate_jeju_style_image(
        self,
        image_bytes: bytes,
        custom_prompt: str = "",
        size: str = "1024x1024"
    ) -> bytes:
        """원본 이미지를 제주 스타일 애니메이션으로 변환"""

        start_time = time.time()
        logger.info(f"🎨 제주 스타일 변환 시작 (크기: {len(image_bytes)} bytes)")

        prompt = self._create_jeju_style_prompt(custom_prompt)

        # 원본 이미지를 BytesIO로 감싸서 tuple 형태로 전달
        image_file = io.BytesIO(image_bytes)

        try:
            # gpt-image-1 images.edit() API - 이미지 직접 입력!
            response = self.client.images.edit(
                model=self.image_model,
                image=("image.png", image_file, "image/png"),  # 🖼️ tuple 형태로 전달
                prompt=prompt,
                size=size,
                n=1
            )

            elapsed = time.time() - start_time

            # 결과 처리
            image_data = response.data[0]

            if hasattr(image_data, 'b64_json') and image_data.b64_json:
                result = base64.standard_b64decode(image_data.b64_json)
            elif hasattr(image_data, 'url') and image_data.url:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
                    async with session.get(image_data.url) as http_response:
                        if http_response.status == 200:
                            result = await http_response.read()
                        else:
                            raise Exception(f"이미지 다운로드 실패: HTTP {http_response.status}")
            else:
                raise Exception("이미지 응답 형식을 알 수 없습니다.")

            logger.info(f"✅ 제주 스타일 변환 완료 ({elapsed:.1f}초)")
            return result

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"❌ 제주 스타일 변환 실패 ({elapsed:.1f}초): {str(e)}")
            raise
