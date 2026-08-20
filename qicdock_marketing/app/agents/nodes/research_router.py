from app.agents.state.marketing_state import MarketingState
from app.agents.nodes.base import NodeResult
from app.db.models.agents import AgentType


async def research_router_node(state: MarketingState) -> NodeResult:
    workflow_plan = state.metadata.get("workflow_plan", {})
    research_needed = workflow_plan.get("research_needed", [])

    if not research_needed:
        return NodeResult(state=state, next_node="content_strategy_agent")

    state.metadata["research_queue"] = research_needed
    state.metadata["current_research_index"] = 0

    return NodeResult(state=state, next_node="execute_research_agent")


async def execute_research_agent_node(state: MarketingState) -> NodeResult:
    research_queue = state.metadata.get("research_queue", [])
    current_index = state.metadata.get("current_research_index", 0)

    if current_index >= len(research_queue):
        return NodeResult(state=state, next_node="content_strategy_agent")

    agent_name = research_queue[current_index]
    state.metadata["current_research_index"] = current_index + 1

    agent_mapping = {
        "product_analyst": "product_analyst_agent",
        "brand_knowledge": "brand_knowledge_agent",
        "research": "research_agent",
        "audience": "audience_agent",
        "competitor_trend": "competitor_trend_agent",
    }

    next_agent = agent_mapping.get(agent_name, "content_strategy_agent")
    return NodeResult(state=state, next_node=next_agent)