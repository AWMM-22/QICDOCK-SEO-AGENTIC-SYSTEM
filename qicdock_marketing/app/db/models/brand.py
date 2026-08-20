import uuid
from sqlalchemy import String, Text, Boolean, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.models.base import Base, UUIDMixin, TimestampMixin, OrganizationBase


class BrandProfile(Base, UUIDMixin, TimestampMixin, OrganizationBase):
    __tablename__ = "brand_profiles"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    brand_story: Mapped[str | None] = mapped_column(Text, nullable=True)
    mission: Mapped[str | None] = mapped_column(Text, nullable=True)
    vision: Mapped[str | None] = mapped_column(Text, nullable=True)
    values: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    brand_voice: Mapped[str | None] = mapped_column(Text, nullable=True)
    tone: Mapped[str | None] = mapped_column(Text, nullable=True)
    personality_traits: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    target_audience: Mapped[str | None] = mapped_column(Text, nullable=True)
    positioning_statement: Mapped[str | None] = mapped_column(Text, nullable=True)
    tagline: Mapped[str | None] = mapped_column(String(255), nullable=True)
    words_to_use: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    words_to_avoid: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    marketing_claims: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    primary_color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    secondary_color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    accent_color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    font_primary: Mapped[str | None] = mapped_column(String(100), nullable=True)
    font_secondary: Mapped[str | None] = mapped_column(String(100), nullable=True)
    visual_style: Mapped[str | None] = mapped_column(Text, nullable=True)
    logo_usage_guidelines: Mapped[str | None] = mapped_column(Text, nullable=True)
    competitors: Mapped[list[dict]] = mapped_column(JSONB, default=list, nullable=False)
    usp: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    additional_info: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="brand_profile",
    )
    guidelines: Mapped[list["BrandGuideline"]] = relationship(
        "BrandGuideline",
        back_populates="brand_profile",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_brand_profiles_org", "organization_id", unique=True),
    )


class BrandGuideline(Base, UUIDMixin, TimestampMixin, OrganizationBase):
    __tablename__ = "brand_guidelines"

    brand_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brand_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[int] = mapped_column(default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    brand_profile: Mapped["BrandProfile"] = relationship(
        "BrandProfile",
        back_populates="guidelines",
    )

    __table_args__ = (
        Index("ix_brand_guidelines_brand_category", "brand_profile_id", "category"),
    )