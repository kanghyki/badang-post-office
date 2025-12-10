"""
텍스트 줄바꿈 유틸리티

폰트와 max_width, max_height를 고려하여 텍스트를 자동 줄바꿈합니다.
"""

from typing import Optional, List
from PIL import ImageFont


class TextWrapper:
    """폰트 기반 텍스트 자동 줄바꿈 및 범위 제한"""

    def __init__(
        self,
        font: ImageFont.FreeTypeFont,
        max_width: int,
        max_height: Optional[int] = None,
        line_height: int = 34  # 실제 줄 높이 (픽셀)
    ):
        """
        TextWrapper 초기화

        Args:
            font: PIL ImageFont 객체
            max_width: 최대 너비 (픽셀)
            max_height: 최대 높이 (픽셀, 선택)
            line_height: 줄 높이 (픽셀)
        """
        self.font = font
        self.max_width = max_width
        self.max_height = max_height
        self.line_height = line_height
        self.font_size = font.size if hasattr(font, 'size') else 28

    def wrap(self, text: str) -> str:
        """
        텍스트를 max_width와 max_height에 맞춰 줄바꿈합니다.

        Args:
            text: 원본 텍스트

        Returns:
            줄바꿈된 텍스트 (\\n으로 구분), max_height 초과 시 잘림
        """
        # 1. 사용자 개행 먼저 처리
        paragraphs = text.split('\n')
        all_lines = []

        # 2. 각 문단을 max_width에 맞춰 자동 개행
        for paragraph in paragraphs:
            if not paragraph:
                all_lines.append('')
                continue
            
            wrapped_lines = self._wrap_line(paragraph)
            all_lines.extend(wrapped_lines)

        # 3. max_height 제한 적용
        if self.max_height:
            all_lines = self._limit_by_height(all_lines)

        return '\n'.join(all_lines)

    def _wrap_line(self, line: str) -> List[str]:
        """
        한 줄을 max_width에 맞춰 여러 줄로 나눕니다.
        단어가 잘리지 않도록 단어 단위로 개행합니다.

        Args:
            line: 개행되지 않은 한 줄

        Returns:
            줄바꿈된 여러 줄
        """
        lines = []
        current_line = ""
        words = line.split(' ')  # 공백 기준으로 단어 분리

        for i, word in enumerate(words):
            # 단어 앞에 공백 추가 (첫 단어 제외)
            test_word = word if i == 0 or not current_line else ' ' + word
            test_line = current_line + test_word
            
            bbox = self.font.getbbox(test_line)
            text_width = bbox[2] - bbox[0]

            if text_width <= self.max_width:
                current_line = test_line
            else:
                # 현재 줄에 아무것도 없으면 단어가 너무 긴 경우 -> 강제로 추가
                if not current_line:
                    current_line = word
                else:
                    # 현재 줄을 저장하고 다음 줄 시작
                    lines.append(current_line)
                    current_line = word

        if current_line:
            lines.append(current_line)

        return lines

    def _limit_by_height(self, lines: List[str]) -> List[str]:
        """
        줄 수를 max_height에 맞춰 제한합니다.

        Args:
            lines: 전체 줄 리스트

        Returns:
            높이 제한이 적용된 줄 리스트
        """
        if not lines:
            return lines

        max_lines = max(1, self.max_height // self.line_height)

        if len(lines) > max_lines:
            # 마지막 줄에 '...' 추가
            limited_lines = lines[:max_lines]
            if limited_lines:
                limited_lines[-1] = limited_lines[-1].rstrip() + '...'
            return limited_lines

        return lines
