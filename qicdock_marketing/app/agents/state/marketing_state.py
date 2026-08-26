import operator
from typing import Optional, Any, Annotated
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from app.db.models.agents import AgentType, AgentRunStatus
from app.db.models.marketing import ContentType, ContentStatus


def _merge_dict(old: Optional[dict], new: Optional[dict]) -> dict:
    """Reducer: shallow-merge dicts so parallel branches can both write metadata."""
    merged = dict(old or {})
    merged.update(new or {})
    return merged


def _merge_unique(old: Optional[list], new: Optional[list]) -> list:
    """Reducer: union of scalar lists (deduped) - safe for parallel error accumulation."""
    seen = set()
    out = []
    for item in list(old or []) + list(new or []):
        key = item if isinstance(item, (str, int, float, bool)) else str(item)
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


def _merge_agent_runs(old: Optional[list], new: Optional[list]) -> list:
    """Reducer: merge agent-run records by id; later status overwrites earlier."""
    by_id = {}
    order = []
    for run in list(old or []) + list(new or []):
        rid = run.get("id") if isinstance(run, dict) else None
        if rid is None:
            continue
        if rid not in by_id:
            order.append(rid)
        by_id[rid] = run
    return [by_id[i] for i in order]


def _last(old, new):
    """Reducer: last write wins."""
    return new if new is not None else old


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
    marketing_claims: list[str] = Field(default_factory=list)
    competitors: list[dict] = Field(default_factory=list)
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
    revision_count: int = 0


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


class ProductAnalysis(BaseModel):
    main_usp: str = ""
    secondary_usps: list[str] = Field(default_factory=list)
    pain_point_solved: str = ""
    ideal_use_case: str = ""
    target_audience: str = ""
    emotional_benefit: str = ""
    functional_benefit: str = ""
    differentiators: list[str] = Field(default_factory=list)
    marketing_angles: list[str] = Field(default_factory=list)
    content_opportunities: list[str] = Field(default_factory=list)


class InstagramCopyItem(BaseModel):
    hook: str
    caption: str
    cta: str
    hashtags: list[str] = Field(default_factory=list)
    visual_concept: str
    image_prompt: str
    carousel_slides: list[str] = Field(default_factory=list)


class InstagramContentSet(BaseModel):
    items: list[InstagramCopyItem] = Field(default_factory=list)


class ReelScene(BaseModel):
    duration: int
    visual: str
    voiceover: str
    text_overlay: str


class ReelCopyItem(BaseModel):
    hook: str
    duration: int
    script: str
    scenes: list[ReelScene] = Field(default_factory=list)
    caption: str
    cta: str
    hashtags: list[str] = Field(default_factory=list)
    cover_image_prompt: str


class ReelContentSet(BaseModel):
    items: list[ReelCopyItem] = Field(default_factory=list)


class StoryFrame(BaseModel):
    frame_type: str
    text: str
    interactive_element: Optional[str] = None


class StorySequenceItem(BaseModel):
    hook: str
    frames: list[StoryFrame] = Field(default_factory=list)
    cta: str
    caption: str = ""
    hashtags: list[str] = Field(default_factory=list)
    cover_image_prompt: str = ""


class StoryContentSet(BaseModel):
    items: list[StorySequenceItem] = Field(default_factory=list)


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
    pending_content_items: Annotated[list[dict], operator.add] = Field(default_factory=list)
    generated_images: Optional[GeneratedImages] = None
    review_results: Optional[ReviewResults] = None
    revision_count: int = 0
    final_report: Optional[str] = None
    email_status: str = "pending"
    errors: Annotated[list[str], _merge_unique] = Field(default_factory=list)
    metadata: Annotated[dict, _merge_dict] = Field(default_factory=dict)
    current_agent: Annotated[Optional[AgentType], _last] = None
    agent_runs: Annotated[list[dict], _merge_agent_runs] = Field(default_factory=list)

    model_config = ConfigDict(arbitrary_types_allowed=True)