"""
엽서 제작 모듈

사진, 텍스트, 테두리를 조합하여 엽서를 만드는 PostcardMaker 클래스를 제공합니다.
"""

from typing import Optional, Dict, Any
from PIL import Image, ImageDraw
from app.services.postcards.font_manager import FontManager
from app.services.postcards.image_effects import apply_effects


class PostcardMaker:
    """한글 텍스트를 지원하는 Pillow 엽서 제작 클래스"""

    def __init__(
        self,
        width: int = 800,
        height: int = 1200,
        bg_color: str = 'white'
    ):
        """
        PostcardMaker 초기화

        Args:
            width: 캔버스 너비 (픽셀), 기본값 800
            height: 캔버스 높이 (픽셀), 기본값 1200
            bg_color: 배경색 (색상명 또는 16진수), 기본값 'white'
        """
        self.width = width
        self.height = height
        self.canvas = Image.new('RGB', (width, height), bg_color)
        self.draw = ImageDraw.Draw(self.canvas)
        self.font_manager = FontManager()

    def add_photo(
        self,
        image_path: str,
        x: int,
        y: int,
        max_width: Optional[int] = None,
        max_height: Optional[int] = None,
        effects: Optional[Dict[str, Any]] = None
    ) -> 'PostcardMaker':
        """
        사진을 엽서에 추가합니다 (contain 방식으로 리사이징하고 중앙 정렬).

        Args:
            image_path: 이미지 파일 경로
            x: 배치 영역 시작 X 좌표
            y: 배치 영역 시작 Y 좌표
            max_width: 최대 너비 (None이면 원본 크기 유지)
            max_height: 최대 높이 (None이면 원본 크기 유지)
            effects: 이미지 효과 설정 (grayscale, sepia, blur, brightness, contrast 등)

        Returns:
            self (메서드 체이닝 가능)

        Raises:
            FileNotFoundError: 이미지 파일을 찾을 수 없는 경우
            PIL.UnidentifiedImageError: 이미지 형식이 잘못된 경우
        """
        try:
            # 1단계: 이미지 로드
            image = Image.open(image_path)
            original_width, original_height = image.size

            # 2단계: 이미지 효과 적용
            if effects:
                image = apply_effects(image, effects)

            # 3단계: Contain 방식 크기 조정
            # max_width/max_height 값 검증 및 기본값 설정
            if max_width is None:
                max_width = original_width
            if max_height is None:
                max_height = original_height

            # 축소 비율 계산 (contain 방식: 가로/세로 중 더 작은 비율 선택)
            scale_x = max_width / original_width
            scale_y = max_height / original_height
            scale = min(scale_x, scale_y, 1.0)  # 1.0 이하로 제한 (자동 확대 방지)

            # 최종 크기 계산
            new_width = int(original_width * scale)
            new_height = int(original_height * scale)

            # resize() 사용하여 리사이징 (LANCZOS 필터로 품질 보장)
            resized_image = image.resize(
                (new_width, new_height),
                Image.Resampling.LANCZOS
            )

            # 4단계: 중앙 정렬 좌표 계산
            # 배치 영역(x, y, max_width, max_height)의 중앙에 이미지를 배치
            area_center_x = x + max_width / 2
            area_center_y = y + max_height / 2

            final_x = int(area_center_x - new_width / 2)
            final_y = int(area_center_y - new_height / 2)

            # 5단계: 캔버스에 붙여넣기 (알파 채널 고려)
            if resized_image.mode == 'RGBA':
                self.canvas.paste(resized_image, (final_x, final_y), resized_image)
            else:
                self.canvas.paste(resized_image, (final_x, final_y))

            return self

        except FileNotFoundError:
            raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")
        except Exception as e:
            raise Exception(f"이미지 로드 중 오류 발생: {e}")

    def add_text(
        self,
        text: str,
        x: int,
        y: int,
        font_id: Optional[str] = None,
        font_size: int = 28,
        color: str = 'black',
        align: str = 'center',
        max_width: Optional[int] = None,
        max_height: Optional[int] = None
    ) -> 'PostcardMaker':
        """
        한글 텍스트를 엽서에 추가합니다.
        max_width, max_height가 지정되면 박스 안에 텍스트를 제약합니다.

        Args:
            text: 텍스트 내용
            x: 배치 X 좌표 (텍스트 영역 시작점)
            y: 배치 Y 좌표
            font_id: 폰트 ID (None이면 기본 폰트 사용)
            font_size: 폰트 크기 (픽셀), 기본값 28
            color: 텍스트 색상 (색상명 또는 16진수), 기본값 'black'
            align: 정렬 방식 ('left', 'center', 'right'), 기본값 'center'
            max_width: 텍스트 영역 최대 너비 (픽셀)
            max_height: 텍스트 영역 최대 높이 (픽셀)

        Returns:
            self (메서드 체이닝 가능)
        """
        # 폰트 로드
        font = self.font_manager.get_font(font_id=font_id, size=font_size)

        # 정렬에 따른 anchor 설정
        anchor_map = {
            'left': 'lt',    # left-top
            'center': 'mt',  # middle-top
            'right': 'rt'    # right-top
        }
        anchor = anchor_map.get(align, 'mt')

        # max_width가 있으면 텍스트를 박스 안에 맞춤
        if max_width:
            # 정렬에 따라 X 좌표 조정
            if align == 'center':
                text_x = x + max_width // 2
            elif align == 'right':
                text_x = x + max_width
            else:
                text_x = x
        else:
            text_x = x

        # 텍스트 그리기
        self.draw.text(
            (text_x, y),
            text,
            fill=color,
            font=font,
            anchor=anchor
        )

        return self

    def add_border(
        self,
        thickness: int = 3,
        color: str = 'black',
        padding: int = 10
    ) -> 'PostcardMaker':
        """
        엽서에 테두리를 추가합니다.

        Args:
            thickness: 테두리 두께 (픽셀), 기본값 3
            color: 테두리 색상 (색상명 또는 16진수), 기본값 'black'
            padding: 테두리와 캔버스 가장자리 간 간격 (픽셀), 기본값 10

        Returns:
            self (메서드 체이닝 가능)
        """
        # 사각형 테두리 그리기
        self.draw.rectangle(
            [
                (padding, padding),
                (self.width - padding - 1, self.height - padding - 1)
            ],
            outline=color,
            width=thickness
        )

        return self

    def add_background_image(
        self,
        image_path: str,
        opacity: float = 1.0
    ) -> 'PostcardMaker':
        """
        배경 이미지를 설정합니다 (투명도 지원).

        Args:
            image_path: 배경 이미지 파일 경로
            opacity: 투명도 (0.0 ~ 1.0), 기본값 1.0 (완전 불투명)

        Returns:
            self (메서드 체이닝 가능)

        Raises:
            FileNotFoundError: 이미지 파일을 찾을 수 없는 경우
        """
        try:
            # 배경 이미지 로드 및 리사이징
            background = Image.open(image_path)
            background = background.resize((self.width, self.height), Image.Resampling.LANCZOS)

            # 투명도 적용
            if opacity < 1.0:
                # RGBA로 변환하여 알파 채널 조정
                background = background.convert('RGBA')
                alpha = background.split()[3]
                alpha = alpha.point(lambda p: int(p * opacity))
                background.putalpha(alpha)

                # 기존 캔버스와 합성
                temp_canvas = Image.new('RGBA', (self.width, self.height), (255, 255, 255, 255))
                temp_canvas.paste(background, (0, 0), background)
                self.canvas = temp_canvas.convert('RGB')
            else:
                self.canvas = background.convert('RGB')

            # Draw 객체 재생성
            self.draw = ImageDraw.Draw(self.canvas)

            return self

        except FileNotFoundError:
            raise FileNotFoundError(f"배경 이미지 파일을 찾을 수 없습니다: {image_path}")
        except Exception as e:
            raise Exception(f"배경 이미지 로드 중 오류 발생: {e}")

    def save(
        self,
        output_path: str,
        format: str = 'PNG',
        quality: int = 95
    ) -> None:
        """
        엽서를 이미지 파일로 저장합니다.

        Args:
            output_path: 저장할 파일 경로
            format: 이미지 형식 ('PNG', 'JPEG', 'JPG'), 기본값 'PNG'
            quality: JPEG 품질 (1-100), 기본값 95 (PNG는 무시됨)

        Raises:
            OSError: 파일 저장 중 오류 발생
        """
        try:
            # 형식 정규화
            format = format.upper()
            if format == 'JPG':
                format = 'JPEG'

            # 저장
            if format == 'JPEG':
                # JPEG는 RGB 모드 필요
                rgb_canvas = self.canvas.convert('RGB')
                rgb_canvas.save(output_path, format=format, quality=quality)
            else:
                self.canvas.save(output_path, format=format)

        except Exception as e:
            raise OSError(f"파일 저장 중 오류 발생: {e}")

    def get_canvas(self) -> Image.Image:
        """
        현재 캔버스 이미지를 반환합니다.

        Returns:
            PIL Image 객체
        """
        return self.canvas
