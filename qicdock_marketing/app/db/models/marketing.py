import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Boolean, Integer, ForeignKey, DateTime, Enum as SQLEnum, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from app.db.models.base import Base, UUIDMixin, TimestampMixin, OrganizationBase


class MarketingGoalStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class MarketingGoal(Base, UUIDMixin, TimestampMixin, OrganizationBase):
    __tablename__ = "marketing_goals"

    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    target_platforms: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    content_types: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    target_quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    target_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[MarketingGoalStatus] = mapped_column(
        SQLEnum(MarketingGoalStatus),
        default=MarketingGoalStatus.DRAFT,
        nullable=False,
    )
    meta: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="marketing_goals",
    )
    product: Mapped[Optional["Product"]] = relationship(
        "Product",
        back_populates="marketing_goals",
    )
    agent_runs: Mapped[list["AgentRun"]] = relationship(
        "AgentRun",
        back_populates="marketing_goal",
    )
    content_items: Mapped[list["ContentItem"]] = relationship(
        "ContentItem",
        back_populates="marketing_goal",
    )

    __table_args__ = (
        Index("ix_marketing_goals_org_status", "organization_id", "status"),
    )


class KnowledgeDocument(Base, UUIDMixin, TimestampMixin, OrganizationBase):
    __tablename__ = "knowledge_documents"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    chunk_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_chunks: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(JSONB, nullable=True)
    meta: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="knowledge_documents",
    )

    __table_args__ = (
        Index("ix_knowledge_docs_org_source", "organization_id", "source_type"),
    )


class ContentType(str, enum.Enum):
    POST = "post"
    CAROUSEL = "carousel"
    REEL = "reel"
    STORY = "story"
    IMAGE = "image"


class ContentStatus(str, enum.Enum):
    DRAFT = "draft"
    GENERATED = "generated"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISED = "revised"
    PUBLISHED = "published"


class ContentItem(Base, UUIDMixin, TimestampMixin, OrganizationBase):
    __tablename__ = "content_items"

    marketing_goal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("marketing_goals.id", ondelete="SET NULL"),
        nullable=True,
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
    )
    agent_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    content_type: Mapped[ContentType] = mapped_column(
        SQLEnum(ContentType),
        nullable=False,
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    visual_concept: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    hashtags: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    cta: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[ContentStatus] = mapped_column(
        SQLEnum(ContentStatus),
        default=ContentStatus.DRAFT,
        nullable=False,
    )
    review_score: Mapped[float | None] = mapped_column(nullable=True)
    review_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    revision_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    meta: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    product: Mapped[Optional["Product"]] = relationship(
        "Product",
        back_populates="content_items",
    )
    marketing_goal: Mapped[Optional["MarketingGoal"]] = relationship(
        "MarketingGoal",
        back_populates="content_items",
    )
    agent_run: Mapped[Optional["AgentRun"]] = relationship(
        "AgentRun",
        back_populates="content_items",
    )
    generated_assets: Mapped[list["GeneratedAsset"]] = relationship(
        "GeneratedAsset",
        back_populates="content_item",
        cascade="all, delete-orphan",
    )
    review_results: Mapped[list["ReviewResult"]] = relationship(
        "ReviewResult",
        back_populates="content_item",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_content_items_org_type_status", "organization_id", "content_type", "status"),
        Index("ix_content_items_goal", "marketing_goal_id"),
    )


class AssetType(str, enum.Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"


class GeneratedAsset(Base, UUIDMixin, TimestampMixin, OrganizationBase):
    __tablename__ = "generated_assets"

    content_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    asset_type: Mapped[AssetType] = mapped_column(
        SQLEnum(AssetType),
        nullable=False,
    )
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    aspect_ratio: Mapped[str | None] = mapped_column(String(20), nullable=True)
    width: Mapped[int | None] = mapped_column(nullable=True)
    height: Mapped[int | None] = mapped_column(nullable=True)
    file_size: Mapped[int | None] = mapped_column(nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    review_status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    review_score: Mapped[float | None] = mapped_column(nullable=True)
    meta: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    content_item: Mapped["ContentItem"] = relationship(
        "ContentItem",
        back_populates="generated_assets",
    )

    __table_args__ = (
        Index("ix_generated_assets_content", "content_item_id"),
    )


class ResearchSource(Base, UUIDMixin, TimestampMixin, OrganizationBase):
    __tablename__ = "research_sources"

    agent_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    relevance: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    meta: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    agent_run: Mapped["AgentRun"] = relationship(
        "AgentRun",
        back_populates="research_sources",
    )

    __table_args__ = (
        Index("ix_research_sources_run", "agent_run_id"),
    )
