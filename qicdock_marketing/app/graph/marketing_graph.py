from langgraph.graph import StateGraph, START, END
from app.agents.state.marketing_state import MarketingState
from app.agents.nodes.marketing_manager import marketing_manager_node
from app.agents.nodes.load_context import (
    load_organization_context_node,
    load_product_context_node,
)
from app.agents.nodes.research_router import (
    research_router_node,
    execute_research_agent_node,
)
from app.agents.nodes.research_agents import (
    product_analyst_agent_node,
    brand_knowledge_agent_node,
    research_agent_node,
    audience_agent_node,
    competitor_trend_agent_node,
)
from app.agents.nodes.content_strategy import (
    content_strategy_agent_node,
    content_router_node,
    execute_content_agent_node,
)
from app.agents.nodes.content_agents import (
    instagram_agent_node,
    reels_agent_node,
    stories_agent_node,
)
from app.agents.nodes.visual_agents import (
    visual_strategy_agent_node,
    image_generation_agent_node,
)
from app.agents.nodes.review_agents import (
    brand_reviewer_node,
    content_revision_node,
)
from app.agents.nodes.report_agent import report_generator_node
from app.agents.nodes.email_agent import email_agent_node


def create_marketing_graph() -> StateGraph:
    workflow = StateGraph(MarketingState)

    workflow.add_node("marketing_manager", marketing_manager_node)
    workflow.add_node("load_organization_context", load_organization_context_node)
    workflow.add_node("load_product_context", load_product_context_node)
    workflow.add_node("research_router", research_router_node)
    workflow.add_node("execute_research_agent", execute_research_agent_node)
    workflow.add_node("product_analyst_agent", product_analyst_agent_node)
    workflow.add_node("brand_knowledge_agent", brand_knowledge_agent_node)
    workflow.add_node("research_agent", research_agent_node)
    workflow.add_node("audience_agent", audience_agent_node)
    workflow.add_node("competitor_trend_agent", competitor_trend_agent_node)
    workflow.add_node("content_strategy_agent", content_strategy_agent_node)
    workflow.add_node("content_router", content_router_node)
    workflow.add_node("execute_content_agent", execute_content_agent_node)
    workflow.add_node("instagram_agent", instagram_agent_node)
    workflow.add_node("reels_agent", reels_agent_node)
    workflow.add_node("stories_agent", stories_agent_node)
    workflow.add_node("visual_strategy_agent", visual_strategy_agent_node)
    workflow.add_node("image_generation_agent", image_generation_agent_node)
    workflow.add_node("brand_reviewer", brand_reviewer_node)
    workflow.add_node("content_revision", content_revision_node)
    workflow.add_node("report_generator", report_generator_node)
    workflow.add_node("email_agent", email_agent_node)

    workflow.add_edge(START, "marketing_manager")
    workflow.add_edge("marketing_manager", "load_organization_context")
    workflow.add_edge("load_organization_context", "load_product_context")
    workflow.add_edge("load_product_context", "research_router")
    workflow.add_edge("research_router", "execute_research_agent")
    workflow.add_edge("execute_research_agent", "product_analyst_agent")
    workflow.add_edge("execute_research_agent", "brand_knowledge_agent")
    workflow.add_edge("execute_research_agent", "research_agent")
    workflow.add_edge("execute_research_agent", "audience_agent")
    workflow.add_edge("execute_research_agent", "competitor_trend_agent")

    workflow.add_edge("product_analyst_agent", "execute_research_agent")
    workflow.add_edge("brand_knowledge_agent", "execute_research_agent")
    workflow.add_edge("research_agent", "execute_research_agent")
    workflow.add_edge("audience_agent", "execute_research_agent")
    workflow.add_edge("competitor_trend_agent", "execute_research_agent")

    workflow.add_edge("execute_research_agent", "content_strategy_agent")
    workflow.add_edge("content_strategy_agent", "content_router")
    workflow.add_edge("content_router", "execute_content_agent")
    workflow.add_edge("execute_content_agent", "instagram_agent")
    workflow.add_edge("execute_content_agent", "reels_agent")
    workflow.add_edge("execute_content_agent", "stories_agent")

    workflow.add_edge("instagram_agent", "execute_content_agent")
    workflow.add_edge("reels_agent", "execute_content_agent")
    workflow.add_edge("stories_agent", "execute_content_agent")

    workflow.add_edge("execute_content_agent", "visual_strategy_agent")
    workflow.add_edge("visual_strategy_agent", "image_generation_agent")
    workflow.add_edge("image_generation_agent", "brand_reviewer")

    workflow.add_conditional_edges(
        "brand_reviewer",
        lambda state: "content_revision" if state.review_results and state.review_results.revision_needed and state.revision_count < 2 else "report_generator",
    )
    workflow.add_edge("content_revision", "brand_reviewer")
    workflow.add_edge("report_generator", "email_agent")
    workflow.add_edge("email_agent", END)

    return workflow.compile()


marketing_graph = create_marketing_graph()