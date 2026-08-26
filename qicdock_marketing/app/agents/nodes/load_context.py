import logging

from sqlalchemy import select

from app.agents.state.marketing_state import MarketingState, BrandContext
from app.agents.nodes.base import create_agent_run, complete_agent_run
from app.db.models.agents import AgentType
from app.db.models.organization import Organization
from app.db.models.brand import BrandProfile, BrandGuideline

logger = logging.getLogger(__name__)


async def load_organization_context_node(state: MarketingState) -> dict:
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

            metadata = dict(state.metadata)
            metadata["organization"] = {
                "id": str(org.id),
                "name": org.name,
                "slug": org.slug,
                "description": org.description,
                "website": org.website,
                "settings": org.settings or {},
            }

            brand_loaded = False
            if brand:
                guidelines_result = await session.execute(
                    select(BrandGuideline).where(
                        BrandGuideline.brand_profile_id == brand.id,
                        BrandGuideline.is_active == True,  # noqa: E712
                    )
                )
                guidelines = [
                    {"title": g.title, "category": g.category, "content": g.content}
                    for g in guidelines_result.scalars().all()
                ]

                state.brand_context = BrandContext(
                    brand_profile_id=brand.id,
                    brand_story=brand.brand_story,
                    brand_voice=brand.brand_voice,
                    tone=brand.tone,
                    target_audience=brand.target_audience,
                    positioning=brand.positioning_statement,
                    words_to_use=brand.words_to_use or [],
                    words_to_avoid=brand.words_to_avoid or [],
                    visual_style=brand.visual_style,
                    colors={
                        "primary": brand.primary_color,
                        "secondary": brand.secondary_color,
                        "accent": brand.accent_color,
                    },
                    usp=brand.usp or [],
                    marketing_claims=brand.marketing_claims or [],
                    competitors=brand.competitors or [],
                    guidelines=guidelines,
                )
                brand_loaded = True

            metadata["brand_loaded"] = brand_loaded

            # RAG: retrieve relevant brand knowledge snippets for this objective
            try:
                from app.db.session.database import async_session_maker as _session_maker
                from app.rag.knowledge import retrieve_brand_context_snippets

                async with _session_maker() as rag_session:
                    snippets = await retrieve_brand_context_snippets(
                        rag_session, state.organization_id, state.request.goal
                    )
                metadata["knowledge_snippets"] = snippets
                if snippets:
                    if state.brand_context:
                        state.brand_context.guidelines = list(
                            state.brand_context.guidelines or []
                        ) + [
                            {
                                "title": s["title"],
                                "category": "knowledge_base",
                                "content": s["content"][:1000],
                            }
                            for s in snippets
                        ]
            except Exception as rag_error:
                logger.warning("Knowledge retrieval skipped: %s", rag_error)

            await complete_agent_run(
                state,
                run["id"],
                {
                    "organization_loaded": True,
                    "brand_loaded": brand_loaded,
                    "knowledge_snippets": len(metadata.get("knowledge_snippets", [])),
                },
            )

            return {
                "brand_context": state.brand_context,
                "metadata": metadata,
                "errors": state.errors,
                "agent_runs": state.agent_runs,
                "current_agent": state.current_agent,
            }

    except Exception as e:
        await complete_agent_run(state, run["id"], {}, error=str(e))
        state.errors.append(f"Load organization context error: {str(e)}")
        return {
            "metadata": state.metadata,
            "errors": state.errors,
            "agent_runs": state.agent_runs,
        }
