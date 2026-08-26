import logging
from typing import Optional

from pydantic import BaseModel, Field

from app.agents.state.marketing_state import (
    MarketingState,
    ReviewResults,
    ReviewResultItem,
    GeneratedContentItem,
)
from app.agents.nodes.base import create_agent_run, complete_agent_run, llm_usage_kwargs
from app.core.config.settings import settings
from app.core.providers.llm.factory import get_llm_provider
from app.core.providers.llm.base import LLMMessage
from app.db.models.agents import AgentType
from app.db.models.marketing import ContentStatus

logger = logging.getLogger(__name__)


class ReviewVerdict(BaseModel):
    content_id: str
    approved: bool
    score: float = Field(ge=0, le=10)
    issues: list[str] = Field(default_factory=list)
    suggested_changes: list[str] = Field(default_factory=list)


class ReviewOutput(BaseModel):
    verdicts: list[ReviewVerdict] = Field(default_factory=list)


async def brand_reviewer_node(state: MarketingState) -> dict:
    run = await create_agent_run(
        state,
        AgentType.BRAND_REVIEWER,
        {
            "content_count": len(state.generated_content.items) if state.generated_content else 0,
            "image_count": len(state.generated_images.images) if state.generated_images else 0,
            "revision_count": state.revision_count,
        },
    )

    items = state.generated_content.items if state.generated_content else []

    bc = state.brand_context
    pa = state.metadata.get("product_analysis", {})

    system_prompt = """You are the Brand Reviewer for Qicdock - the quality-control layer.
Review each content item for:
- Brand voice compliance and tone
- Words-to-avoid violations
- Product accuracy (no invented features/specs/claims)
- Unsupported marketing claims or statistics
- Grammar, clarity, hook effectiveness, CTA clarity
- Audience relevance and platform suitability

Be strict about factual accuracy against the product facts provided. Approve only
content that is on-brand and factually safe. Score 0-10 (7+ = approval worthy)."""

    content_summary = []
    for item in items:
        content_summary.append({
            "content_id": str(item.content_id),
            "type": item.content_type.value,
            "title": item.title,
            "hook": item.content.get("hook", ""),
            "caption": (item.content.get("caption", "") or "")[:600],
            "cta": item.cta,
            "hashtags": item.hashtags,
            "revision_notes_applied": item.content.get("revision_notes"),
            "revision_count": item.revision_count,
        })

    user_prompt = f"""Review these {len(content_summary)} content items:

{content_summary}

Brand voice: {bc.brand_voice if bc else 'N/A'}
Tone: {bc.tone if bc else 'N/A'}
Words to use: {bc.words_to_use if bc else []}
Words to AVOID: {bc.words_to_avoid if bc else []}
Verified marketing claims ONLY: {bc.marketing_claims if bc else []}
Product USPs: {pa.get('main_usp', 'N/A')} + {pa.get('secondary_usps', [])}
Product features: {state.product_context[0].features if state.product_context else []}

Return a verdict for EVERY content_id."""

    review_output: Optional[ReviewOutput] = None
    usage = {}
    try:
        llm = get_llm_provider()
        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_prompt),
        ]
        review_output = await llm.generate_structured(messages, ReviewOutput, temperature=0.2)
        usage = llm_usage_kwargs(review_output)
    except Exception as e:
        logger.warning("Brand Reviewer LLM failed - approving by default to avoid deadlock: %s", e)
        state.errors.append(f"Brand Reviewer error: {str(e)}")

    verdict_map = {}
    if review_output:
        for v in review_output.verdicts:
            verdict_map[v.content_id] = v

    review_results = []
    any_rejected = False

    for item in items:
        item_key = str(item.content_id)
        verdict = verdict_map.get(item_key)

        if verdict is not None:
            approved = bool(verdict.approved) and verdict.score >= 7.0
            result = ReviewResultItem(
                content_item_id=item.content_id,
                reviewer_agent_type=AgentType.BRAND_REVIEWER,
                approved=approved,
                score=verdict.score,
                issues=verdict.issues,
                suggested_changes=verdict.suggested_changes,
                review_details={"llm_reviewed": True},
            )
        else:
            result = ReviewResultItem(
                content_item_id=item.content_id,
                reviewer_agent_type=AgentType.BRAND_REVIEWER,
                approved=True,
                score=None,
                issues=["No verdict returned by reviewer - passed by default"],
                review_details={"llm_reviewed": False},
            )

        if not result.approved:
            any_rejected = True

        item.review_score = result.score
        item.review_feedback = "; ".join(result.issues) if result.issues else None
        item.status = ContentStatus.APPROVED if result.approved else ContentStatus.REJECTED

        review_results.append(result)

    revision_needed = any_rejected and state.revision_count < settings.MAX_REVISION_LOOPS

    # Retries exhausted with content still rejected -> flag for human review
    # instead of silently regenerating forever (plan section 24/29).
    human_review_required = any_rejected and not revision_needed

    state.review_results = ReviewResults(
        results=review_results,
        all_approved=not any_rejected,
        revision_needed=revision_needed,
    )

    metadata = dict(state.metadata)
    if human_review_required:
        metadata["human_review_required"] = {
            "reason": "Content failed brand review after max revision loops",
            "rejected_items": [
                str(r.content_item_id)
                for r in review_results
                if not r.approved
            ],
            "issues": [
                issue
                for r in review_results
                if not r.approved
                for issue in r.issues
            ],
        }
        state.errors.append(
            "Human review required: content still failing brand review after "
            f"{state.revision_count} revision loops"
        )

    await complete_agent_run(
        state,
        run["id"],
        {
            "review_results": [r.model_dump(mode="json") for r in review_results],
            "all_approved": not any_rejected,
            "revision_needed": revision_needed,
        },
        **usage,
    )

    return {
        "generated_content": state.generated_content,
        "review_results": state.review_results,
        "metadata": metadata,
        "errors": state.errors,
        "agent_runs": state.agent_runs,
        "current_agent": state.current_agent,
    }


