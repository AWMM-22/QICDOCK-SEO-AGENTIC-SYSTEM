from typing import List, Dict, Any, Optional
from datetime import date
from pydantic import BaseModel, Field
import logging

from app.services.llm_provider import get_llm_provider
from app.knowledge.knowledge_base import get_knowledge_base

logger = logging.getLogger(__name__)


from pydantic import BaseModel, Field, model_validator

import json

class ContentRecommendationOutput(BaseModel):
    """Actionable, publish-ready content recommendation output."""
    hook: str = Field(description="The actual opening hook that will appear in the content")
    angle: str = Field(description="ONE concise sentence explaining the marketing angle")
    content: str = Field(description="Structured content: slides for carousel, scenes for reel, frames for story, or main visual for single image")
    caption: str = Field(description="Actual publish-ready Instagram/LinkedIn caption")
    cta: str = Field(description="The exact CTA to use")
    hashtags: str = Field(description="5-10 highly relevant hashtags")
    creative_prompt: str = Field(description="Production-ready prompt for image/video generation")
    primary_kpi: str = Field(description="The ONE most important metric for this post")
    why: str = Field(description="1-2 sentences explaining why this post is strategically useful")

    @model_validator(mode="before")
    @classmethod
    def _normalize_keys(cls, data: Any) -> Any:
        if isinstance(data, dict):
            new_data = {}
            for k, v in data.items():
                k_str = str(k).lower().replace(" ", "_")
                val_str = json.dumps(v) if isinstance(v, (dict, list)) else (str(v) if v else "")
                if k_str in ("hook",):
                    new_data["hook"] = val_str
                elif k_str in ("angle", "marketing_angle"):
                    new_data["angle"] = val_str
                elif k_str in ("content", "content_structure"):
                    new_data["content"] = val_str
                elif k_str in ("caption", "caption_text"):
                    new_data["caption"] = val_str
                elif k_str in ("cta", "call_to_action"):
                    new_data["cta"] = val_str
                elif k_str in ("hashtags", "tags"):
                    new_data["hashtags"] = val_str
                elif k_str in ("creative_prompt", "creativeprompt", "image_prompt", "imageprompt"):
                    new_data["creative_prompt"] = val_str
                elif k_str in ("primary_kpi", "primarykpi", "kpi"):
                    new_data["primary_kpi"] = val_str
                elif k_str in ("why", "strategic_reason", "reason"):
                    new_data["why"] = val_str
                else:
                    new_data[k_str] = val_str
            return new_data
        return data


