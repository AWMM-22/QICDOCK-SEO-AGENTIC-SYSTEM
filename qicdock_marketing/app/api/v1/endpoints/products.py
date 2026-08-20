from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import Optional

from app.db.session.database import get_async_session
from app.db.models.organization import Organization
from app.db.models.product import Product, ProductImage
from app.db.models.marketing import KnowledgeDocument
from app.schemas.request.marketing import ProductCreateRequest, KnowledgeIngestRequest


router = APIRouter()


@router.post("/products", status_code=status.HTTP_201_CREATED)
async def create_product(
    request: ProductCreateRequest,
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(
        select(Organization).where(Organization.id == request.organization_id)
    )
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    existing = await session.execute(
        select(Product).where(
            Product.organization_id == request.organization_id,
            Product.slug == request.slug,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Product with this slug already exists")

    product = Product(
        organization_id=request.organization_id,
        name=request.name,
        slug=request.slug,
        description=request.description,
        short_description=request.short_description,
        features=request.features,
        benefits=request.benefits,
        specifications=request.specifications,
        price=request.price,
        currency=request.currency,
        sku=request.sku,
        category=request.category,
        tags=request.tags,
        product_url=request.product_url,
        usp=request.usp,
        target_audience=request.target_audience,
        pain_points_solved=request.pain_points_solved,
        use_cases=request.use_cases,
        emotional_benefits=request.emotional_benefits,
        functional_benefits=request.functional_benefits,
        differentiators=request.differentiators,
    )
    session.add(product)
    await session.commit()
    await session.refresh(product)

    return {
        "id": product.id,
        "name": product.name,
        "slug": product.slug,
        "message": "Product created successfully",
    }


@router.get("/products/{product_id}")
async def get_product(
    product_id: UUID,
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    images_result = await session.execute(
        select(ProductImage).where(ProductImage.product_id == product_id)
    )
    images = images_result.scalars().all()

    return {
        "id": product.id,
        "name": product.name,
        "slug": product.slug,
        "description": product.description,
        "short_description": product.short_description,
        "features": product.features,
        "benefits": product.benefits,
        "specifications": product.specifications,
        "price": float(product.price) if product.price else None,
        "currency": product.currency,
        "sku": product.sku,
        "category": product.category,
        "tags": product.tags,
        "product_url": product.product_url,
        "usp": product.usp,
        "target_audience": product.target_audience,
        "pain_points_solved": product.pain_points_solved,
        "use_cases": product.use_cases,
        "emotional_benefits": product.emotional_benefits,
        "functional_benefits": product.functional_benefits,
        "differentiators": product.differentiators,
        "images": [
            {"id": img.id, "url": img.url, "is_primary": img.is_primary, "alt_text": img.alt_text}
            for img in images
        ],
        "created_at": product.created_at,
        "updated_at": product.updated_at,
    }


@router.post("/knowledge/ingest", status_code=status.HTTP_201_CREATED)
async def ingest_knowledge(
    request: KnowledgeIngestRequest,
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(
        select(Organization).where(Organization.id == request.organization_id)
    )
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    doc = KnowledgeDocument(
        organization_id=request.organization_id,
        title=request.title,
        content=request.content,
        source_type=request.source_type,
        source_url=request.source_url,
        metadata=request.metadata,
    )
    session.add(doc)
    await session.commit()
    await session.refresh(doc)

    return {
        "id": doc.id,
        "title": doc.title,
        "message": "Knowledge document ingested successfully",
    }