"""
Postcard Helper Functions

편지 관련 공통 유틸리티 함수들
"""

from typing import Optional, Dict


def extract_main_text(text_contents: Optional[Dict[str, str]]) -> str:
    """
    text_contents에서 메인 텍스트 추출
    
    main_text 키를 우선 사용하고, 없으면 첫 번째 값을 반환
    
    Args:
        text_contents: 텍스트 컨텐츠 딕셔너리
        
    Returns:
        추출된 텍스트 (없으면 빈 문자열)
    """
    if not text_contents:
        return ""
    
    return (
        text_contents.get("main_text")
        or next(iter(text_contents.values()), "")
    )
