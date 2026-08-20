import uuid
from typing import Optional
from sqlalchemy import String, Text, Boolean, Numeric, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.models.base import Base, UUIDMixin, TimestampMixin, OrganizationBase


class Product(Base, UUIDMixin, TimestampMixin, OrganizationBase):
    __tablename__ = "products"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    short_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    features: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    benefits: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    specifications: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    price: Mapped[Optional[Numeric(10, 2)]] = mapped_column(Numeric(10, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tags: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    availability: Mapped[str] = mapped_column(String(50), default="in_stock", nullable=False)
    product_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    usp: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    target_audience: Mapped[str | None] = mapped_column(Text, nullable=True)
    pain_points_solved: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    use_cases: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    emotional_benefits: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    functional_benefits: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    differentiators: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    marketing_info: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    meta: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="products",
    )
    images: Mapped[list["ProductImage"]] = relationship(
        "ProductImage",
        back_populates="product",
        cascade="all, delete-orphan",
    )
    content_items: Mapped[list["ContentItem"]] = relationship(
        "ContentItem",
        back_populates="product",
        cascade="all, delete-orphan",
    )
    marketing_goals: Mapped[list["MarketingGoal"]] = relationship(
        "MarketingGoal",
        back_populates="product",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_products_org_slug", "organization_id", "slug", unique=True),
        Index("ix_products_org_active", "organization_id", "is_active"),
    )


class ProductImage(Base, UUIDMixin, TimestampMixin, OrganizationBase):
    __tablename__ = "product_images"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    alt_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    image_type: Mapped[str] = mapped_column(String(50), default="product", nullable=False)
    meta: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    product: Mapped["Product"] = relationship(
        "Product",
        back_populates="images",
    )

    __table_args__ = (
        Index("ix_product_images_product_primary", "product_id", "is_primary"),
    )