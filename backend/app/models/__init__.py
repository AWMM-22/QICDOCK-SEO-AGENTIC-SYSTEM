from sqlalchemy import Column, Integer, String, Text, DateTime, Date, Enum as SQLEnum, ForeignKey, UniqueConstraint, Boolean, JSON
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum


Base = declarative_base()


class PlanStatus(str, enum.Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    READY = "ready"
    PARTIAL = "partial"
    FAILED = "failed"


class EntryStatus(str, enum.Enum):
    PLANNED = "planned"
    QUEUED = "queued"
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"
    RETRYING = "retrying"
    SKIPPED = "skipped"
    REGENERATING = "regenerating"


class JobType(str, enum.Enum):
    CALENDAR_PLAN = "calendar_plan"
    CONTENT_RECOMMENDATION = "content_recommendation"
    REVIEW = "review"
    IMAGE_GENERATION = "image_generation"
    REGENERATE_ENTRY = "regenerate_entry"


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class ImageStatus(str, enum.Enum):
    NOT_REQUESTED = "not_requested"
    QUEUED = "queued"
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"


class ReviewStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    NEEDS_REVISION = "needs_revision"
    FAILED = "failed"


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    plans = relationship("MarketingPlan", back_populates="project", cascade="all, delete-orphan")


class BrandKnowledgeVersion(Base):
    __tablename__ = "brand_knowledge_versions"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    version = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project")


class MarketingPlan(Base):
    __tablename__ = "marketing_plans"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    objective = Column(Text, nullable=True)
    status = Column(SQLEnum(PlanStatus), default=PlanStatus.DRAFT, nullable=False)
    strategy_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="plans")
    entries = relationship("CalendarEntry", back_populates="plan", cascade="all, delete-orphan")
    jobs = relationship("GenerationJob", back_populates="plan", cascade="all, delete-orphan")


class CalendarEntry(Base):
    __tablename__ = "calendar_entries"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("marketing_plans.id"), nullable=False)
    date = Column(Date, nullable=False)
    platform = Column(String(50), nullable=False)
    content_type = Column(String(50), nullable=True)
    status = Column(SQLEnum(EntryStatus), default=EntryStatus.PLANNED, nullable=False)
    title = Column(String(255), nullable=True)
    objective = Column(String(50), nullable=True)
    content_pillar = Column(String(50), nullable=True)
    product = Column(String(100), nullable=True)
    audience = Column(String(100), nullable=True)
    hook = Column(Text, nullable=True)
    concept = Column(Text, nullable=True)
    caption_direction = Column(Text, nullable=True)
    cta = Column(String(255), nullable=True)
    visual_direction = Column(Text, nullable=True)
    image_prompt = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)
    sequence_position = Column(Integer, nullable=True)
    campaign_thread = Column(String(100), nullable=True)
    follows_entry = Column(String(20), nullable=True)
    supports_entry = Column(String(20), nullable=True)
    review_status = Column(SQLEnum(ReviewStatus), default=ReviewStatus.PENDING, nullable=False)
    review_score = Column(Integer, nullable=True)
    review_issues = Column(JSON, nullable=True)
    review_corrections = Column(JSON, nullable=True)
    review_attempts = Column(Integer, default=0)
    error = Column(Text, nullable=True)
    image_status = Column(SQLEnum(ImageStatus), default=ImageStatus.NOT_REQUESTED, nullable=False)
    image_url = Column(Text, nullable=True)
    image_prompt_used = Column(Text, nullable=True)
    image_prompts = Column(JSON, nullable=True)
    image_urls = Column(JSON, nullable=True)
    image_prompts_used = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    plan = relationship("MarketingPlan", back_populates="entries")
    jobs = relationship("GenerationJob", back_populates="calendar_entry")

    __table_args__ = (
        UniqueConstraint("plan_id", "date", "platform", name="uq_plan_date_platform"),
    )


class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("marketing_plans.id"), nullable=False)
    calendar_entry_id = Column(Integer, ForeignKey("calendar_entries.id"), nullable=True)
    job_type = Column(SQLEnum(JobType), nullable=False)
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING, nullable=False)
    attempts = Column(Integer, default=0)
    payload = Column(JSON, nullable=True)
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    plan = relationship("MarketingPlan", back_populates="jobs")
    calendar_entry = relationship("CalendarEntry", back_populates="jobs")


class RecommendationVersion(Base):
    __tablename__ = "recommendation_versions"

    id = Column(Integer, primary_key=True, index=True)
    calendar_entry_id = Column(Integer, ForeignKey("calendar_entries.id"), nullable=False)
    version = Column(Integer, nullable=False)
    title = Column(String(255), nullable=True)
    objective = Column(String(50), nullable=True)
    content_pillar = Column(String(50), nullable=True)
    product = Column(String(100), nullable=True)
    audience = Column(String(100), nullable=True)
    hook = Column(Text, nullable=True)
    concept = Column(Text, nullable=True)
    caption_direction = Column(Text, nullable=True)
    cta = Column(String(255), nullable=True)
    visual_direction = Column(Text, nullable=True)
    image_prompt = Column(Text, nullable=True)
    image_prompts = Column(JSON, nullable=True)
    reason = Column(Text, nullable=True)
    sequence_position = Column(Integer, nullable=True)
    campaign_thread = Column(String(100), nullable=True)
    follows_entry = Column(String(20), nullable=True)
    supports_entry = Column(String(20), nullable=True)
    user_feedback = Column(Text, nullable=True)
    review_status = Column(SQLEnum(ReviewStatus), default=ReviewStatus.PENDING, nullable=False)
    review_score = Column(Integer, nullable=True)
    review_issues = Column(JSON, nullable=True)
    review_corrections = Column(JSON, nullable=True)
    is_current = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    calendar_entry = relationship("CalendarEntry")