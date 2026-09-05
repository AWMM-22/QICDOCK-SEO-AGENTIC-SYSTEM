from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from enum import Enum


class Platform(str, Enum):
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"


class ContentType(str, Enum):
    SINGLE_IMAGE = "single_image"
    CAROUSEL = "carousel"
    REEL = "reel"
    STORY = "story"
    STORY_SEQUENCE = "story_sequence"
    PRODUCT_SHOWCASE = "product_showcase"
    EDUCATIONAL = "educational"
    PROBLEM_SOLUTION = "problem_solution"
    COMPARISON = "comparison"
    COMMUNITY = "community"
    UGC_STYLE = "ugc_style"
    PROMOTIONAL = "promotional"
    TEXT_POST = "text_post"
    IMAGE_POST = "image_post"
    DOCUMENT_CAROUSEL = "document_carousel"
    BRAND_STORY = "brand_story"
    INDUSTRY_INSIGHT = "industry_insight"
    CASE_STUDY = "case_study"
    PRODUCT_INSIGHT = "product_insight"


class PlanStatus(str, Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    READY = "ready"
    PARTIAL = "partial"
    FAILED = "failed"


class EntryStatus(str, Enum):
    PLANNED = "planned"
    QUEUED = "queued"
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"
    RETRYING = "retrying"
    SKIPPED = "skipped"
    REGENERATING = "regenerating"


class ImageStatus(str, Enum):
    NOT_REQUESTED = "not_requested"
    QUEUED = "queued"
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"


class ReviewStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    NEEDS_REVISION = "needs_revision"
    FAILED = "failed"


class JobType(str, Enum):
    CALENDAR_PLAN = "calendar_plan"
    CONTENT_RECOMMENDATION = "content_recommendation"
    REVIEW = "review"
    IMAGE_GENERATION = "image_generation"
    REGENERATE_ENTRY = "regenerate_entry"


class JobStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class CreatePlanRequest(BaseModel):
    start_date: date
    end_date: date
    platforms: List[Platform]
    objective: Optional[str] = None
    additional_instructions: Optional[str] = None

    @field_validator("platforms")
    @classmethod
    def at_least_one_platform(cls, v):
        if not v:
            raise ValueError("At least one platform must be selected")
        return v


class CreatePlanResponse(BaseModel):
    plan_id: int
    status: PlanStatus


class PlanResponse(BaseModel):
    plan_id: int
    project_id: int
    start_date: date
    end_date: date
    objective: Optional[str] = None
    status: PlanStatus
    strategy_summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class CalendarEntryBase(BaseModel):
    date: date
    platform: Platform
    content_type: Optional[ContentType] = None
    status: EntryStatus = EntryStatus.PLANNED
    title: Optional[str] = None
    objective: Optional[str] = None
    content_pillar: Optional[str] = None
    product: Optional[str] = None
    audience: Optional[str] = None
    hook: Optional[str] = None
    concept: Optional[str] = None
    caption_direction: Optional[str] = None
    cta: Optional[str] = None
    visual_direction: Optional[str] = None
    image_prompt: Optional[str] = None
    reason: Optional[str] = None
    sequence_position: Optional[int] = None
    campaign_thread: Optional[str] = None
    follows_entry: Optional[str] = None
    supports_entry: Optional[str] = None
    review_status: ReviewStatus = ReviewStatus.PENDING
    review_score: Optional[float] = None
    review_issues: Optional[List[str]] = None
    review_corrections: Optional[List[str]] = None
    review_attempts: int = 0
    error: Optional[str] = None
    image_status: ImageStatus = ImageStatus.NOT_REQUESTED
    image_url: Optional[str] = None
    image_prompt_used: Optional[str] = None
    image_prompts: Optional[List[str]] = None
    image_urls: Optional[List[str]] = None
    image_prompts_used: Optional[List[str]] = None


class CalendarEntryResponse(CalendarEntryBase):
    id: int
    plan_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CalendarResponse(BaseModel):
    plan_id: int
    start_date: date
    end_date: date
    strategy_summary: Optional[str] = None
    recommended_frequency: Dict[str, str] = {}
    entries: List[CalendarEntryResponse]
    total_days: int
    planned_posts: int
    empty_days: int


class DayRecommendationResponse(BaseModel):
    id: Optional[int] = None
    date: date
    platform: Platform
    content_type: Optional[ContentType] = None
    title: Optional[str] = None
    objective: Optional[str] = None
    audience: Optional[str] = None
    product: Optional[str] = None
    content_pillar: Optional[str] = None
    reason: Optional[str] = None
    hook: Optional[str] = None
    concept: Optional[str] = None
    caption_direction: Optional[str] = None
    cta: Optional[str] = None
    visual_direction: Optional[str] = None
    image_prompt: Optional[str] = None
    review_status: ReviewStatus
    review_score: Optional[float] = None
    review_issues: Optional[List[str]] = None
    review_corrections: Optional[List[str]] = None
    image_status: ImageStatus
    image_url: Optional[str] = None
    image_prompt_used: Optional[str] = None
    image_prompts: Optional[List[str]] = None
    image_urls: Optional[List[str]] = None
    image_prompts_used: Optional[List[str]] = None
    status: EntryStatus
    error: Optional[str] = None
    is_empty: bool = False
    empty_reason: Optional[str] = None


class RegenerateRequest(BaseModel):
    feedback: Optional[str] = None


class RegenerateResponse(BaseModel):
    date: str
    status: EntryStatus


class ImageGenerateRequest(BaseModel):
    prompt: Optional[str] = None
    aspect_ratio: Optional[str] = "1:1"
    model: Optional[str] = None
    quality: Optional[str] = "standard"
    n: int = 1


class ImageGenerateResponse(BaseModel):
    image_status: ImageStatus
    image_url: Optional[str] = None
    image_prompt_used: Optional[str] = None
    image_urls: Optional[List[str]] = None
    image_prompts_used: Optional[List[str]] = None


class BrandKnowledgeUpdateRequest(BaseModel):
    force_reingest: bool = False


class BrandKnowledgeUpdateResponse(BaseModel):
    success: bool
    message: str
    version: Optional[int] = None


class ErrorResponse(BaseModel):
    status: str = "error"
    component: str
    error_code: str
    message: str
    recoverable: bool
    retry_after: Optional[int] = None


class HealthResponse(BaseModel):
    status: str
    database: str
    chromadb: str
    llm_configured: bool
    image_provider_configured: bool