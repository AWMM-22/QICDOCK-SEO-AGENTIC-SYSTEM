import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, ForeignKey, DateTime, Enum as SQLEnum, Index, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from app.db.models.base import Base, UUIDMixin, TimestampMixin, OrganizationBase


class AgentRunStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentType(str, enum.Enum):
    MARKETING_MANAGER = "marketing_manager"
    PRODUCT_ANALYST = "product_analyst"
    BRAND_KNOWLEDGE = "brand_knowledge"
    RESEARCH = "research"
    AUDIENCE = "audience"
    COMPETITOR_TREND = "competitor_trend"
    CONTENT_STRATEGY = "content_strategy"
    INSTAGRAM = "instagram"
    REELS = "reels"
    STORIES = "stories"
    VISUAL = "visual"
    BRAND_REVIEWER = "brand_reviewer"
    REPORT_GENERATOR = "report_generator"
    EMAIL = "email"


class AgentRun(Base, UUIDMixin, TimestampMixin, OrganizationBase):
    __tablename__ = "agent_runs"

    marketing_goal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("marketing_goals.id", ondelete="SET NULL"),
        nullable=True,
    )
    parent_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    agent_type: Mapped[AgentType] = mapped_column(
        SQLEnum(AgentType),
        nullable=False,
    )
    status: Mapped[AgentRunStatus] = mapped_column(
        SQLEnum(AgentRunStatus),
        default=AgentRunStatus.PENDING,
        nullable=False,
    )
    input_data: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    output_data: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_input: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tokens_output: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estimated_cost: Mapped[Numeric(10, 6)] = mapped_column(Numeric(10, 6), default=0, nullable=False)
    model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    provider_used: Mapped[str | None] = mapped_column(String(50), nullable=True)
    meta: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="agent_runs",
    )
    marketing_goal: Mapped[Optional["MarketingGoal"]] = relationship(
        "MarketingGoal",
        back_populates="agent_runs",
    )
    parent_run: Mapped[Optional["AgentRun"]] = relationship(
        "AgentRun",
        back_populates="child_runs",
        remote_side="AgentRun.id",
    )
    child_runs: Mapped[list["AgentRun"]] = relationship(
        "AgentRun",
        back_populates="parent_run",
    )
    messages: Mapped[list["AgentMessage"]] = relationship(
        "AgentMessage",
        back_populates="agent_run",
        cascade="all, delete-orphan",
    )
    content_items: Mapped[list["ContentItem"]] = relationship(
        "ContentItem",
        back_populates="agent_run",
    )
    research_sources: Mapped[list["ResearchSource"]] = relationship(
        "ResearchSource",
        back_populates="agent_run",
        cascade="all, delete-orphan",
    )
    review_results: Mapped[list["ReviewResult"]] = relationship(
        "ReviewResult",
        back_populates="agent_run",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_agent_runs_org_status", "organization_id", "status"),
        Index("ix_agent_runs_goal", "marketing_goal_id"),
        Index("ix_agent_runs_parent", "parent_run_id"),
    )


class AgentMessage(Base, UUIDMixin, TimestampMixin, OrganizationBase):
    __tablename__ = "agent_messages"

    agent_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    meta: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    agent_run: Mapped["AgentRun"] = relationship(
        "AgentRun",
        back_populates="messages",
    )

    __table_args__ = (
        Index("ix_agent_messages_run", "agent_run_id"),
    )


class ReviewStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


class ReviewResult(Base, UUIDMixin, TimestampMixin, OrganizationBase):
    __tablename__ = "review_results"

    agent_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    content_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    reviewer_agent_type: Mapped[AgentType] = mapped_column(
        SQLEnum(AgentType),
        nullable=False,
    )
    status: Mapped[ReviewStatus] = mapped_column(
        SQLEnum(ReviewStatus),
        default=ReviewStatus.PENDING,
        nullable=False,
    )
    score: Mapped[float | None] = mapped_column(nullable=True)
    issues: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    suggested_changes: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    approved: Mapped[bool] = mapped_column(default=False, nullable=False)
    review_details: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    agent_run: Mapped["AgentRun"] = relationship(
        "AgentRun",
        back_populates="review_results",
    )
    content_item: Mapped["ContentItem"] = relationship(
        "ContentItem",
        back_populates="review_results",
    )

    __table_args__ = (
        Index("ix_review_results_content", "content_item_id"),
        Index("ix_review_results_run", "agent_run_id"),
    )


class ReportStatus(str, enum.Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    COMPLETED = "completed"
    EMAILED = "emailed"
    FAILED = "failed"


class MarketingReport(Base, UUIDMixin, TimestampMixin, OrganizationBase):
    __tablename__ = "marketing_reports"

    marketing_goal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("marketing_goals.id", ondelete="CASCADE"),
        nullable=False,
    )
    agent_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    executive_summary: Mapped[str] = mapped_column(Text, nullable=False)
    html_content: Mapped[str] = mapped_column(Text, nullable=False)
    markdown_content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ReportStatus] = mapped_column(
        SQLEnum(ReportStatus),
        default=ReportStatus.DRAFT,
        nullable=False,
    )
    email_status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    email_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    email_recipient: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meta: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="marketing_reports",
    )
    marketing_goal: Mapped["MarketingGoal"] = relationship(
        "MarketingGoal",
    )

    __table_args__ = (
        Index("ix_marketing_reports_org_status", "organization_id", "status"),
        Index("ix_marketing_reports_goal", "marketing_goal_id"),
    )