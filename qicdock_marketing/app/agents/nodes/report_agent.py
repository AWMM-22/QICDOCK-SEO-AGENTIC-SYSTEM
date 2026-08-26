import logging
from datetime import datetime, timezone

from app.agents.state.marketing_state import MarketingState
from app.agents.nodes.base import create_agent_run, complete_agent_run, llm_usage_kwargs
from app.core.providers.llm.factory import get_llm_provider
from app.core.providers.llm.base import LLMMessage
from app.db.models.agents import AgentType, ReportStatus

logger = logging.getLogger(__name__)


async def report_generator_node(state: MarketingState) -> dict:
    run = await create_agent_run(
        state,
        AgentType.REPORT_GENERATOR,
        {"content_count": len(state.generated_content.items) if state.generated_content else 0},
    )

    content_items = (
        [item.model_dump(mode="json") for item in state.generated_content.items]
        if state.generated_content else []
    )
    images = (
        [img.model_dump(mode="json") for img in state.generated_images.images]
        if state.generated_images else []
    )
    review_results = (
        [rev.model_dump(mode="json") for rev in state.review_results.results]
        if state.review_results else []
    )
    pa = state.metadata.get("product_analysis", {})

    user_prompt = f"""Generate a complete marketing report for Qicdock.

Campaign: {state.request.goal}
Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}
Platforms: {state.request.platforms}
Content Types: {[ct.value for ct in state.request.content_types]}

Product: {state.product_context[0].name if state.product_context else 'N/A'}
Product Description: {state.product_context[0].description if state.product_context else 'N/A'}
Product analysis: {pa}

Brand voice: {state.brand_context.brand_voice if state.brand_context else 'N/A'}

Audience: {state.audience_insights.model_dump() if state.audience_insights else 'N/A'}

Research trends: {state.research.trends if state.research else []}
Consumer insights: {state.research.consumer_insights if state.research else []}

Competitor opportunities: {state.competitor_insights.opportunities if state.competitor_insights else []}
Content gaps: {state.competitor_insights.content_gaps if state.competitor_insights else []}

Content strategy: {state.content_strategy.model_dump(mode='json') if state.content_strategy else 'N/A'}

Generated content items ({len(content_items)}): {content_items}
Generated images ({len(images)}): {images}

Brand review results: {review_results}

{f"IMPORTANT: Some content failed brand review after max revisions and requires HUMAN REVIEW before use: {state.metadata.get('human_review_required')}" if state.metadata.get('human_review_required') else ''}

Generate a professional, self-contained HTML report with inline CSS containing these sections:
1. Executive Summary  2. Marketing Objective  3. Product Insights  4. Target Audience
5. Market & Competitor Insights  6. Content Strategy & Pillars  7. Instagram Feed Posts
8. Carousels  9. Reels Scripts  10. Story Sequences  11. Visual Requirements & Image Prompts
12. Recommendations  13. Next Steps"""

    usage = {}
    try:
        llm = get_llm_provider()
        messages = [
            LLMMessage(
                role="system",
                content=(
                    "You are the Marketing Report Generator for Qicdock. Compile all validated "
                    "agent outputs into one complete HTML marketing report. Do not invent new "
                    "facts - only organize and present what is provided. Output ONLY the HTML "
                    "document."
                ),
            ),
            LLMMessage(role="user", content=user_prompt),
        ]
        response = await llm.generate(messages, temperature=0.4)
        html_report = response.content
        usage = llm_usage_kwargs(response)
    except Exception as e:
        logger.warning("Report Generator LLM failed - building fallback HTML: %s", e)
        state.errors.append(f"Report Generator error: {str(e)}")
        html_report = _fallback_html(state)

    # Persist report to database
    report_id = None
    try:
        from sqlalchemy import select
        from app.db.session.database import async_session_maker
        from app.db.models.agents import MarketingReport

        async with async_session_maker() as session:
            existing = None
            if state.marketing_goal_id:
                result = await session.execute(
                    select(MarketingReport).where(
                        MarketingReport.marketing_goal_id == state.marketing_goal_id,
                        MarketingReport.status == ReportStatus.GENERATING,
                    )
                )
                existing = result.scalars().first()

            if not existing:
                existing = MarketingReport(
                    organization_id=state.organization_id,
                    marketing_goal_id=state.marketing_goal_id,
                    title=f"Marketing Report - {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
                    executive_summary=_extract_summary(html_report),
                    html_content="",
                    markdown_content="",
                    status=ReportStatus.GENERATING,
                    agent_run_id=None,
                )
                session.add(existing)

            existing.html_content = html_report
            existing.markdown_content = html_report
            existing.status = ReportStatus.COMPLETED
            await session.commit()
            await session.refresh(existing)
            report_id = str(existing.id)
    except Exception as e:
        logger.warning("Failed to persist marketing report: %s", e)
        state.errors.append(f"Report persistence error: {str(e)}")

    metadata = dict(state.metadata)
    metadata["report_id"] = report_id

    state.final_report = html_report

    await complete_agent_run(
        state,
        run["id"],
        {
            "report_generated": True,
            "report_id": report_id,
            "report_length": len(html_report),
        },
        **usage,
    )

    return {
        "final_report": html_report,
        "metadata": metadata,
        "errors": state.errors,
        "agent_runs": state.agent_runs,
        "current_agent": state.current_agent,
    }


def _extract_summary(html: str, max_len: int = 800) -> str:
    text = html
    for tag in ["<h1>", "</h1>", "<h2>", "</h2>", "<p>", "</p>"]:
        text = text.replace(tag, "\n")
    lines = [ln.strip() for ln in text.split("\n") if ln.strip() and not ln.strip().startswith("<")]
    return " ".join(lines)[:max_len]


def _fallback_html(state: MarketingState) -> str:
    items_html = ""
    if state.generated_content:
        for item in state.generated_content.items:
            items_html += f"<li><b>{item.title}</b><br>{item.content.get('caption', '')}</li>"
    return f"""
<html><body style="font-family:sans-serif;max-width:800px;margin:auto">
<h1>Qicdock Marketing Report</h1>
<p>Campaign: {state.request.goal}</p>
<p>Note: full report generation encountered an error; showing generated content summary.</p>
<ul>{items_html}</ul>
</body></html>"""