class ContentRecommendationAgent:
    def __init__(self):
        self.llm = get_llm_provider()
        self.knowledge_base = get_knowledge_base()

    def _build_recommendation_prompt(
        self,
        entry_plan: Dict[str, Any],
        brand_context: List[Dict],
        product_context: List[Dict],
        surrounding_entries: List[Dict],
        user_feedback: Optional[str] = None
    ) -> str:
        platform = entry_plan.get('platform', 'instagram')
        content_type = entry_plan.get('content_type', 'single_image')
        product = entry_plan.get('product', '')
        objective = entry_plan.get('objective', 'awareness')
        content_pillar = entry_plan.get('content_pillar', 'education')
        audience = entry_plan.get('audience', '')
        reason = entry_plan.get('reason', '')
        title = entry_plan.get('title', '')

        brand_info = "\n".join([f"- {item['content'][:200]}" for item in brand_context[:2]])
        product_info = "\n".join([f"- {item['content'][:200]}" for item in product_context[:2]])

        surrounding_info = ""
        if surrounding_entries:
            surrounding_info = "\nSurrounding calendar context (for sequencing):\n"
            for se in surrounding_entries:
                surrounding_info += f"- {se.get('date', '')} ({se.get('platform', '')}): {se.get('title', '')} [{se.get('content_type', '')}]\n"

        feedback_info = ""
        if user_feedback:
            feedback_info = f"\nUSER FEEDBACK FOR REGENERATION: {user_feedback}\nGenerate a meaningfully different recommendation addressing this feedback."

        # Determine content structure instructions based on content_type
        content_structure_guide = ""
        if content_type in ("carousel", "document_carousel"):
            content_structure_guide = """For CAROUSEL content field, provide:
- Slide 1: [description]
- Slide 2: [description]
- Slide 3: [description]
- ...
- Final CTA slide: [description]"""
        elif content_type == "reel":
            content_structure_guide = """For REEL content field, provide:
- Scene 1: [description]
- Scene 2: [description]
- Scene 3: [description]
- ...
- Final CTA: [description]"""
        elif content_type in ("story", "story_sequence"):
            content_structure_guide = """For STORY content field, provide:
- Frame 1: [description]
- Frame 2: [description]
- Frame 3: [description]
- CTA: [description]"""
        else:
            content_structure_guide = """For SINGLE IMAGE content field, provide:
- Main visual/message
- Optional text overlay"""

        prompt = f"""You are a practical social media marketing strategist.

Your job is to generate ONE actionable content recommendation that is ready to execute.

## ENTRY PLAN
**Date**: {entry_plan.get('date', '')}
**Platform**: {platform}
**Format**: {content_type}
**Title**: {title}
**Objective**: {objective}
**Content Pillar**: {content_pillar}
**Product**: {product or 'General brand'}
**Target Audience**: {audience}
**Strategic Context**: {reason}

{surrounding_info}
{feedback_info}

## BRAND CONTEXT
{brand_info}

## PRODUCT CONTEXT
{product_info}

## WHAT TO GENERATE

Return ONLY these fields:

1. **hook** — The actual opening hook that will appear in the content. Must grab attention instantly.

2. **angle** — ONE concise sentence explaining the marketing angle.

3. **content** — The actual content structure for this {content_type} post.
{content_structure_guide}
Do NOT provide a long conceptual explanation. Provide the actual structure.

4. **caption** — Generate the actual publish-ready caption for {platform}.
Do NOT give "caption direction". Write the ACTUAL caption that will be posted.
Do NOT explain the tone or structure separately.

5. **cta** — The exact CTA to use.

6. **hashtags** — 5-10 highly relevant hashtags. No huge lists.

7. **creative_prompt** — A production-ready prompt for the image/video generation model containing ONLY:
Subject, Product, Environment, Composition, Camera/perspective, Lighting, Style, Important product appearance requirements.
Do NOT repeat the marketing strategy inside the creative prompt.

8. **primary_kpi** — The ONE most important metric (e.g. Reach, Saves, Shares, Comments, Profile Visits, Link Clicks).

9. **why** — Maximum 1-2 sentences explaining why this post is strategically useful.

## IMPORTANT RULES
- Every field must help the user either understand what to post, create the post, publish the post, or measure its result.
- Do NOT generate unnecessary explanations or verbose marketing theory.
- Do NOT repeat information between fields.
- Never invent product features, prices, offers, reviews, statistics or claims not present in the supplied data.
- If a field is not relevant to this format, write "N/A" instead of generating filler.

TOKEN EFFICIENCY: Before generating a field, ask "Does this add something another field does not already provide?" If NO, keep it minimal.

Return ONLY valid JSON with these 9 fields: hook, angle, content, caption, cta, hashtags, creative_prompt, primary_kpi, why.
"""
        return prompt

    def generate_recommendation(
        self,
        entry_plan: Dict[str, Any],
        surrounding_entries: Optional[List[Dict]] = None,
        user_feedback: Optional[str] = None
    ) -> ContentRecommendationOutput:
        # Retrieve compact brand context (top 2 chunks)
        brand_context = self.knowledge_base.query_brand_context(
            f"Qicdock brand voice {entry_plan.get('platform', '')}", n_results=2
        )
        
        # Retrieve compact product context (top 2 chunks)
        product = entry_plan.get('product', '')
        if product:
            product_context = self.knowledge_base.query_product_context(
                f"{product} features", n_results=2
            )
        else:
            product_context = self.knowledge_base.query_product_context(
                "Qicdock wireless charger features", n_results=2
            )

        prompt = self._build_recommendation_prompt(
            entry_plan, brand_context, product_context, surrounding_entries or [], user_feedback
        )

        logger.info(f"[CONTENT AGENT] Generating recommendation for {entry_plan.get('date')} ({entry_plan.get('platform')}): '{entry_plan.get('title')}'")
        result = self.llm.generate_structured(prompt, ContentRecommendationOutput, temperature=0.7)
        
        return result


def get_content_recommendation_agent() -> ContentRecommendationAgent:
    return ContentRecommendationAgent()