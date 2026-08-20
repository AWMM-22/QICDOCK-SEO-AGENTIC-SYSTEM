from app.agents.state.marketing_state import MarketingState
from app.agents.nodes.base import NodeResult, create_agent_run, complete_agent_run
from app.db.models.agents import AgentType


async def visual_strategy_agent_node(state: MarketingState) -> NodeResult:
    run = await create_agent_run(
        state,
        AgentType.VISUAL,
        {"content_count": len(state.generated_content.items) if state.generated_content else 0},
    )

    try:
        if not state.generated_content or not state.generated_content.items:
            await complete_agent_run(state, run["id"], {"images_needed": 0})
            return NodeResult(state=state, next_node="brand_reviewer")

        visual_plan = []
        for item in state.generated_content.items:
            aspect_ratio = "4:5"
            if item.content_type.value in ["reel", "story"]:
                aspect_ratio = "9:16"
            elif item.content_type.value == "carousel":
                aspect_ratio = "4:5"

            visual_plan.append({
                "content_item_id": str(item.content_id),
                "content_type": item.content_type.value,
                "aspect_ratio": aspect_ratio,
                "visual_concept": item.visual_concept,
                "image_prompt": item.image_prompt,
                "product_images": state.product_context[0].images if state.product_context else [],
            })

        state.metadata["visual_plan"] = visual_plan

        await complete_agent_run(state, run["id"], {"visual_plan": visual_plan})

        return NodeResult(state=state, next_node="image_generation_agent")

    except Exception as e:
        await complete_agent_run(state, run["id"], {}, error=str(e))
        state.errors.append(f"Visual Strategy error: {str(e)}")
        return NodeResult(state=state, next_node="brand_reviewer")


async def image_generation_agent_node(state: MarketingState) -> NodeResult:
    run = await create_agent_run(
        state,
        AgentType.VISUAL,
        {"action": "generate_images", "visual_plan": state.metadata.get("visual_plan", [])},
    )

    try:
        visual_plan = state.metadata.get("visual_plan", [])
        generated_images = []

        for plan in visual_plan:
            generated_images.append({
                "content_item_id": plan["content_item_id"],
                "url": f"https://placeholder.com/{plan['aspect_ratio']}/qicdock-{plan['content_item_id']}.jpg",
                "prompt": plan["image_prompt"],
                "provider": "placeholder",
                "model": "placeholder",
                "aspect_ratio": plan["aspect_ratio"],
                "width": 1080 if plan["aspect_ratio"] == "4:5" else 1080,
                "height": 1350 if plan["aspect_ratio"] == "4:5" else 1920,
                "review_status": "pending",
            })

        from app.agents.state.marketing_state import GeneratedImages, GeneratedImage
        state.generated_images = GeneratedImages(
            images=[GeneratedImage(**img) for img in generated_images]
        )

        await complete_agent_run(state, run["id"], {"images_generated": len(generated_images)})

        return NodeResult(state=state, next_node="brand_reviewer")

    except Exception as e:
        await complete_agent_run(state, run["id"], {}, error=str(e))
        state.errors.append(f"Image Generation error: {str(e)}")
        return NodeResult(state=state, next_node="brand_reviewer")