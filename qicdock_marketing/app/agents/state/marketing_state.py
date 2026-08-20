from typing import Optional, Any
from pydantic import BaseModel, Field
from uuid import UUID
from app.db.models.agents import AgentType, AgentRunStatus
from app.db.models.marketing import ContentType, ContentStatus


class MarketingRequest(BaseModel):
    organization_id: UUID
    user_id: Optional[UUID] = None
    product_ids: list[UUID] = Field(default_factory=list)
    marketing_goal_id: Optional[UUID] = None
    goal: str
    platforms: list[str] = Field(default_factory=list)
    content_types: list[ContentType] = Field(default_factory=list)
    quantity: int = 5
    email: Optional[str] = None
    date_range: Optional[dict] = None
    meta: dict = Field(default_factory=dict)


class BrandContext(BaseModel):
    brand_profile_id: Optional[UUID] = None
    brand_story: Optional[str] = None
    brand_voice: Optional[str] = None
    tone: Optional[str] = None
    target_audience: Optional[str] = None
    positioning: Optional[str] = None
    words_to_use: list[str] = Field(default_factory=list)
    words_to_avoid: list[str] = Field(default_factory=list)
    visual_style: Optional[str] = None
    colors: dict = Field(default_factory=dict)
    usp: list[str] = Field(default_factory=list)
    guidelines: list[dict] = Field(default_factory=list)


class ProductContext(BaseModel):
    product_id: UUID
    name: str
    description: Optional[str] = None
    features: list[str] = Field(default_factory=list)
    benefits: list[str] = Field(default_factory=list)
    specifications: dict = Field(default_factory=dict)
    price: Optional[float] = None
    currency: str = "USD"
    images: list[str] = Field(default_factory=list)
    usp: list[str] = Field(default_factory=list)
    target_audience: Optional[str] = None
    pain_points_solved: list[str] = Field(default_factory=list)
    use_cases: list[str] = Field(default_factory=list)
    emotional_benefits: list[str] = Field(default_factory=list)
    functional_benefits: list[str] = Field(default_factory=list)
    differentiators: list[str] = Field(default_factory=list)


class AudienceInsights(BaseModel):
    audience: str
    pain_points: list[str] = Field(default_factory=list)
    motivations: list[str] = Field(default_factory=list)
    objections: list[str] = Field(default_factory=list)
    buying_triggers: list[str] = Field(default_factory=list)
    demographics: dict = Field(default_factory=dict)
    psychographics: dict = Field(default_factory=dict)


class ResearchSourceItem(BaseModel):
    title: str
    url: str
    source: str
    summary: str
    relevance: Optional[str] = None
    published_at: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class ResearchData(BaseModel):
    sources: list[ResearchSourceItem] = Field(default_factory=list)
    trends: list[str] = Field(default_factory=list)
    consumer_insights: list[str] = Field(default_factory=list)
    industry_news: list[str] = Field(default_factory=list)
    search_trends: list[str] = Field(default_factory=list)


class CompetitorInsights(BaseModel):
    competitors: list[dict] = Field(default_factory=list)
    common_angles: list[str] = Field(default_factory=list)
    overused_angles: list[str] = Field(default_factory=list)
    content_gaps: list[str] = Field(default_factory=list)
    opportunities: list[str] = Field(default_factory=list)
    trending_formats: list[str] = Field(default_factory=list)
    potential_hooks: list[str] = Field(default_factory=list)


class ContentStrategyItem(BaseModel):
    platform: str
    format: ContentType
    objective: str
    topic: str
    audience: str
    angle: str
    hook: str
    cta: str
    priority: int = 1
    reasoning: str
    visual_requirement: Optional[str] = None
    hashtags: list[str] = Field(default_factory=list)


class ContentStrategy(BaseModel):
    items: list[ContentStrategyItem] = Field(default_factory=list)
    overall_theme: Optional[str] = None
    key_messages: list[str] = Field(default_factory=list)
    content_calendar: dict = Field(default_factory=dict)


class GeneratedContentItem(BaseModel):
    content_id: Optional[UUID] = None
    content_type: ContentType
    platform: str
    title: Optional[str] = None
    content: dict = Field(default_factory=dict)
    visual_concept: Optional[str] = None
    image_prompt: Optional[str] = None
    hashtags: list[str] = Field(default_factory=list)
    cta: Optional[str] = None
    status: ContentStatus = ContentStatus.GENERATED
    review_score: Optional[float] = None
    review_feedback: Optional[str] = None


class GeneratedContent(BaseModel):
    items: list[GeneratedContentItem] = Field(default_factory=list)


class GeneratedImage(BaseModel):
    asset_id: Optional[UUID] = None
    content_item_id: Optional[UUID] = None
    url: str
    prompt: str
    provider: str
    model: str
    aspect_ratio: str
    width: Optional[int] = None
    height: Optional[int] = None
    review_status: str = "pending"
    review_score: Optional[float] = None


class GeneratedImages(BaseModel):
    images: list[GeneratedImage] = Field(default_factory=list)


class ReviewResultItem(BaseModel):
    content_item_id: UUID
    reviewer_agent_type: AgentType
    approved: bool
    score: Optional[float] = None
    issues: list[str] = Field(default_factory=list)
    suggested_changes: list[str] = Field(default_factory=list)
    review_details: dict = Field(default_factory=dict)


class ReviewResults(BaseModel):
    results: list[ReviewResultItem] = Field(default_factory=list)
    all_approved: bool = False
    revision_needed: bool = False


class MarketingState(BaseModel):
    request: MarketingRequest
    organization_id: UUID
    user_id: Optional[UUID] = None
    product_ids: list[UUID] = Field(default_factory=list)
    marketing_goal_id: Optional[UUID] = None
    brand_context: Optional[BrandContext] = None
    product_context: list[ProductContext] = Field(default_factory=list)
    audience_insights: Optional[AudienceInsights] = None
    research: Optional[ResearchData] = None
    competitor_insights: Optional[CompetitorInsights] = None
    trend_insights: Optional[CompetitorInsights] = None
    content_strategy: Optional[ContentStrategy] = None
    generated_content: Optional[GeneratedContent] = None
    generated_images: Optional[GeneratedImages] = None
    review_results: Optional[ReviewResults] = None
    revision_count: int = 0
    final_report: Optional[str] = None
    email_status: str = "pending"
    errors: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    current_agent: Optional[AgentType] = None
    agent_runs: list[dict] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True