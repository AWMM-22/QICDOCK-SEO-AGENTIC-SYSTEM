from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import Optional

from app.db.session.database import get_async_session
from app.db.models.marketing import ContentItem, ContentType, ContentStatus
from app.schemas.request.marketing import (
    ContentInstagramRequest,
    ContentReelRequest,
    ContentStoryRequest,
    ContentImageRequest,
)
from app.schemas.response.marketing import ContentItemResponse, ErrorResponse


router = APIRouter()


@router.post("/content/instagram", response_model=list[ContentItemResponse])
async def generate_instagram_content(
    request: ContentInstagramRequest,
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(
        select(ContentItem).where(ContentItem.id == request.product_id)
    )
    # Placeholder - actual implementation would call the Instagram agent
    return []


@router.post("/content/reel", response_model=list[ContentItemResponse])
async def generate_reel_content(
    request: ContentReelRequest,
    session: AsyncSession = Depends(get_async_session),
):
    return []


@router.post("/content/story", response_model=list[ContentItemResponse])
async def generate_story_content(
    request: ContentStoryRequest,
    session: AsyncSession = Depends(get_async_session),
):
    return []


@router.post("/content/image")
async def generate_marketing_image(
    request: ContentImageRequest,
    session: AsyncSession = Depends(get_async_session),
):
    return {
        "message": "Image generation endpoint - to be implemented",
        "request": request.model_dump(),
    }


@router.get("/content/{content_id}", response_model=ContentItemResponse)
async def get_content(
    content_id: UUID,
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(select(ContentItem).where(ContentItem.id == content_id))
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    return ContentItemResponse(
        id=content.id,
        content_type=content.content_type.value,
        platform=content.platform,
        title=content.title,
        content=content.content,
        status=content.status.value,
        review_score=content.review_score,
        created_at=content.created_at,
    )