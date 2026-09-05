from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
from pydantic import BaseModel, Field
import logging

from app.services.llm_provider import get_llm_provider
from app.knowledge.knowledge_base import get_knowledge_base

logger = logging.getLogger(__name__)


from pydantic import BaseModel, Field, field_validator

class CalendarEntryPlan(BaseModel):
    date: str = Field(description="Date in YYYY-MM-DD format")
    platform: str = Field(description="Platform: instagram or linkedin")
    content_type: str = Field(description="Content format type")
    title: str = Field(description="Brief title for the post")
    objective: str = Field(description="Marketing objective")
    content_pillar: str = Field(description="Content pillar/category")
    product: Optional[str] = Field(default=None, description="Product to feature")
    audience: str = Field(description="Target audience segment")
    reason: str = Field(description="Strategic reasoning for this date and content")
    sequence_position: int = Field(description="Position in the overall sequence")
    campaign_thread: Optional[str] = Field(default=None, description="Campaign thread identifier")
    follows_entry: Optional[str] = Field(default=None, description="Date of entry this follows")
    supports_entry: Optional[str] = Field(default=None, description="Date of entry this supports")

    @field_validator("sequence_position", mode="before")
    @classmethod
    def _normalize_seq(cls, v: Any) -> int:
        try:
            return int(v)
        except Exception:
            return 1


class CalendarPlanOutput(BaseModel):
    plan_status: str = Field(default="ready")
    strategy_summary: str = Field(description="Overall marketing strategy for the month")
    recommended_frequency: Dict[str, str] = Field(default_factory=dict)
    calendar_entries: List[CalendarEntryPlan] = Field(default_factory=list)

    @field_validator("recommended_frequency", mode="before")
    @classmethod
    def _normalize_frequency(cls, v: Any) -> Dict[str, str]:
        if isinstance(v, dict):
            return {str(k): str(val) for k, val in v.items()}
        if isinstance(v, str):
            return {"general": v}
        return {}


INSTAGRAM_CONTENT_TYPES = [
    "single_image", "carousel", "reel", "story", "story_sequence",
    "product_showcase", "educational", "problem_solution", "comparison",
    "community", "ugc_style", "promotional"
]

LINKEDIN_CONTENT_TYPES = [
    "text_post", "image_post", "document_carousel", "educational",
    "product_insight", "brand_story", "industry_insight", "case_study",
    "problem_solution"
]

INDIAN_FESTIVALS_2026 = {
    "2026-01-14": "Makar Sankranti",
    "2026-01-26": "Republic Day",
    "2026-02-26": "Maha Shivaratri",
    "2026-03-03": "Holi",
    "2026-03-22": "Ugadi/Gudi Padwa",
    "2026-03-30": "Ram Navami",
    "2026-04-10": "Eid al-Fitr",
    "2026-04-14": "Ambedkar Jayanti",
    "2026-05-01": "Maharashtra Day",
    "2026-08-15": "Independence Day",
    "2026-08-27": "Janmashtami",
    "2026-09-05": "Teacher's Day",
    "2026-09-19": "Ganesh Chaturthi",
    "2026-10-02": "Gandhi Jayanti",
    "2026-10-20": "Dussehra",
    "2026-10-21": "Diwali",
    "2026-11-01": "Kannada Rajyotsava",
    "2026-11-14": "Children's Day",
    "2026-12-25": "Christmas",
}


