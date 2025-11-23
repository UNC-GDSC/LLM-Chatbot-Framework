"""Conversation templates API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.services.template_service import TemplateService, SYSTEM_TEMPLATES

router = APIRouter()


class TemplateCreate(BaseModel):
    """Request schema for creating a template."""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    system_prompt: Optional[str] = Field(None, max_length=5000)
    model_config: Optional[dict] = None
    is_public: bool = False


class TemplateUpdate(BaseModel):
    """Request schema for updating a template."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    system_prompt: Optional[str] = Field(None, max_length=5000)
    model_config: Optional[dict] = None
    is_public: Optional[bool] = None


class TemplateResponse(BaseModel):
    """Response schema for template."""

    id: str
    name: str
    description: Optional[str]
    system_prompt: Optional[str]
    model_config: Optional[dict]
    is_public: bool
    usage_count: int

    class Config:
        from_attributes = True


@router.post("/", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    data: TemplateCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> TemplateResponse:
    """Create a new conversation template."""
    template_service = TemplateService(db)

    template = await template_service.create_template(
        name=data.name,
        description=data.description,
        system_prompt=data.system_prompt,
        model_config=data.model_config,
        user_id=user_id,
        is_public=data.is_public,
    )

    return TemplateResponse.from_orm(template)


@router.get("/", response_model=List[TemplateResponse])
async def list_templates(
    public_only: bool = False,
    limit: int = 50,
    offset: int = 0,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> List[TemplateResponse]:
    """List available templates."""
    template_service = TemplateService(db)

    templates = await template_service.list_templates(
        user_id=user_id if not public_only else None,
        public_only=public_only,
        limit=limit,
        offset=offset,
    )

    return [TemplateResponse.from_orm(t) for t in templates]


@router.get("/system", response_model=List[dict])
async def get_system_templates() -> List[dict]:
    """Get pre-defined system templates."""
    return SYSTEM_TEMPLATES


@router.get("/popular", response_model=List[TemplateResponse])
async def get_popular_templates(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
) -> List[TemplateResponse]:
    """Get most popular public templates."""
    template_service = TemplateService(db)

    templates = await template_service.get_popular_templates(limit=limit)

    return [TemplateResponse.from_orm(t) for t in templates]


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> TemplateResponse:
    """Get a specific template."""
    template_service = TemplateService(db)

    template = await template_service.get_template(template_id, user_id)

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return TemplateResponse.from_orm(template)


@router.patch("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: str,
    data: TemplateUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> TemplateResponse:
    """Update a template."""
    template_service = TemplateService(db)

    template = await template_service.update_template(
        template_id=template_id,
        user_id=user_id,
        **data.dict(exclude_unset=True),
    )

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return TemplateResponse.from_orm(template)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a template."""
    template_service = TemplateService(db)

    deleted = await template_service.delete_template(template_id, user_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Template not found")


@router.post("/{template_id}/use", status_code=status.HTTP_200_OK)
async def use_template(
    template_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Increment template usage count."""
    template_service = TemplateService(db)

    await template_service.increment_usage(template_id)

    return {"message": "Template usage recorded"}