def route_after_review(state: MarketingState) -> str:
    if (
        state.review_results
        and state.review_results.revision_needed
        and state.revision_count < settings.MAX_REVISION_LOOPS
    ):
        return "content_revision"
    return "report_generator"


async def content_revision_node(state: MarketingState) -> dict:
    run = await create_agent_run(
        state,
        AgentType.CONTENT_STRATEGY,
        {"action": "revise_content", "revision_count": state.revision_count},
    )

    try:
        rejected_ids = {
            str(r.content_item_id)
            for r in (state.review_results.results if state.review_results else [])
            if not r.approved
        }

        if state.generated_content:
            for item in state.generated_content.items:
                if str(item.content_id) in rejected_ids:
                    matching = next(
                        (
                            r for r in state.review_results.results
                            if str(r.content_item_id) == str(item.content_id)
                        ),
                        None,
                    )
                    notes = matching.suggested_changes if matching else []
                    existing_notes = item.content.get("revision_notes") or []
                    item.content["revision_notes"] = list(
                        dict.fromkeys(list(existing_notes) + list(notes))
                    )
                    item.revision_count += 1
                    item.status = ContentStatus.UNDER_REVIEW

        state.revision_count += 1

        await complete_agent_run(
            state,
            run["id"],
            {"revised": True, "revision_count": state.revision_count},
        )

        return {
            "generated_content": state.generated_content,
            "revision_count": state.revision_count,
            "agent_runs": state.agent_runs,
            "current_agent": state.current_agent,
        }

    except Exception as e:
        await complete_agent_run(state, run["id"], {}, error=str(e))
        state.errors.append(f"Content Revision error: {str(e)}")
        return {
            "errors": state.errors,
            "agent_runs": state.agent_runs,
        }
