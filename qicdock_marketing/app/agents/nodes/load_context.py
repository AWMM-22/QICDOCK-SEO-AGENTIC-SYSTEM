from app.agents.state.marketing_state import MarketingState
from app.agents.nodes.base import NodeResult, create_agent_run, complete_agent_run
from app.db.models.agents import AgentType
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.organization import Organization
from app.db.models.brand import BrandProfile


async def load_organization_context_node(state: MarketingState) -> NodeResult:
    run = await create_agent_run(
        state,
        AgentType.MARKETING_MANAGER,
        {"action": "load_organization_context", "organization_id": str(state.organization_id)},
    )

    try:
        from app.db.session.database import async_session_maker

        async with async_session_maker() as session:
            org_result = await session.execute(
                select(Organization).where(Organization.id == state.organization_id)
            )
            org = org_result.scalar_one_or_none()

            if not org:
                raise ValueError(f"Organization not found: {state.organization_id}")

            brand_result = await session.execute(
                select(BrandProfile).where(BrandProfile.organization_id == state.organization_id)
            )
            brand = brand_result.scalar_one_or_none()

            state.metadata["organization"] = {
                "id": str(org.id),
                "name": org.name,
                "slug": org.slug,
                "description": org.description,
                "website": org.website,
                "settings": org.settings,
            }

            if brand:
                state.brand_context = type('BrandContext', (), {
                    'brand_profile_id': brand.id,
                    'brand_story': brand.brand_story,
                    'brand_voice': brand.brand_voice,
                    'tone': brand.tone,
                    'target_audience': brand.target_audience,
                    'positioning': brand.positioning_statement,
                    'words_to_use': brand.words_to_use,
                    'words_to_avoid': brand.words_to_avoid,
                    'visual_style': brand.visual_style,
                    'colors': {
                        'primary': brand.primary_color,
                        'secondary': brand.secondary_color,
                        'accent': brand.accent_color,
                    },
                    'usp': brand.usp,
                    'guidelines': [],
                })()

        await complete_agent_run(
            state,
            run["id"],
            {"organization_loaded": True, "brand_loaded": brand is not None},
        )

        return NodeResult(state=state, next_node="load_product_context")

    except Exception as e:
        await complete_agent_run(state, run["id"], {}, error=str(e))
        state.errors.append(f"Load organization context error: {str(e)}")
        return NodeResult(state=state, error=str(e))