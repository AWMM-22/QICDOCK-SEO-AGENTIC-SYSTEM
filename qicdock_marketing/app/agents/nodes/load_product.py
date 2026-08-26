import logging

from sqlalchemy import select

from app.agents.state.marketing_state import MarketingState, ProductContext
from app.agents.nodes.base import create_agent_run, complete_agent_run
from app.db.models.agents import AgentType
from app.db.models.product import Product, ProductImage

logger = logging.getLogger(__name__)


async def load_product_context_node(state: MarketingState) -> dict:
    run = await create_agent_run(
        state,
        AgentType.MARKETING_MANAGER,
        {"action": "load_product_context", "product_ids": [str(pid) for pid in state.product_ids]},
    )

    try:
        from app.db.session.database import async_session_maker

        product_contexts: list[ProductContext] = []

        async with async_session_maker() as session:
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

                product_contexts.append(
                    ProductContext(
                        product_id=product.id,
                        name=product.name,
                        description=product.description,
                        features=product.features or [],
                        benefits=product.benefits or [],
                        specifications=product.specifications or {},
                        price=float(product.price) if product.price else None,
                        currency=product.currency,
                        images=[img.url for img in images],
                        usp=product.usp or [],
                        target_audience=product.target_audience,
                        pain_points_solved=product.pain_points_solved or [],
                        use_cases=product.use_cases or [],
                        emotional_benefits=product.emotional_benefits or [],
                        functional_benefits=product.functional_benefits or [],
                        differentiators=product.differentiators or [],
                    )
                )

        state.product_context = product_contexts

        await complete_agent_run(
            state,
            run["id"],
            {"products_loaded": len(product_contexts)},
        )

        return {
            "product_context": product_contexts,
            "errors": state.errors,
            "agent_runs": state.agent_runs,
            "current_agent": state.current_agent,
        }

    except Exception as e:
        await complete_agent_run(state, run["id"], {}, error=str(e))
        state.errors.append(f"Load product context error: {str(e)}")
        return {
            "errors": state.errors,
            "agent_runs": state.agent_runs,
        }
