from app.agents.state.marketing_state import (
    MarketingState,
    GeneratedContent,
    GeneratedContentItem,
    ContentType,
    ContentStatus,
)
from app.agents.nodes.base import NodeResult, create_agent_run, complete_agent_run
from app.db.models.agents import AgentType
from app.core.providers.llm.factory import get_llm_provider
from app.core.providers.llm.base import LLMMessage
from uuid import uuid4


async def instagram_agent_node(state: MarketingState) -> NodeResult:
    run = await create_agent_run(
        state,
        AgentType.INSTAGRAM,
        {"content_types": ["post", "carousel"]},
    )

    llm = get_llm_provider()

    system_prompt = """You are the Instagram Content Agent for Qicdock.
Generate Instagram posts and carousels based on the content strategy.
For each item, create:
- Hook
- Caption
- CTA
- Hashtags
- Content angle
- Visual concept
- Image generation prompt

For carousels, also create slide-by-slide content."""

    strategy_items = [
        item for item in state.content_strategy.items
        if item.format in [ContentType.POST, ContentType.CAROUSEL]
    ]

    user_prompt = f"""
Generate Instagram content for {len(strategy_items)} strategy items.

Strategy Items:
{strategy_items}

Brand Voice: {state.brand_context.brand_voice if state.brand_context else 'Professional, helpful'}
Tone: {state.brand_context.tone if state.brand_context else 'Friendly, informative'}
Words to use: {state.brand_context.words_to_use if state.brand_context else []}
Words to avoid: {state.brand_context.words_to_avoid if state.brand_context else []}

Product: {state.product_context[0].name if state.product_context else 'Wireless Charger'}
Product Features: {state.product_context[0].features if state.product_context else []}
Product Benefits: {state.product_context[0].benefits if state.product_context else []}
"""

    messages = [
        LLMMessage(role="system", content=system_prompt),
        LLMMessage(role="user", content=user_prompt),
    ]

    try:
        response = await llm.generate(messages, temperature=0.8)

        generated_items = []
        for i, strategy_item in enumerate(strategy_items):
            item = GeneratedContentItem(
                content_id=uuid4(),
                content_type=strategy_item.format,
                platform="instagram",
                title=f"{strategy_item.format.value.title()} - {strategy_item.topic}",
                content={
                    "hook": strategy_item.hook,
                    "caption": f"Generated caption for {strategy_item.topic}",
                    "angle": strategy_item.angle,
                },
                visual_concept=strategy_item.visual_requirement,
                image_prompt=f"Marketing image for {strategy_item.topic}, {strategy_item.visual_requirement}",
                hashtags=strategy_item.hashtags,
                cta=strategy_item.cta,
                status=ContentStatus.GENERATED,
            )
            generated_items.append(item)

        if not state.generated_content:
            state.generated_content = GeneratedContent(items=[])
        state.generated_content.items.extend(generated_items)

        await complete_agent_run(
            state,
            run["id"],
            {"generated_count": len(generated_items)},
            tokens_input=response.usage.input_tokens,
            tokens_output=response.usage.output_tokens,
            estimated_cost=response.usage.estimated_cost,
        )

        return NodeResult(state=state, next_node="execute_content_agent")

    except Exception as e:
        await complete_agent_run(state, run["id"], {}, error=str(e))
        state.errors.append(f"Instagram Agent error: {str(e)}")
        return NodeResult(state=state, next_node="execute_content_agent")