class CalendarPlannerAgent:
    def __init__(self):
        self.llm = get_llm_provider()
        self.knowledge_base = get_knowledge_base()

    def _get_relevant_festivals(self, start_date: date, end_date: date) -> List[Dict[str, str]]:
        festivals = []
        current = start_date
        while current <= end_date:
            date_str = current.strftime("%Y-%m-%d")
            if date_str in INDIAN_FESTIVALS_2026:
                festivals.append({"date": date_str, "name": INDIAN_FESTIVALS_2026[date_str]})
            current += timedelta(days=1)
        return festivals

    def _build_planner_prompt(
        self,
        start_date: date,
        end_date: date,
        platforms: List[str],
        objective: Optional[str],
        additional_instructions: Optional[str],
        brand_context: List[Dict],
        product_context: List[Dict],
        festivals: List[Dict],
        existing_entries: List[Dict]
    ) -> str:
        total_days = (end_date - start_date).days + 1
        platforms_str = ", ".join(platforms)
        
        brand_info = "\n".join([f"- {item['content'][:150]}" for item in brand_context[:3]])
        product_info = "\n".join([f"- {item['content'][:150]}" for item in product_context[:4]])
        festival_info = "\n".join([f"- {f['date']}: {f['name']}" for f in festivals]) if festivals else "None in this period"
        
        existing_info = ""
        if existing_entries:
            existing_info = "\nExisting planned entries:\n" + "\n".join([
                f"- {e['date']} ({e['platform']}): {e['title']} [{e['content_type']}]"
                for e in existing_entries
            ])

        prompt = f"""
You are the Calendar Brain for Qicdock, an AI marketing strategist that plans realistic monthly marketing calendars.

## CONTEXT
**Date Range**: {start_date} to {end_date} ({total_days} days)
**Platforms**: {platforms_str}
**Marketing Objective**: {objective or "General brand awareness and engagement"}
**Additional Instructions**: {additional_instructions or "None"}

## BRAND KNOWLEDGE (from verified brand documents)
{brand_info}

## PRODUCT KNOWLEDGE (verified product catalog)
{product_info}

## RELEVANT FESTIVALS/OCCASIONS IN THIS PERIOD
{festival_info}

{existing_info}

## YOUR TASK
Create a strategic monthly marketing calendar. You MUST:
1. Decide WHICH days deserve content (NOT every day)
2. Decide WHICH platform for each entry
3. Decide WHAT content format for each entry
4. Decide WHICH product/audience/pillar for each entry
5. Provide STRATEGIC REASONING for each decision
6. Ensure SEQUENCING creates a marketing journey (awareness → problem → solution → engagement → conversion)

## CRITICAL RULES
- DO NOT generate content for every day. Leave days empty strategically.
- DO NOT auto-post for festivals. Evaluate relevance: Is it relevant to Qicdock's audience? Can Qicdock naturally participate? Would it feel forced?
- Instagram and LinkedIn must have DIFFERENT content, not identical cross-posts.
- Balance content pillars: Education, Awareness, Problem/Solution, Product, Engagement, Storytelling, Conversion.
- Avoid repetitive formats, products, or promotional content.
- Maintain platform-specific behavior (Instagram=visual, LinkedIn=professional).
- Sequence logically: Awareness → Problem/Pain Point → Product Solution → Education/Value → Engagement → Conversion.

## PLATFORM CONTENT TYPES
**Instagram**: {', '.join(INSTAGRAM_CONTENT_TYPES)}
**LinkedIn**: {', '.join(LINKEDIN_CONTENT_TYPES)}

## OUTPUT FORMAT
Return a JSON object with:
- strategy_summary: Overall strategy explanation
- recommended_frequency: {{"instagram": "...", "linkedin": "..."}}
- calendar_entries: Array of entries, each with:
  - date (YYYY-MM-DD)
  - platform (instagram/linkedin)
  - content_type (from above lists)
  - title (brief)
  - objective (awareness/engagement/consideration/conversion)
  - content_pillar (education/awareness/problem_solution/product/engagement/storytelling/conversion)
  - product (product name or null)
  - audience (target segment)
  - reason (strategic reasoning)
  - sequence_position (1, 2, 3...)
  - campaign_thread (identifier like "wireless_charging_awareness")
  - follows_entry (date string or null)
  - supports_entry (date string or null)

Example entry:
{{
  "date": "2026-09-04",
  "platform": "instagram",
  "content_type": "reel",
  "title": "The everyday problem your car setup can solve",
  "objective": "awareness",
  "content_pillar": "problem_solution",
  "product": "Qicdock Wireless Charger",
  "audience": "daily commuters",
  "reason": "Follows previous awareness content with problem-solution format, creates natural transition toward product consideration",
  "sequence_position": 1,
  "campaign_thread": "wireless_charging_awareness",
  "follows_entry": null,
  "supports_entry": null
}}

Return ONLY valid JSON matching the CalendarPlanOutput schema.
"""
        return prompt

    def plan_month(
        self,
        start_date: date,
        end_date: date,
        platforms: List[str],
        objective: Optional[str],
        additional_instructions: Optional[str],
        existing_entries: Optional[List[Dict]] = None
    ) -> CalendarPlanOutput:
        # Retrieve compact brand context (top 2 chunks)
        brand_context = self.knowledge_base.query_brand_context(
            "Qicdock brand voice positioning values", n_results=2
        )
        
        # Retrieve compact product context (top 3 chunks)
        product_context = self.knowledge_base.query_product_context(
            "Qicdock wireless charger car features", n_results=3
        )

        # Get relevant festivals
        festivals = self._get_relevant_festivals(start_date, end_date)

        # Build prompt
        prompt = self._build_planner_prompt(
            start_date, end_date, platforms, objective, additional_instructions,
            brand_context, product_context, festivals, existing_entries or []
        )

        # Generate plan with single strategic call
        logger.info(f"[CALENDAR BRAIN] Making strategic planning call for period {start_date} to {end_date}")
        result = self.llm.generate_structured(prompt, CalendarPlanOutput, temperature=0.7)
        
        logger.info(f"[CALENDAR BRAIN] Generated strategic plan with {len(result.calendar_entries)} entries")
        return result


def get_calendar_planner() -> CalendarPlannerAgent:
    return CalendarPlannerAgent()