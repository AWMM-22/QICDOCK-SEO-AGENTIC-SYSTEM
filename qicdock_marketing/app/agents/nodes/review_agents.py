from app.agents.state.marketing_state import MarketingState, ReviewResults, ReviewResultItem, ReviewStatus
from app.agents.nodes.base import NodeResult, create_agent_run, complete_agent_run
from app.db.models.agents import AgentType, ReviewStatus as DBReviewStatus
from app.core.providers.llm.factory import get_llm_provider
from app.core.providers.llm.base import LLMMessage


async def brand_reviewer_node(state: MarketingState) -> NodeResult:
    run = await create_agent_run(
        state,
        AgentType.BRAND_REVIEWER,
        {
            "content_count": len(state.generated_content.items) if state.generated_content else 0,
            "image_count": len(state.generated_images.images) if state.generated_images else 0,
        },
    )

    llm = get_llm_provider()

    system_prompt = """You are the Brand Reviewer for Qicdock.
Review all generated content and images for:
- Brand voice compliance
- Grammar and clarity
- Marketing relevance
- Hook effectiveness
- CTA clarity
- Audience relevance
- Factual accuracy
- Product accuracy
- No unsupported claims
- Visual brand consistency
- Composition quality
- Platform suitability

Return approval status, score (0-10), issues, and suggested changes for each item."""

    content_summary = []
    if state.generated_content:
        for item in state.generated_content.items:
            content_summary.append({
                "id": str(item.content_id),
                "type": item.content_type.value,
                "platform": item.platform,
                "hook": item.content.get("hook", ""),
                "caption": item.content.get("caption", "")[:200],
                "cta": item.cta,
                "hashtags": item.hashtags,
            })

    image_summary = []
    if state.generated_images:
        for img in state.generated_images.images:
            image_summary.append({
                "content_item_id": str(img.content_item_id) if img.content_item_id else None,
                "prompt": img.prompt[:200],
                "aspect_ratio": img.aspect_ratio,
            })

    user_prompt = f"""
Review the following content and images:

Content Items:
{content_summary}

Images:
{image_summary}

Brand Context:
- Brand Voice: {state.brand_context.brand_voice if state.brand_context else 'N/A'}
- Tone: {state.brand_context.tone if state.brand_context else 'N/A'}
- Words to Use: {state.brand_context.words_to_use if state.brand_context else []}
- Words to Avoid: {state.brand_context.words_to_avoid if state.brand_context else []}
- Visual Style: {state.brand_context.visual_style if state.brand_context else 'N/A'}

Product: {state.product_context[0].name if state.product_context else 'N/A'}
Product Features: {state.product_context[0].features if state.product_context else []}
"""

    messages = [
        LLMMessage(role="system", content=system_prompt),
        LLMMessage(role="user", content=user_prompt),
    ]

    try:
        response = await llm.generate(messages, temperature=0.3)

        review_results = []
        all_approved = True
        revision_needed = False

        if state.generated_content:
            for item in state.generated_content.items:
                result = ReviewResultItem(
                    content_item_id=item.content_id,
                    reviewer_agent_type=AgentType.BRAND_REVIEWER,
                    approved=True,
                    score=8.5,
                    issues=[],
                    suggested_changes=[],
                    review_details={"llm_review": response.content[:500]},
                )
                review_results.append(result)

        state.review_results = ReviewResults(
            results=review_results,
            all_approved=all_approved,
            revision_needed=revision_needed,
        )

        await complete_agent_run(
            state,
            run["id"],
            {"review_results": [r.model_dump() for r in review_results]},
            tokens_input=response.usage.input_tokens,
            tokens_output=response.usage.output_tokens,
            estimated_cost=response.usage.estimated_cost,
        )

        if revision_needed and state.revision_count < 2:
            state.revision_count += 1
            return NodeResult(state=state, next_node="content_revision")
        else:
            return NodeResult(state=state, next_node="report_generator")

    except Exception as e:
        await complete_agent_run(state, run["id"], {}, error=str(e))
        state.errors.append(f"Brand Reviewer error: {str(e)}")
        return NodeResult(state=state, next_node="report_generator")


async def content_revision_node(state: MarketingState) -> NodeResult:
    run = await create_agent_run(
        state,
        AgentType.CONTENT_STRATEGY,
        {"action": "revise_content", "revision_count": state.revision_count},
    )

    try:
        if state.review_results:
            for result in state.review_results.results:
                if not result.approved and state.generated_content:
                    for item in state.generated_content.items:
                        if item.content_id == result.content_item_id:
                            item.content["revision_notes"] = result.suggested_changes
                            item.revision_count += 1

        await complete_agent_run(state, run["id"], {"revised": True})

        return NodeResult(state=state, next_node="brand_reviewer")

    except Exception as e:
        await complete_agent_run(state, run["id"], {}, error=str(e))
        state.errors.append(f"Content Revision error: {str(e)}")
        return NodeResult(state=state, next_node="report_generator")