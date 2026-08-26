import logging

from app.agents.state.marketing_state import (
    MarketingState,
    ContentStrategy,
)
from app.agents.nodes.base import create_agent_run, complete_agent_run, llm_usage_kwargs
from app.db.models.agents import AgentType
from app.core.providers.llm.factory import get_llm_provider
from app.core.providers.llm.base import LLMMessage

logger = logging.getLogger(__name__)


async def content_strategy_agent_node(state: MarketingState) -> dict:
    run = await create_agent_run(
        state,
        AgentType.CONTENT_STRATEGY,
        {
            "goal": state.request.goal,
            "platforms": state.request.platforms,
            "content_types": [ct.value for ct in state.request.content_types],
            "quantity": state.request.quantity,
        },
    )

    context_parts = []
    if state.product_context:
        for p in state.product_context:
            context_parts.append(
                f"Product: {p.name} - {p.description}\n"
                f"USPs: {p.usp}\nFeatures: {p.features}\nBenefits: {p.benefits}"
            )

    if state.metadata.get("product_analysis"):
        pa = state.metadata["product_analysis"]
        context_parts.append(f"Product analysis: marketing angles={pa.get('marketing_angles', [])}, "
                             f"content opportunities={pa.get('content_opportunities', [])}")

    if state.brand_context:
        bc = state.brand_context
        context_parts.append(
            f"Brand voice: {bc.brand_voice}\nTone: {bc.tone}\n"
            f"Words to use: {bc.words_to_use}\nWords to avoid: {bc.words_to_avoid}"
        )

    if state.audience_insights:
        ai = state.audience_insights
        context_parts.append(
            f"Audience: {ai.audience}\nPain points: {ai.pain_points}\n"
            f"Motivations: {ai.motivations}\nObjections: {ai.objections}"
        )

    if state.research:
        context_parts.append(
            f"Trends: {state.research.trends}\nConsumer insights: {state.research.consumer_insights}"
        )

    if state.competitor_insights:
        ci = state.competitor_insights
        context_parts.append(
            f"Competitor opportunities: {ci.opportunities}\nContent gaps: {ci.content_gaps}\n"
            f"Potential hooks: {ci.potential_hooks}\nTrending formats: {ci.trending_formats}"
        )

    strategy = None
    usage = {}
    try:
        llm = get_llm_provider()
        messages = [
            LLMMessage(
                role="system",
                content=(
                    "You are the Content Strategy Agent for Qicdock. Create a detailed content "
                    "strategy grounded strictly in the provided context. For each content item "
                    "determine: platform, format (post/carousel/reel/story), objective, topic, "
                    "target audience, angle, hook, CTA, priority (1=highest), reasoning, visual "
                    "requirement, hashtags. Never invent product features or claims.\n\n"
                    "CONTENT MIX RULE (very important):\n"
                    "- Roughly HALF of the items must be GENERAL product/educational topics, NOT "
                    "tied to any specific car model. Examples: advantages of wireless charging, "
                    "wireless charging myths vs facts, disadvantages of cheap wireless chargers "
                    "and how Qicdock solves them (heat, slow charging, misalignment), MagSafe & "
                    "Qi explained, battery health tips, cable clutter problem, one-hand docking "
                    "convenience, modular charging setups (car console, AC vent, desk, office, "
                    "wall), travel charging tips, why custom-fit beats universal clips.\n"
                    "- The other HALF can be car-specific fit content (e.g. 'Perfect fit for "
                    "your Swift console').\n"
                    "- Vary formats and objectives: educate, entertain, compare, announce, engage.\n\n"
                    "Also define overall_theme and key_messages."
                ),
            ),
            LLMMessage(
                role="user",
                content=(
                    f"Marketing goal: {state.request.goal}\n"
                    f"Platforms: {state.request.platforms}\n"
                    f"Requested content types: {[ct.value for ct in state.request.content_types] or 'any'}\n"
                    f"Quantity of items: {state.request.quantity}\n\n"
                    "Context:\n" + "\n\n".join(context_parts) +
                    "\n\nCreate the content strategy with exactly "
                    f"{state.request.quantity} items."
                ),
            ),
        ]

        strategy = await llm.generate_structured(messages, ContentStrategy, temperature=0.7)
        usage = llm_usage_kwargs(strategy)
    except Exception as e:
        logger.warning("Content Strategy LLM failed: %s", e)
        state.errors.append(f"Content Strategy error: {str(e)}")
        strategy = ContentStrategy()

    state.content_strategy = strategy

    await complete_agent_run(
        state,
        run["id"],
        {"strategy": strategy.model_dump(mode="json")},
        **usage,
    )

    return {
        "content_strategy": strategy,
        "errors": state.errors,
        "agent_runs": state.agent_runs,
        "current_agent": state.current_agent,
    }


# ---------------------------------------------------------------------------
# Routing functions used by conditional edges in the graph.
# ---------------------------------------------------------------------------

def route_content_dispatch(state: MarketingState) -> list[str]:
    workflow_plan = state.metadata.get("workflow_plan", {})
    needed = workflow_plan.get("content_agents_needed", [])

    agent_mapping = {
        "instagram": "instagram_agent",
        "reels": "reels_agent",
        "stories": "stories_agent",
    }

    targets = [agent_mapping[name] for name in needed if name in agent_mapping]
    return targets or ["visual_strategy_agent"]


def route_research_dispatch(state: MarketingState) -> list[str]:
    agent_mapping = {
        "product_analyst": "product_analyst_agent",
        "brand_knowledge": "brand_knowledge_agent",
        "research": "research_agent",
        "audience": "audience_agent",
        "competitor_trend": "competitor_trend_agent",
    }

    targets = list(agent_mapping.values())
    return targets or ["content_strategy_agent"]
