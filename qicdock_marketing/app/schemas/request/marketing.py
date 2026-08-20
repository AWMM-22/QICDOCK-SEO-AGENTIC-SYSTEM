from pydantic import BaseModel, Field, EmailStr
from uuid import UUID
from typing import Optional
from app.db.models.marketing import ContentType


class MarketingGenerateRequest(BaseModel):
    organization_id: UUID
    user_id: Optional[UUID] = None
    product_ids: list[UUID] = Field(default_factory=list, min_length=1)
    marketing_goal_id: Optional[UUID] = None
    goal: str = Field(..., min_length=10, max_length=1000)
    platforms: list[str] = Field(default_factory=list)
    content_types: list[ContentType] = Field(default_factory=list)
    quantity: int = Field(default=5, ge=1, le=20)
    email: Optional[EmailStr] = None
    date_range: Optional[dict] = None
    meta: dict = Field(default_factory=dict)


class MarketingStrategyRequest(BaseModel):
    organization_id: UUID
    product_ids: list[UUID] = Field(default_factory=list, min_length=1)
    goal: str = Field(..., min_length=10, max_length=1000)
    platforms: list[str] = Field(default_factory=list)
    content_types: list[ContentType] = Field(default_factory=list)
    quantity: int = Field(default=5, ge=1, le=20)


class ContentInstagramRequest(BaseModel):
    organization_id: UUID
    product_id: UUID
    content_type: ContentType = Field(default=ContentType.POST)
    topic: str = Field(..., min_length=5, max_length=200)
    angle: Optional[str] = None
    hook: Optional[str] = None
    quantity: int = Field(default=1, ge=1, le=10)


class ContentReelRequest(BaseModel):
    organization_id: UUID
    product_id: UUID
    topic: str = Field(..., min_length=5, max_length=200)
    duration: int = Field(default=15, ge=5, le=60)
    hook: Optional[str] = None
    quantity: int = Field(default=1, ge=1, le=5)


class ContentStoryRequest(BaseModel):
    organization_id: UUID
    product_id: UUID
    topic: str = Field(..., min_length=5, max_length=200)
    sequence_length: int = Field(default=5, ge=3, le=10)
    quantity: int = Field(default=1, ge=1, le=5)


class ContentImageRequest(BaseModel):
    organization_id: UUID
    product_id: UUID
    prompt: str = Field(..., min_length=10, max_length=1000)
    aspect_ratio: str = Field(default="4:5", pattern="^(1:1|4:5|9:16|16:9)$")
    reference_image_url: Optional[str] = None
    number_of_images: int = Field(default=1, ge=1, le=4)


class KnowledgeIngestRequest(BaseModel):
    organization_id: UUID
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=10)
    source_type: str = Field(..., pattern="^(document|webpage|pdf|faq|manual|brand_guide)$")
    source_url: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class ProductCreateRequest(BaseModel):
    organization_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    short_description: Optional[str] = None
    features: list[str] = Field(default_factory=list)
    benefits: list[str] = Field(default_factory=list)
    specifications: dict = Field(default_factory=dict)
    price: Optional[float] = None
    currency: str = Field(default="USD", pattern="^[A-Z]{3}$")
    sku: Optional[str] = None
    category: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    product_url: Optional[str] = None
    usp: list[str] = Field(default_factory=list)
    target_audience: Optional[str] = None
    pain_points_solved: list[str] = Field(default_factory=list)
    use_cases: list[str] = Field(default_factory=list)
    emotional_benefits: list[str] = Field(default_factory=list)
    functional_benefits: list[str] = Field(default_factory=list)
    differentiators: list[str] = Field(default_factory=list)