async def reels_agent_node(state: MarketingState) -> NodeResult:
    run = await create_agent_run(
        state,
        AgentType.REELS,
        {"content_types": ["reel"]},
    )

    llm = get_llm_provider()

    system_prompt = """You are the Reels Content Agent for Qicdock.
Generate Reel scripts and specifications based on the content strategy.
For each Reel, create:
- Hook
- Duration
- Script
- Scene breakdown
- Voiceover
- On-screen text
- B-roll suggestions
- Product placement
- CTA
- Caption
- Hashtags
- Video generation prompt"""

    strategy_items = [
        item for item in state.content_strategy.items
        if item.format == ContentType.REEL
    ]

    user_prompt = f"""
Generate Reel content for {len(strategy_items)} strategy items.

Strategy Items:
{strategy_items}

Brand Voice: {state.brand_context.brand_voice if state.brand_context else 'Professional, helpful'}
Product: {state.product_context[0].name if state.product_context else 'Wireless Charger'}
"""

    messages = [
        LLMMessage(role="system", content=system_prompt),
        LLMMessage(role="user", content=user_prompt),
    ]

    try:
        response = await llm.generate(messages, temperature=0.8)

        generated_items = []
        for i, strategy_item in enumerate(strategy_items):
            item = GeneratedContentItem(
                content_id=uuid4(),
                content_type=ContentType.REEL,
                platform="instagram",
                title=f"Reel - {strategy_item.topic}",
                content={
                    "hook": strategy_item.hook,
                    "duration": 15,
                    "script": f"Generated script for {strategy_item.topic}",
                    "scenes": [
                        {"duration": 3, "visual": "Opening hook", "voiceover": strategy_item.hook, "text": strategy_item.hook},
                        {"duration": 5, "visual": "Product demo", "voiceover": "Watch how easy it is", "text": "Just dock and charge"},
                        {"duration": 4, "visual": "Lifestyle shot", "voiceover": "Clean setup, zero cables", "text": "Zero cables"},
                        {"duration": 3, "visual": "CTA", "voiceover": strategy_item.cta, "text": strategy_item.cta},
                    ],
                    "cta": strategy_item.cta,
                    "caption": f"Generated Reel caption for {strategy_item.topic}",
                },
                visual_concept=strategy_item.visual_requirement,
                image_prompt=f"Reel cover for {strategy_item.topic}",
                hashtags=strategy_item.hashtags,
                cta=strategy_item.cta,
                status=ContentStatus.GENERATED,
            )
            generated_items.append(item)

        if not state.generated_content:
            state.generated_content = GeneratedContent(items=[])
        state.generated_content.items.extend(generated_items)

        await complete_agent_run(
            state,
            run["id"],
            {"generated_count": len(generated_items)},
            tokens_input=response.usage.input_tokens,
            tokens_output=response.usage.output_tokens,
            estimated_cost=response.usage.estimated_cost,
        )

        return NodeResult(state=state, next_node="execute_content_agent")

    except Exception as e:
        await complete_agent_run(state, run["id"], {}, error=str(e))
        state.errors.append(f"Reels Agent error: {str(e)}")
        return NodeResult(state=state, next_node="execute_content_agent")


async def stories_agent_node(state: MarketingState) -> NodeResult:
    run = await create_agent_run(
        state,
        AgentType.STORIES,
        {"content_types": ["story"]},
    )

    llm = get_llm_provider()

    system_prompt = """You are the Stories Content Agent for Qicdock.
Generate Instagram Story sequences based on the content strategy.
For each Story sequence, create a series of story frames (5-7 frames).
Frame types: Question, Poll, Problem, Solution, Product, CTA, Quiz."""

    strategy_items = [
        item for item in state.content_strategy.items
        if item.format == ContentType.STORY
    ]

    user_prompt = f"""
Generate Story sequences for {len(strategy_items)} strategy items.

Strategy Items:
{strategy_items}

Brand Voice: {state.brand_context.brand_voice if state.brand_context else 'Professional, helpful'}
Product: {state.product_context[0].name if state.product_context else 'Wireless Charger'}
"""

    messages = [
        LLMMessage(role="system", content=system_prompt),
        LLMMessage(role="user", content=user_prompt),
    ]

    try:
        response = await llm.generate(messages, temperature=0.8)

        generated_items = []
        for i, strategy_item in enumerate(strategy_items):
            item = GeneratedContentItem(
                content_id=uuid4(),
                content_type=ContentType.STORY,
                platform="instagram",
                title=f"Story Sequence - {strategy_item.topic}",
                content={
                    "hook": strategy_item.hook,
                    "frames": [
                        {"type": "question", "text": "Tired of cable mess in your car?"},
                        {"type": "problem", "text": "Tangled cables, cluttered console"},
                        {"type": "solution", "text": "Qicdock - custom fit, zero cables"},
                        {"type": "product", "text": "Snaps perfectly in your console"},
                        {"type": "cta", "text": strategy_item.cta},
                    ],
                    "cta": strategy_item.cta,
                },
                visual_concept=strategy_item.visual_requirement,
                image_prompt=f"Story frame for {strategy_item.topic}",
                hashtags=strategy_item.hashtags,
                cta=strategy_item.cta,
                status=ContentStatus.GENERATED,
            )
            generated_items.append(item)

        if not state.generated_content:
            state.generated_content = GeneratedContent(items=[])
        state.generated_content.items.extend(generated_items)

        await complete_agent_run(
            state,
            run["id"],
            {"generated_count": len(generated_items)},
            tokens_input=response.usage.input_tokens,
            tokens_output=response.usage.output_tokens,
            estimated_cost=response.usage.estimated_cost,
        )

        return NodeResult(state=state, next_node="execute_content_agent")

    except Exception as e:
        await complete_agent_run(state, run["id"], {}, error=str(e))
        state.errors.append(f"Stories Agent error: {str(e)}")
        return NodeResult(state=state, next_node="execute_content_agent")