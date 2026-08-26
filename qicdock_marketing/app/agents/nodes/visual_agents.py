import base64
import logging
from pathlib import Path
from uuid import uuid4

from app.agents.state.marketing_state import (
    MarketingState,
    GeneratedImages,
    GeneratedImage,
)
from app.agents.nodes.base import create_agent_run, complete_agent_run, llm_usage_kwargs
from app.core.config.settings import settings
from app.core.providers.image.factory import get_image_provider
from app.db.models.agents import AgentType

logger = logging.getLogger(__name__)

ASPECT_DIMENSIONS = {
    "1:1": (1080, 1080),
    "4:5": (1080, 1350),
    "9:16": (1080, 1920),
    "16:9": (1920, 1080),
}


async def visual_strategy_agent_node(state: MarketingState) -> dict:
    run = await create_agent_run(
        state,
        AgentType.VISUAL,
        {"content_count": len(state.generated_content.items) if state.generated_content else 0},
    )

    try:
        from app.agents.nodes.prompt_engineering import build_image_prompt

        visual_plan = []
        if state.generated_content and state.generated_content.items:
            for idx, item in enumerate(state.generated_content.items):
                if item.content_type.value in ["reel", "story"]:
                    aspect_ratio = "9:16"
                else:
                    aspect_ratio = "4:5"

                product = state.product_context[0] if state.product_context else None
                engineered_prompt = build_image_prompt(
                    base_prompt=item.image_prompt or item.visual_concept or "",
                    content_type=item.content_type.value,
                    variation_index=idx,
                    product_name=product.name if product else None,
                    compatibility=(
                        (product.specifications or {}).get("compatibility") if product else None
                    ),
                    hook=item.content.get("hook"),
                    key_message=(item.content.get("caption") or "")[:60] or item.cta,
                )

                visual_plan.append({
                    "content_item_id": str(item.content_id) if item.content_id else None,
                    "content_type": item.content_type.value,
                    "aspect_ratio": aspect_ratio,
                    "visual_concept": item.visual_concept,
                    "image_prompt": item.image_prompt,
                    "engineered_prompt": engineered_prompt,
                    "product_images": state.product_context[0].images if state.product_context else [],
                })

        metadata = dict(state.metadata)
        metadata["visual_plan"] = visual_plan

        await complete_agent_run(state, run["id"], {"images_needed": len(visual_plan)})

        return {
            "metadata": metadata,
            "agent_runs": state.agent_runs,
            "current_agent": state.current_agent,
        }

    except Exception as e:
        await complete_agent_run(state, run["id"], {}, error=str(e))
        state.errors.append(f"Visual Strategy error: {str(e)}")
        return {
            "errors": state.errors,
            "agent_runs": state.agent_runs,
        }


def _save_image(data: bytes, content_item_id: str, mime_type: str) -> str:
    output_dir = Path("generated_images")
    output_dir.mkdir(parents=True, exist_ok=True)

    ext = "png" if "png" in (mime_type or "") else "jpg"
    path = output_dir / f"{content_item_id}.{ext}"
    path.write_bytes(data)
    return str(path)


def _save_video(data: bytes, content_item_id: str) -> str:
    output_dir = Path("generated_videos")
    output_dir.mkdir(parents=True, exist_ok=True)

    path = output_dir / f"{content_item_id}.mp4"
    path.write_bytes(data)
    return str(path)


def _load_reference_images(product_images: list) -> list[bytes]:
    """Load local product photos so the generated post features the real product."""
    refs: list[bytes] = []
    for src in (product_images or [])[:3]:
        if not src or str(src).startswith("http"):
            continue
        path = Path(str(src))
        if not path.is_absolute():
            path = Path("product_images") / str(src)
        try:
            if path.exists():
                refs.append(path.read_bytes())
        except Exception as e:
            logger.warning("Could not load reference image %s: %s", src, e)
    return refs


async def image_generation_agent_node(state: MarketingState) -> dict:
    """Build image PROMPT BRIEFS - no image generation.

    For every content item this produces:
    - a professional, copy-paste-ready image prompt
    - the product reference photo paths to use with it
    The email then shows prompt + reference photos inline so images can be
    generated manually in any tool (Higgsfield web app, etc).
    """
    run = await create_agent_run(
        state,
        AgentType.VISUAL,
        {"action": "build_prompt_briefs", "visual_plan": state.metadata.get("visual_plan", [])},
    )

    visual_plan = state.metadata.get("visual_plan", [])
    generated_images = []

    for plan in visual_plan:
        prompt = (
            plan.get("engineered_prompt")
            or plan.get("image_prompt")
            or plan.get("visual_concept")
            or ""
        )
        aspect_ratio = plan.get("aspect_ratio", "4:5")
        width, height = ASPECT_DIMENSIONS.get(aspect_ratio, (1080, 1350))

        # Reference photos = the product's own photos, resolved to local paths
        ref_paths = []
        for src in (plan.get("product_images") or [])[:3]:
            if not src or str(src).startswith("http"):
                continue
            path = Path(str(src))
            if not path.is_absolute():
                path = Path("product_images") / str(src)
            if path.exists():
                ref_paths.append(str(path))

        generated_images.append(
            GeneratedImage(
                content_item_id=plan.get("content_item_id"),
                url="|".join(ref_paths),  # reference photo paths (not a generated image)
                prompt=prompt,
                provider="prompt_brief",
                model="none",
                aspect_ratio=aspect_ratio,
                width=width,
                height=height,
                review_status="prompt_ready" if prompt else "skipped_no_prompt",
            )
        )

    state.generated_images = GeneratedImages(images=generated_images)

    metadata = dict(state.metadata)

    await complete_agent_run(
        state,
        run["id"],
        {
            "briefs_prepared": sum(1 for i in generated_images if i.review_status == "prompt_ready"),
            "note": "image generation disabled - prompts + reference photos prepared for manual generation",
        },
    )

    return {
        "generated_images": state.generated_images,
        "metadata": metadata,
        "errors": state.errors,
        "agent_runs": state.agent_runs,
        "current_agent": state.current_agent,
    }
