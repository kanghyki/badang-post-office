"""
이미지 효과 처리 유틸리티

다양한 이미지 효과를 적용하는 함수들을 제공합니다.
"""

from typing import Dict, Any, Tuple, Optional
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw


def apply_effects(image: Image.Image, effects: Dict[str, Any]) -> Image.Image:
    """
    이미지에 여러 효과를 적용합니다.
    
    Args:
        image: 원본 PIL Image 객체
        effects: 적용할 효과들의 딕셔너리
            - grayscale: bool (흑백 변환)
            - sepia: bool (세피아 톤)
            - blur: float (0.0 ~ 10.0, 블러 강도)
            - brightness: float (0.0 ~ 2.0, 1.0이 원본)
            - contrast: float (0.0 ~ 2.0, 1.0이 원본)
            - saturation: float (0.0 ~ 2.0, 1.0이 원본)
            - sharpness: float (0.0 ~ 2.0, 1.0이 원본)
            - rounded_corners: int (둥근 모서리 반경)
    
    Returns:
        효과가 적용된 PIL Image 객체
    """
    if not effects:
        return image
    
    result = image.copy()
    
    # 흑백 변환
    if effects.get('grayscale', False):
        result = apply_grayscale(result)
    
    # 세피아 톤
    if effects.get('sepia', False):
        result = apply_sepia(result)
    
    # 블러 효과
    blur_amount = effects.get('blur')
    if blur_amount is not None and blur_amount > 0:
        result = apply_blur(result, blur_amount)
    
    # 밝기 조정
    brightness = effects.get('brightness')
    if brightness is not None and brightness != 1.0:
        result = apply_brightness(result, brightness)
    
    # 대비 조정
    contrast = effects.get('contrast')
    if contrast is not None and contrast != 1.0:
        result = apply_contrast(result, contrast)
    
    # 채도 조정
    saturation = effects.get('saturation')
    if saturation is not None and saturation != 1.0:
        result = apply_saturation(result, saturation)
    
    # 선명도 조정
    sharpness = effects.get('sharpness')
    if sharpness is not None and sharpness != 1.0:
        result = apply_sharpness(result, sharpness)
    
    # 둥근 모서리
    rounded_corners = effects.get('rounded_corners')
    if rounded_corners is not None and rounded_corners > 0:
        result = apply_rounded_corners(result, rounded_corners)
    
    return result


def apply_grayscale(image: Image.Image) -> Image.Image:
    """
    이미지를 흑백으로 변환합니다.
    
    Args:
        image: 원본 PIL Image 객체
    
    Returns:
        흑백으로 변환된 PIL Image 객체 (RGB 모드 유지)
    """
    grayscale = image.convert('L')
    return grayscale.convert('RGB')


def apply_sepia(image: Image.Image) -> Image.Image:
    """
    이미지에 세피아 톤을 적용합니다.
    
    Args:
        image: 원본 PIL Image 객체
    
    Returns:
        세피아 톤이 적용된 PIL Image 객체
    """
    # RGB 모드로 변환
    img = image.convert('RGB')
    width, height = img.size
    pixels = img.load()
    
    for py in range(height):
        for px in range(width):
            r, g, b = pixels[px, py]
            
            # 세피아 톤 계산 공식
            tr = int(0.393 * r + 0.769 * g + 0.189 * b)
            tg = int(0.349 * r + 0.686 * g + 0.168 * b)
            tb = int(0.272 * r + 0.534 * g + 0.131 * b)
            
            # 255를 초과하는 값은 255로 제한
            pixels[px, py] = (min(tr, 255), min(tg, 255), min(tb, 255))
    
    return img


def apply_blur(image: Image.Image, radius: float) -> Image.Image:
    """
    이미지에 블러 효과를 적용합니다.
    
    Args:
        image: 원본 PIL Image 객체
        radius: 블러 반경 (0.0 ~ 10.0 권장)
    
    Returns:
        블러가 적용된 PIL Image 객체
    """
    return image.filter(ImageFilter.GaussianBlur(radius=radius))


def apply_brightness(image: Image.Image, factor: float) -> Image.Image:
    """
    이미지의 밝기를 조정합니다.
    
    Args:
        image: 원본 PIL Image 객체
        factor: 밝기 계수 (0.0 = 검은색, 1.0 = 원본, 2.0 = 매우 밝음)
    
    Returns:
        밝기가 조정된 PIL Image 객체
    """
    enhancer = ImageEnhance.Brightness(image)
    return enhancer.enhance(factor)


def apply_contrast(image: Image.Image, factor: float) -> Image.Image:
    """
    이미지의 대비를 조정합니다.
    
    Args:
        image: 원본 PIL Image 객체
        factor: 대비 계수 (0.0 = 회색, 1.0 = 원본, 2.0 = 높은 대비)
    
    Returns:
        대비가 조정된 PIL Image 객체
    """
    enhancer = ImageEnhance.Contrast(image)
    return enhancer.enhance(factor)


def apply_saturation(image: Image.Image, factor: float) -> Image.Image:
    """
    이미지의 채도를 조정합니다.
    
    Args:
        image: 원본 PIL Image 객체
        factor: 채도 계수 (0.0 = 흑백, 1.0 = 원본, 2.0 = 높은 채도)
    
    Returns:
        채도가 조정된 PIL Image 객체
    """
    enhancer = ImageEnhance.Color(image)
    return enhancer.enhance(factor)


def apply_sharpness(image: Image.Image, factor: float) -> Image.Image:
    """
    이미지의 선명도를 조정합니다.
    
    Args:
        image: 원본 PIL Image 객체
        factor: 선명도 계수 (0.0 = 흐림, 1.0 = 원본, 2.0 = 매우 선명)
    
    Returns:
        선명도가 조정된 PIL Image 객체
    """
    enhancer = ImageEnhance.Sharpness(image)
    return enhancer.enhance(factor)


def apply_rounded_corners(image: Image.Image, radius: int) -> Image.Image:
    """
    이미지에 둥근 모서리를 적용합니다.
    
    Args:
        image: 원본 PIL Image 객체
        radius: 모서리 반경 (픽셀)
    
    Returns:
        둥근 모서리가 적용된 PIL Image 객체
    """
    # RGBA 모드로 변환
    img = image.convert('RGBA')
    width, height = img.size
    
    # 마스크 생성
    mask = Image.new('L', (width, height), 0)
    draw = ImageDraw.Draw(mask)
    
    # 둥근 사각형 그리기
    draw.rounded_rectangle([(0, 0), (width, height)], radius=radius, fill=255)
    
    # 마스크 적용
    img.putalpha(mask)
    
    # 흰색 배경에 합성
    background = Image.new('RGBA', (width, height), (255, 255, 255, 255))
    background.paste(img, (0, 0), img)
    
    return background.convert('RGB')




