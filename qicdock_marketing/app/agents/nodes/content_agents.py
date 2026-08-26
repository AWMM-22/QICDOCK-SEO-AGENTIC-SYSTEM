import logging
from uuid import uuid4

from app.agents.state.marketing_state import (
    MarketingState,
    GeneratedContent,
    GeneratedContentItem,
    ContentType,
    ContentStatus,
    InstagramContentSet,
    ReelContentSet,
    StoryContentSet,
)
from app.agents.nodes.base import create_agent_run, complete_agent_run, llm_usage_kwargs
from app.db.models.agents import AgentType
from app.core.providers.llm.factory import get_llm_provider
from app.core.providers.llm.base import LLMMessage

logger = logging.getLogger(__name__)


def _brand_context_text(state: MarketingState) -> str:
    bc = state.brand_context
    if not bc:
        return "Brand voice: Professional, helpful. Tone: Friendly, informative."
    return (
        f"Brand voice: {bc.brand_voice or 'N/A'}\n"
        f"Tone: {bc.tone or 'N/A'}\n"
        f"Words to use: {bc.words_to_use}\n"
        f"Words to avoid (NEVER use these): {bc.words_to_avoid}\n"
        f"Do not make claims beyond these verified claims: {bc.marketing_claims}"
    )


def _product_context_text(state: MarketingState) -> str:
    if not state.product_context:
        return "No product context available."
    p = state.product_context[0]
    return (
        f"Product: {p.name}\nDescription: {p.description}\n"
        f"Features: {p.features}\nBenefits: {p.benefits}\nUSPs: {p.usp}\n"
        f"Pain points solved: {p.pain_points_solved}\nUse cases: {p.use_cases}"
    )


def _strategy_items_text(items) -> str:
    parts = []
    for i, item in enumerate(items):
        parts.append(
            f"[{i}] topic={item.topic} | objective={item.objective} | audience={item.audience} "
            f"| angle={item.angle} | hook_hint={item.hook} | cta_hint={item.cta}"
        )
    return "\n".join(parts)


async def instagram_agent_node(state: MarketingState) -> dict:
    run = await create_agent_run(state, AgentType.INSTAGRAM, {"content_types": ["post", "carousel"]})

    strategy_items = [
        item for item in state.content_strategy.items
        if item.format in [ContentType.POST, ContentType.CAROUSEL]
    ] if state.content_strategy else []

    generated_items = []
    usage = {}

    try:
        if strategy_items:
            llm = get_llm_provider()
            messages = [
                LLMMessage(
                    role="system",
                    content=(
                        "You are the Instagram Content Agent for Qicdock. Generate Instagram feed "
                        "posts and carousels based strictly on the strategy items and product "
                        "facts provided. For each item create: hook, caption, CTA, hashtags, "
                        "visual concept, image generation prompt. For carousel items also provide "
                        "slide-by-slide content (3-6 slides). Never invent product features, "
                        "specs, statistics or testimonials.\n\n"
                        f"{_brand_context_text(state)}"
                    ),
                ),
                LLMMessage(
                    role="user",
                    content=(
                        f"{_product_context_text(state)}\n\n"
                        f"Strategy items ({len(strategy_items)}):\n{_strategy_items_text(strategy_items)}\n\n"
                        f"Audience insights: {state.audience_insights.model_dump() if state.audience_insights else 'N/A'}\n\n"
                        "Generate exactly one content item per strategy item, in order."
                    ),
                ),
            ]

            result = await llm.generate_structured(messages, InstagramContentSet, temperature=0.8)
            usage = llm_usage_kwargs(result)

            for strategy_item, copy_item in zip(strategy_items, result.items):
                generated_items.append(
                    GeneratedContentItem(
                        content_id=uuid4(),
                        content_type=strategy_item.format,
                        platform="instagram",
                        title=f"{strategy_item.format.value.title()} - {strategy_item.topic}",
                        content={
                            "hook": copy_item.hook,
                            "caption": copy_item.caption,
                            "angle": strategy_item.angle,
                            **({"carousel_slides": copy_item.carousel_slides} if copy_item.carousel_slides else {}),
                        },
                        visual_concept=copy_item.visual_concept or strategy_item.visual_requirement,
                        image_prompt=copy_item.image_prompt,
                        hashtags=copy_item.hashtags,
                        cta=copy_item.cta,
                        status=ContentStatus.GENERATED,
                    )
                )
    except Exception as e:
        logger.warning("Instagram Agent LLM failed: %s", e)
        state.errors.append(f"Instagram Agent error: {str(e)}")

    await complete_agent_run(state, run["id"], {"generated_count": len(generated_items)}, **usage)

    return {
        "pending_content_items": [i.model_dump(mode="json") for i in generated_items],
        "errors": state.errors,
        "agent_runs": state.agent_runs,
        "current_agent": state.current_agent,
    }


