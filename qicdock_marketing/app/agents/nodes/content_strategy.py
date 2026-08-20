from app.agents.state.marketing_state import (
    MarketingState,
    ContentStrategy,
    ContentStrategyItem,
    ContentType,
)
from app.agents.nodes.base import NodeResult, create_agent_run, complete_agent_run
from app.db.models.agents import AgentType
from app.core.providers.llm.factory import get_llm_provider
from app.core.providers.llm.base import LLMMessage


async def content_strategy_agent_node(state: MarketingState) -> NodeResult:
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

    llm = get_llm_provider()

    system_prompt = """You are the Content Strategy Agent for Qicdock.
Create a detailed content strategy based on all the research and context gathered.
For each content item, determine:
- Platform
- Format (post, carousel, reel, story)
- Objective
- Topic
- Target audience
- Content angle
- Hook
- CTA
- Priority
- Reasoning
- Visual requirement
- Hashtags

Return a structured content strategy with multiple content items."""

    context_parts = []
    if state.product_context:
        p = state.product_context[0]
        context_parts.append(f"Product: {p.name} - {p.description}")
        context_parts.append(f"USPs: {p.usp}")
        context_parts.append(f"Features: {p.features}")
        context_parts.append(f"Benefits: {p.benefits}")

    if state.brand_context:
        context_parts.append(f"Brand Voice: {state.brand_context.brand_voice}")
        context_parts.append(f"Tone: {state.brand_context.tone}")
        context_parts.append(f"Words to use: {state.brand_context.words_to_use}")
        context_parts.append(f"Words to avoid: {state.brand_context.words_to_avoid}")

    if state.audience_insights:
        context_parts.append(f"Audience: {state.audience_insights.audience}")
        context_parts.append(f"Pain points: {state.audience_insights.pain_points}")
        context_parts.append(f"Motivations: {state.audience_insights.motivations}")

    if state.competitor_insights:
        context_parts.append(f"Opportunities: {state.competitor_insights.opportunities}")
        context_parts.append(f"Content gaps: {state.competitor_insights.content_gaps}")
        context_parts.append(f"Potential hooks: {state.competitor_insights.potential_hooks}")

    user_prompt = f"""
Marketing Goal: {state.request.goal}
Platforms: {state.request.platforms}
Content Types: {[ct.value for ct in state.request.content_types]}
Quantity: {state.request.quantity}

Context:
{chr(10).join(context_parts)}

Create a content strategy with {state.request.quantity} content items.
"""

    messages = [
        LLMMessage(role="system", content=system_prompt),
        LLMMessage(role="user", content=user_prompt),
    ]

    try:
        response = await llm.generate_structured(messages, ContentStrategy, temperature=0.7)

        state.content_strategy = response

        await complete_agent_run(
            state,
            run["id"],
            {"strategy": response.model_dump()},
            tokens_input=response.usage.input_tokens,
            tokens_output=response.usage.output_tokens,
            estimated_cost=response.usage.estimated_cost,
        )

        return NodeResult(state=state, next_node="content_router")

    except Exception as e:
        await complete_agent_run(state, run["id"], {}, error=str(e))
        state.errors.append(f"Content Strategy error: {str(e)}")
        return NodeResult(state=state, next_node="content_router")


async def content_router_node(state: MarketingState) -> NodeResult:
    if not state.content_strategy or not state.content_strategy.items:
        return NodeResult(state=state, next_node="visual_strategy_agent")

    workflow_plan = state.metadata.get("workflow_plan", {})
    content_agents_needed = workflow_plan.get("content_agents_needed", [])

    if not content_agents_needed:
        return NodeResult(state=state, next_node="visual_strategy_agent")

    state.metadata["content_queue"] = content_agents_needed
    state.metadata["current_content_index"] = 0

    return NodeResult(state=state, next_node="execute_content_agent")


async def execute_content_agent_node(state: MarketingState) -> NodeResult:
    content_queue = state.metadata.get("content_queue", [])
    current_index = state.metadata.get("current_content_index", 0)

    if current_index >= len(content_queue):
        return NodeResult(state=state, next_node="visual_strategy_agent")

    agent_name = content_queue[current_index]
    state.metadata["current_content_index"] = current_index + 1

    agent_mapping = {
        "instagram": "instagram_agent",
        "reels": "reels_agent",
        "stories": "stories_agent",
    }

    next_agent = agent_mapping.get(agent_name, "visual_strategy_agent")
    return NodeResult(state=state, next_node=next_agent)