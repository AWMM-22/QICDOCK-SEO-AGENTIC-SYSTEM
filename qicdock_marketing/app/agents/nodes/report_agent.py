from app.agents.state.marketing_state import MarketingState
from app.agents.nodes.base import NodeResult, create_agent_run, complete_agent_run
from app.db.models.agents import AgentType
from app.core.providers.llm.factory import get_llm_provider
from app.core.providers.llm.base import LLMMessage
from datetime import datetime


async def report_generator_node(state: MarketingState) -> NodeResult:
    run = await create_agent_run(
        state,
        AgentType.REPORT_GENERATOR,
        {"content_count": len(state.generated_content.items) if state.generated_content else 0},
    )

    llm = get_llm_provider()

    system_prompt = """You are the Marketing Report Generator for Qicdock.
Create a comprehensive HTML marketing report containing:
1. Executive Summary
2. Marketing Objective
3. Product Analysis
4. Audience Analysis
5. Trend Research
6. Competitor Insights
7. Content Strategy
8. Content Calendar
9. Instagram Posts
10. Instagram Carousels
11. Reel Scripts
12. Story Sequences
13. Generated Images
14. Image Prompts
15. Recommended CTAs
16. Hashtags
17. Reasoning behind each content idea
18. Sources
19. Brand Review Results"""

    content_items = []
    if state.generated_content:
        for item in state.generated_content.items:
            content_items.append(item.model_dump())

    images = []
    if state.generated_images:
        for img in state.generated_images.images:
            images.append(img.model_dump())

    review_results = []
    if state.review_results:
        for rev in state.review_results.results:
            review_results.append(rev.model_dump())

    user_prompt = f"""
Generate a complete marketing report for Qicdock.

Campaign: {state.request.goal}
Date: {datetime.now().strftime('%Y-%m-%d')}
Platforms: {state.request.platforms}
Content Types: {[ct.value for ct in state.request.content_types]}

Product: {state.product_context[0].name if state.product_context else 'N/A'}
Product Description: {state.product_context[0].description if state.product_context else 'N/A'}

Brand Voice: {state.brand_context.brand_voice if state.brand_context else 'N/A'}

Audience: {state.audience_insights.audience if state.audience_insights else 'N/A'}
Pain Points: {state.audience_insights.pain_points if state.audience_insights else []}

Research Sources: {len(state.research.sources) if state.research else 0}
Trends: {state.research.trends if state.research else []}

Competitor Insights: {state.competitor_insights.opportunities if state.competitor_insights else []}

Content Strategy Items: {len(state.content_strategy.items) if state.content_strategy else 0}
Generated Content: {len(content_items)}
Generated Images: {len(images)}

Review Results: {review_results}

Generate a professional HTML report.
"""

    messages = [
        LLMMessage(role="system", content=system_prompt),
        LLMMessage(role="user", content=user_prompt),
    ]

    try:
        response = await llm.generate(messages, temperature=0.5)

        state.final_report = response.content

        await complete_agent_run(
            state,
            run["id"],
            {"report_generated": True, "report_length": len(response.content)},
            tokens_input=response.usage.input_tokens,
            tokens_output=response.usage.output_tokens,
            estimated_cost=response.usage.estimated_cost,
        )

        return NodeResult(state=state, next_node="email_agent")

    except Exception as e:
        await complete_agent_run(state, run["id"], {}, error=str(e))
        state.errors.append(f"Report Generator error: {str(e)}")
        return NodeResult(state=state, next_node="email_agent")