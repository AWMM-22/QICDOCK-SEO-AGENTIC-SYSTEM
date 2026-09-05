from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import logging

from app.services.llm_provider import get_llm_provider
from app.knowledge.knowledge_base import get_knowledge_base

logger = logging.getLogger(__name__)


from pydantic import BaseModel, Field, model_validator

class ReviewOutput(BaseModel):
    status: str = Field(description="approved, needs_revision, or failed")
    score: float = Field(description="0.0 to 1.0 quality score")
    issues: List[str] = Field(default_factory=list, description="List of issues found")
    corrections: List[str] = Field(default_factory=list, description="Specific corrections needed")

    @model_validator(mode="before")
    @classmethod
    def _normalize_keys(cls, data: Any) -> Any:
        if isinstance(data, dict):
            new_data = {}
            for k, v in data.items():
                k_str = str(k).lower().replace(" ", "_")
                if k_str in ("status",):
                    new_data["status"] = str(v).lower() if v else "approved"
                elif k_str in ("score", "rating"):
                    try:
                        new_data["score"] = float(v)
                    except Exception:
                        new_data["score"] = 0.95
                elif k_str in ("issues", "issue_list"):
                    new_data["issues"] = [str(x) for x in v] if isinstance(v, list) else ([str(v)] if v else [])
                elif k_str in ("corrections", "correction_list"):
                    new_data["corrections"] = [str(x) for x in v] if isinstance(v, list) else ([str(v)] if v else [])
                else:
                    new_data[k_str] = v
            return new_data
        return data


class BrandReviewerAgent:
    def __init__(self):
        self.llm = get_llm_provider()
        self.knowledge_base = get_knowledge_base()

    def _build_review_prompt(
        self,
        recommendation: Dict[str, Any],
        entry_plan: Dict[str, Any],
        brand_context: List[Dict],
        product_context: List[Dict],
        surrounding_entries: List[Dict]
    ) -> str:
        platform = entry_plan.get('platform', 'instagram')
        content_type = entry_plan.get('content_type', 'single_image')
        product = entry_plan.get('product', '')
        objective = entry_plan.get('objective', 'awareness')
        content_pillar = entry_plan.get('content_pillar', 'education')

        brand_info = "\n".join([f"- {item['content'][:400]}" for item in brand_context[:3]])
        product_info = "\n".join([f"- {item['content'][:400]}" for item in product_context[:3]])

        surrounding_info = ""
        if surrounding_entries:
            surrounding_info = "\nSurrounding calendar context:\n"
            for se in surrounding_entries:
                surrounding_info += f"- {se.get('date', '')} ({se.get('platform', '')}): {se.get('title', '')} [{se.get('content_type', '')}]\n"

        prompt = f"""
You are the Brand Reviewer for Qicdock. Review the generated content recommendation for brand alignment, product accuracy, marketing quality, and calendar quality.

## ENTRY PLAN
**Date**: {entry_plan.get('date', '')}
**Platform**: {platform}
**Content Type**: {content_type}
**Product**: {product or 'General brand'}
**Objective**: {objective}
**Content Pillar**: {content_pillar}

{surrounding_info}

## GENERATED RECOMMENDATION
**Hook**: {recommendation.get('hook', '')}
**Angle**: {recommendation.get('concept', '')}
**Content Structure**: {recommendation.get('caption_direction', '')}
**Caption**: {recommendation.get('visual_direction', '')}
**CTA**: {recommendation.get('cta', '')}
**Creative Prompt**: {recommendation.get('image_prompt', '')}

## VERIFIED BRAND KNOWLEDGE
{brand_info}

## VERIFIED PRODUCT KNOWLEDGE
{product_info}

## REVIEW CRITERIA
Score each area 0.0-1.0, then provide overall score:

### 1. BRAND ALIGNMENT (weight: 30%)
- Brand voice: clean, smart, adaptive, effortless
- Positioning: "Made for the way life moves", technology that fits naturally
- Messaging: Modular, freedom to customize, seamless integration
- Visual identity: Clean, minimal, lifestyle-oriented

### 2. PRODUCT ACCURACY (weight: 30%)
- Features: ONLY use verified features (Precision Fit, One-Hand Operation, Dual-Mode Design, Easy Undocking, MagSafe & Qi Compatibility, 6-Month Warranty, Universal Fit, Movable Docking, Strong Magnetic Grip, Advanced PCB Technology, Fast Wireless Charging, Fixed Base Mounting, Advanced Cooling PCB)
- Benefits: Hands-free charging, cable-free, cleaner console, car-specific fit
- Specifications: Car-specific models (XUV 3XO, Glanza, Taisor, Dzire, Swift, Baleno, Ertiga, Fronx) + Universal (Movable/Fixed)
- Claims: Do not exaggerate charging speed, compatibility, or warranty

### 3. MARKETING QUALITY (weight: 25%)
- Relevance to target audience (daily commuters, car owners, tech-savvy professionals)
- Usefulness: Does it solve a problem or provide value?
- Audience fit: Language, tone, format appropriate for platform
- CTA: Clear, actionable, not pushy
- Originality: Fresh concept, not generic template

### 4. CALENDAR QUALITY (weight: 15%)
- Repetition: Not repeating same concept/format/product recently
- Frequency: Appropriate spacing from other posts
- Platform fit: Content truly adapted to {platform}, not cross-posted
- Sequence quality: Logically follows previous, sets up next
- Strategic relevance: Serves the {objective} objective

### 5. OCCASION QUALITY (if applicable)
- Is the event actually relevant to Qicdock?
- Is the connection natural?
- Is the recommendation forced?

## OUTPUT
Return JSON with:
- status: "approved" (score >= 0.8), "needs_revision" (score 0.5-0.79), "failed" (score < 0.5)
- score: Overall weighted score 0.0-1.0
- issues: Specific issues found (empty if approved)
- corrections: Specific actionable corrections (empty if approved)

Be thorough but fair. Minor style preferences are not issues. Factual inaccuracies, brand misalignment, or strategic flaws are issues.
"""
        return prompt

    def review_recommendation(
        self,
        recommendation: Dict[str, Any],
        entry_plan: Dict[str, Any],
        surrounding_entries: Optional[List[Dict]] = None
    ) -> ReviewOutput:
        # Retrieve brand context for review
        brand_context = self.knowledge_base.query_brand_context(
            "Qicdock brand voice visual identity do's don'ts positioning", n_results=3
        )
        
        # Retrieve product context
        product = entry_plan.get('product', '')
        if product:
            product_context = self.knowledge_base.query_product_context(
                f"{product} features benefits specifications", n_results=3
            )
        else:
            product_context = self.knowledge_base.query_product_context(
                "Qicdock wireless charger features benefits", n_results=3
            )

        prompt = self._build_review_prompt(
            recommendation, entry_plan, brand_context, product_context, surrounding_entries or []
        )

        logger.info(f"Reviewing recommendation for {entry_plan.get('date')} ({entry_plan.get('platform')})")
        result = self.llm.generate_structured(prompt, ReviewOutput, temperature=0.3)
        
        logger.info(f"Review result: {result.status} (score: {result.score})")
        return result


def get_brand_reviewer() -> BrandReviewerAgent:
    return BrandReviewerAgent()