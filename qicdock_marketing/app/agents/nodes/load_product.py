from app.agents.state.marketing_state import MarketingState, ProductContext
from app.agents.nodes.base import NodeResult, create_agent_run, complete_agent_run
from app.db.models.agents import AgentType
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.product import Product, ProductImage


async def load_product_context_node(state: MarketingState) -> NodeResult:
    run = await create_agent_run(
        state,
        AgentType.MARKETING_MANAGER,
        {"action": "load_product_context", "product_ids": [str(pid) for pid in state.product_ids]},
    )

    try:
        from app.db.session.database import async_session_maker

        async with async_session_maker() as session:
            product_contexts = []

            for product_id in state.product_ids:
                product_result = await session.execute(
                    select(Product).where(Product.id == product_id)
                )
                product = product_result.scalar_one_or_none()

                if not product:
                    state.errors.append(f"Product not found: {product_id}")
                    continue

                images_result = await session.execute(
                    select(ProductImage)
                    .where(ProductImage.product_id == product_id)
                    .order_by(ProductImage.is_primary.desc(), ProductImage.sort_order)
                )
                images = images_result.scalars().all()

                product_context = ProductContext(
                    product_id=product.id,
                    name=product.name,
                    description=product.description,
                    features=product.features,
                    benefits=product.benefits,
                    specifications=product.specifications,
                    price=float(product.price) if product.price else None,
                    currency=product.currency,
                    images=[img.url for img in images],
                    usp=product.usp,
                    target_audience=product.target_audience,
                    pain_points_solved=product.pain_points_solved,
                    use_cases=product.use_cases,
                    emotional_benefits=product.emotional_benefits,
                    functional_benefits=product.functional_benefits,
                    differentiators=product.differentiators,
                )
                product_contexts.append(product_context)

            state.product_context = product_contexts

        await complete_agent_run(
            state,
            run["id"],
            {"products_loaded": len(product_contexts)},
        )

        return NodeResult(state=state, next_node="research_router")

    except Exception as e:
        await complete_agent_run(state, run["id"], {}, error=str(e))
        state.errors.append(f"Load product context error: {str(e)}")
        return NodeResult(state=state, error=str(e))