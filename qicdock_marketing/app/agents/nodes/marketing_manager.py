from app.agents.state.marketing_state import MarketingState, MarketingRequest
from app.agents.nodes.base import NodeResult, create_agent_run, complete_agent_run
from app.db.models.agents import AgentType
from app.core.providers.llm.factory import get_llm_provider
from app.core.providers.llm.base import LLMMessage


async def marketing_manager_node(state: MarketingState) -> NodeResult:
    run = await create_agent_run(
        state,
        AgentType.MARKETING_MANAGER,
        {
            "request": state.request.model_dump(),
            "organization_id": str(state.organization_id),
        },
    )

    llm = get_llm_provider()

    system_prompt = """You are the Marketing Manager for Qicdock, an AI marketing department.
Your role is to orchestrate the marketing workflow by understanding the user's request
and determining which agents need to be involved.

Analyze the request and determine:
1. What marketing objective is being requested
2. Which research agents are needed (product, brand, audience, competitor/trend, general research)
3. Which content agents are needed (instagram, reels, stories, visual)
4. Whether image generation is needed
5. The overall workflow plan

Return a structured plan for the workflow."""

    user_prompt = f"""
Marketing Request:
- Goal: {state.request.goal}
- Platforms: {state.request.platforms}
- Content Types: {[ct.value for ct in state.request.content_types]}
- Quantity: {state.request.quantity}
- Product IDs: {[str(pid) for pid in state.request.product_ids]}
- Email: {state.request.email}

Determine the workflow plan and which agents to invoke.
"""

    messages = [
        LLMMessage(role="system", content=system_prompt),
        LLMMessage(role="user", content=user_prompt),
    ]

    try:
        response = await llm.generate(messages, temperature=0.3)

        workflow_plan = {
            "objective": state.request.goal,
            "agents_needed": [],
            "research_needed": [],
            "content_agents_needed": [],
            "visual_needed": False,
            "reasoning": response.content,
        }

        content_types = [ct.value for ct in state.request.content_types]
        platforms = state.request.platforms

        if "post" in content_types or "carousel" in content_types:
            workflow_plan["content_agents_needed"].append("instagram")
        if "reel" in content_types:
            workflow_plan["content_agents_needed"].append("reels")
        if "story" in content_types:
            workflow_plan["content_agents_needed"].append("stories")

        if platforms:
            workflow_plan["visual_needed"] = True

        workflow_plan["research_needed"] = [
            "product_analyst",
            "brand_knowledge",
            "research",
            "audience",
            "competitor_trend",
        ]

        workflow_plan["agents_needed"] = (
            workflow_plan["research_needed"]
            + workflow_plan["content_agents_needed"]
        )

        if workflow_plan["visual_needed"]:
            workflow_plan["agents_needed"].append("visual")

        workflow_plan["agents_needed"].extend(["brand_reviewer", "report_generator", "email"])

        state.metadata["workflow_plan"] = workflow_plan
        state.current_agent = AgentType.MARKETING_MANAGER

        await complete_agent_run(
            state,
            run["id"],
            {"workflow_plan": workflow_plan},
            tokens_input=response.usage.input_tokens,
            tokens_output=response.usage.output_tokens,
            estimated_cost=response.usage.estimated_cost,
        )

        return NodeResult(state=state, next_node="load_organization_context")

    except Exception as e:
        await complete_agent_run(state, run["id"], {}, error=str(e))
        state.errors.append(f"Marketing Manager error: {str(e)}")
        return NodeResult(state=state, error=str(e))