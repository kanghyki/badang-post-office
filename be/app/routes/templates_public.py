"""
템플릿 API 라우터 (프로덕션용)

프로덕션 환경에서 사용하는 템플릿 조회 API만 제공합니다.
"""

from fastapi import APIRouter, HTTPException, Depends
from app.services import template_service
from app.models.template import (
    Template,
    TemplateListResponse,
    TemplateResponse,
)
from app.utils.url import convert_static_path_to_url
from app.dependencies.auth import get_current_user
from app.database.models import User

router = APIRouter(
    prefix="/v1/templates",
    tags=["Templates"]
)


@router.get("", response_model=TemplateListResponse)
def get_templates(current_user: User = Depends(get_current_user)):
    """
    메모리에 로드된 모든 템플릿 목록을 조회합니다.
    
    인증된 사용자만 접근 가능합니다.
    """
    templates = template_service.get_all_templates()
    
    # Template 모델을 API 응답용 TemplateResponse 모델로 변환
    templates_response = [TemplateResponse.from_template(t) for t in templates]
    
    return TemplateListResponse(templates=templates_response)


@router.get("/{template_id}", response_model=Template)
def get_template_detail(template_id: str, current_user: User = Depends(get_current_user)):
    """
    특정 템플릿의 상세 정보를 조회합니다.
    
    인증된 사용자만 접근 가능합니다.
    """
    template = template_service.get_template_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="템플릿을 찾을 수 없습니다.")
    
    # template_image_path를 보안 URL로 변환
    template_dict = template.model_dump()
    template_dict["template_image_path"] = convert_static_path_to_url(template.template_image_path)
    
    return Template(**template_dict)