async def reels_agent_node(state: MarketingState) -> dict:
    run = await create_agent_run(state, AgentType.REELS, {"content_types": ["reel"]})

    strategy_items = [
        item for item in state.content_strategy.items
        if item.format == ContentType.REEL
    ] if state.content_strategy else []

    generated_items = []
    usage = {}

    try:
        if strategy_items:
            llm = get_llm_provider()
            messages = [
                LLMMessage(
                    role="system",
                    content=(
                        "You are the Reels Content Agent for Qicdock. Generate short-form video "
                        "concepts based strictly on the strategy items and product facts. For "
                        "each reel create: hook, duration (seconds), script voiceover text, "
                        "scene-by-scene breakdown (duration, visual, voiceover, on-screen text), "
                        "caption, CTA, hashtags, cover image prompt. Prioritize engaging "
                        "storytelling over plain product promotion. Never invent features or "
                        "claims.\n\n"
                        f"{_brand_context_text(state)}"
                    ),
                ),
                LLMMessage(
                    role="user",
                    content=(
                        f"{_product_context_text(state)}\n\n"
                        f"Strategy items ({len(strategy_items)}):\n{_strategy_items_text(strategy_items)}\n\n"
                        "Trending formats to consider: "
                        f"{state.trend_insights.trending_formats if state.trend_insights else 'N/A'}\n\n"
                        "Generate exactly one reel per strategy item, in order."
                    ),
                ),
            ]

            result = await llm.generate_structured(messages, ReelContentSet, temperature=0.8)
            usage = llm_usage_kwargs(result)

            for strategy_item, copy_item in zip(strategy_items, result.items):
                generated_items.append(
                    GeneratedContentItem(
                        content_id=uuid4(),
                        content_type=ContentType.REEL,
                        platform="instagram",
                        title=f"Reel - {strategy_item.topic}",
                        content={
                            "hook": copy_item.hook,
                            "duration": copy_item.duration,
                            "script": copy_item.script,
                            "scenes": [s.model_dump() for s in copy_item.scenes],
                            "caption": copy_item.caption,
                        },
                        visual_concept=strategy_item.visual_requirement,
                        image_prompt=copy_item.cover_image_prompt,
                        hashtags=copy_item.hashtags,
                        cta=copy_item.cta,
                        status=ContentStatus.GENERATED,
                    )
                )
    except Exception as e:
        logger.warning("Reels Agent LLM failed: %s", e)
        state.errors.append(f"Reels Agent error: {str(e)}")

    await complete_agent_run(state, run["id"], {"generated_count": len(generated_items)}, **usage)

    return {
        "pending_content_items": [i.model_dump(mode="json") for i in generated_items],
        "errors": state.errors,
        "agent_runs": state.agent_runs,
        "current_agent": state.current_agent,
    }


async def stories_agent_node(state: MarketingState) -> dict:
    run = await create_agent_run(state, AgentType.STORIES, {"content_types": ["story"]})

    strategy_items = [
        item for item in state.content_strategy.items
        if item.format == ContentType.STORY
    ] if state.content_strategy else []

    generated_items = []
    usage = {}

    try:
        if strategy_items:
            llm = get_llm_provider()
            messages = [
                LLMMessage(
                    role="system",
                    content=(
                        "You are the Stories Content Agent for Qicdock. Generate Instagram Story "
                        "sequences (5-7 frames each). Frame types: question, poll, problem, "
                        "solution, product, cta, quiz. Each frame has text and optional "
                        "interactive element (poll options / question prompt / slider). Stories "
                        "must flow as a narrative sequence. Base everything on the provided facts; "
                        "never invent features or claims.\n\n"
                        f"{_brand_context_text(state)}"
                    ),
                ),
                LLMMessage(
                    role="user",
                    content=(
                        f"{_product_context_text(state)}\n\n"
                        f"Strategy items ({len(strategy_items)}):\n{_strategy_items_text(strategy_items)}\n\n"
                        "Generate exactly one story sequence per strategy item, in order."
                    ),
                ),
            ]

            result = await llm.generate_structured(messages, StoryContentSet, temperature=0.8)
            usage = llm_usage_kwargs(result)

            for strategy_item, story_item in zip(strategy_items, result.items):
                generated_items.append(
                    GeneratedContentItem(
                        content_id=uuid4(),
                        content_type=ContentType.STORY,
                        platform="instagram",
                        title=f"Story Sequence - {strategy_item.topic}",
                        content={
                            "hook": story_item.hook,
                            "frames": [f.model_dump() for f in story_item.frames],
                            "caption": story_item.caption,
                        },
                        visual_concept=strategy_item.visual_requirement,
                        image_prompt=story_item.cover_image_prompt,
                        hashtags=story_item.hashtags,
                        cta=story_item.cta,
                        status=ContentStatus.GENERATED,
                    )
                )
    except Exception as e:
        logger.warning("Stories Agent LLM failed: %s", e)
        state.errors.append(f"Stories Agent error: {str(e)}")

    await complete_agent_run(state, run["id"], {"generated_count": len(generated_items)}, **usage)

    return {
        "pending_content_items": [i.model_dump(mode="json") for i in generated_items],
        "errors": state.errors,
        "agent_runs": state.agent_runs,
        "current_agent": state.current_agent,
    }


# ---------------------------------------------------------------------------
# Fan-in join node: merges items emitted by the parallel content agents.
# ---------------------------------------------------------------------------

def content_join_node(state: MarketingState) -> dict:
    metadata = dict(state.metadata)
    merged_ids: set = set(metadata.get("merged_content_ids", []))

    merged = GeneratedContent(items=state.generated_content.items if state.generated_content else [])
    for item_data in state.pending_content_items:
        item = GeneratedContentItem(**item_data)
        if item.content_id and str(item.content_id) not in merged_ids:
            merged.items.append(item)
            merged_ids.add(str(item.content_id))

    metadata["merged_content_ids"] = list(merged_ids)
    state.generated_content = merged

    return {
        "generated_content": merged,
        "metadata": metadata,
    }
