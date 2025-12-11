"""
템플릿 관리 API 라우터 (개발/운영용)

템플릿 JSON 파일을 생성/수정/삭제하는 관리용 엔드포인트를 제공합니다.

⚠️ 주의: 이 API는 프로덕션 환경에서 사용하지 않습니다 (env=dev일 때만 활성화).
템플릿 조회는 /v1/templates (Templates 태그)를 사용하세요.
"""

from fastapi import APIRouter, HTTPException
from app.services import template_service
from app.models.template import (
    Template,
    TemplateListResponse,
    TemplateResponse,
    TemplateUpdateRequest,
)

router = APIRouter(
    prefix="/v1/templates",
    tags=["Templates Management (개발/운영용)"]
)


@router.get("", response_model=TemplateListResponse)
def get_templates_dev():
    """
    메모리에 로드된 모든 템플릿 목록을 조회합니다 (개발용 - 인증 불필요).

    ⚠️ 주의: 이 엔드포인트는 개발 환경에서만 활성화됩니다.
    """
    templates = template_service.get_all_templates()

    # Template 모델을 API 응답용 TemplateResponse 모델로 변환
    templates_response = [TemplateResponse.from_template(t) for t in templates]

    return TemplateListResponse(templates=templates_response)


@router.get("/{template_id}", response_model=Template)
def get_template_detail_dev(template_id: str):
    """
    특정 템플릿의 상세 정보를 조회합니다 (개발용 - 인증 불필요).

    ⚠️ 주의: 이 엔드포인트는 개발 환경에서만 활성화됩니다.
    """
    template = template_service.get_template_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="템플릿을 찾을 수 없습니다.")

    return template


@router.post("", response_model=Template, status_code=201)
def create_template(template: Template):
    """
    새 템플릿을 생성하고 JSON 파일로 저장합니다.
    """
    # ID 중복 검사
    existing_template = template_service.get_template_by_id(template.id)
    if existing_template:
        raise HTTPException(
            status_code=409,
            detail=f"ID '{template.id}'를 가진 템플릿이 이미 존재합니다."
        )

    try:
        saved_template = template_service.save_template_to_disk(template)
        return saved_template
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"템플릿 저장 중 오류 발생: {str(e)}"
        )


@router.put("/{template_id}", response_model=Template)
def update_template(template_id: str, template: Template):
    """
    기존 템플릿을 수정하고 JSON 파일에 저장합니다.
    """
    # 기존 템플릿 확인
    existing_template = template_service.get_template_by_id(template_id)
    if not existing_template:
        raise HTTPException(
            status_code=404,
            detail=f"ID '{template_id}'인 템플릿을 찾을 수 없습니다."
        )

    # ID 일치 확인
    if template.id != template_id:
        raise HTTPException(
            status_code=400,
            detail="요청 본문의 템플릿 ID와 경로의 ID가 일치하지 않습니다."
        )

    try:
        saved_template = template_service.save_template_to_disk(template)
        return saved_template
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"템플릿 저장 중 오류 발생: {str(e)}"
        )


@router.delete("/{template_id}")
def delete_template(template_id: str):
    """
    템플릿을 삭제합니다 (JSON 파일 삭제).
    """
    # 기존 템플릿 확인
    existing_template = template_service.get_template_by_id(template_id)
    if not existing_template:
        raise HTTPException(
            status_code=404,
            detail=f"ID '{template_id}'인 템플릿을 찾을 수 없습니다."
        )

    try:
        success = template_service.delete_template_from_disk(template_id)
        if success:
            return {"message": f"템플릿 '{template_id}'가 성공적으로 삭제되었습니다."}
        else:
            raise HTTPException(
                status_code=500,
                detail="템플릿 삭제 중 오류가 발생했습니다."
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"템플릿 삭제 중 오류 발생: {str(e)}"
        )
