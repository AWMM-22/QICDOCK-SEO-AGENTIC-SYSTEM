import logging

from app.agents.state.marketing_state import MarketingState
from app.agents.nodes.base import create_agent_run, complete_agent_run
from app.db.models.agents import AgentType

logger = logging.getLogger(__name__)

ALL_RESEARCH_AGENTS = [
    "product_analyst",
    "brand_knowledge",
    "research",
    "audience",
    "competitor_trend",
]


async def marketing_manager_node(state: MarketingState) -> dict:
    run = await create_agent_run(
        state,
        AgentType.MARKETING_MANAGER,
        {
            "request": state.request.model_dump(mode="json"),
            "organization_id": str(state.organization_id),
        },
    )

    content_types = [ct.value for ct in state.request.content_types]
    platforms = state.request.platforms

    workflow_plan = {
        "objective": state.request.goal,
        "research_needed": list(ALL_RESEARCH_AGENTS),
        "content_agents_needed": [],
        "visual_needed": bool(platforms),
        "reasoning": "",
    }

    if not content_types or "post" in content_types or "carousel" in content_types:
        workflow_plan["content_agents_needed"].append("instagram")
    if "reel" in content_types:
        workflow_plan["content_agents_needed"].append("reels")
    if "story" in content_types:
        workflow_plan["content_agents_needed"].append("stories")

    if not workflow_plan["content_agents_needed"]:
        workflow_plan["content_agents_needed"] = ["instagram", "reels", "stories"]

    reasoning = ""
    llm_usage = {}
    try:
        from app.core.providers.llm.factory import get_llm_provider
        from app.core.providers.llm.base import LLMMessage

        llm = get_llm_provider()
        messages = [
            LLMMessage(
                role="system",
                content=(
                    "You are the Marketing Manager orchestrating Qicdock's AI marketing team. "
                    "Briefly (max 120 words) outline how you will approach this request."
                ),
            ),
            LLMMessage(
                role="user",
                content=(
                    f"Goal: {state.request.goal}\n"
                    f"Platforms: {platforms}\n"
                    f"Content types: {content_types}\n"
                    f"Quantity: {state.request.quantity}"
                ),
            ),
        ]
        response = await llm.generate(messages, temperature=0.3, max_tokens=300)
        reasoning = response.content.strip()
        llm_usage = {
            "tokens_input": response.usage.input_tokens,
            "tokens_output": response.usage.output_tokens,
            "estimated_cost": response.usage.estimated_cost,
            "model_used": response.model,
            "provider_used": response.provider,
        }
    except Exception as e:
        logger.warning("Marketing Manager LLM reasoning unavailable: %s", e)
        state.errors.append(f"Marketing Manager LLM reasoning unavailable: {e}")

    workflow_plan["reasoning"] = reasoning

    metadata = dict(state.metadata)
    metadata["workflow_plan"] = workflow_plan

    await complete_agent_run(
        state,
        run["id"],
        {"workflow_plan": workflow_plan},
        **llm_usage,
    )

    return {
        "metadata": metadata,
        "current_agent": AgentType.MARKETING_MANAGER,
        "errors": state.errors,
        "agent_runs": state.agent_runs,
    }
