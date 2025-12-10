"""
URL 변환 유틸리티

파일 경로를 보안 API URL로 변환하는 헬퍼 함수들
"""


def convert_static_path_to_url(file_path: str | None) -> str | None:
    """
    static 파일 경로를 보안 API URL로 변환
    
    Args:
        file_path: static 파일 경로 (예: static/uploads/2025/12/08/uuid.jpg)
        
    Returns:
        보안 API URL (예: /v1/files/static/uploads/2025/12/08/uuid.jpg)
        file_path가 None이면 None 반환
    """
    if not file_path:
        return None
    
    # static/ 접두사 제거 후 /v1/files/static/ 경로로 변환
    if file_path.startswith("static/"):
        path_without_static = file_path[7:]  # "static/" 제거
        return f"/v1/files/static/{path_without_static}"
    
    return file_path
