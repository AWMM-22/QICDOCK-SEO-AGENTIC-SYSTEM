from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator
import logging
from datetime import date

from app.services.llm_provider import get_llm_provider
from app.services.tavily_search import get_tavily_search

logger = logging.getLogger(__name__)


import json

class MarketResearchOutput(BaseModel):
    audience_segments: List[str] = Field(default_factory=list)
    pain_points: List[str] = Field(default_factory=list)
    needs: List[str] = Field(default_factory=list)
    motivations: List[str] = Field(default_factory=list)
    market_trends: List[str] = Field(default_factory=list)
    competitor_insights: List[str] = Field(default_factory=list)
    market_gaps: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)

    @field_validator("audience_segments", "pain_points", "needs", "motivations", "market_trends", "competitor_insights", "market_gaps", "opportunities", "sources", mode="before")
    @classmethod
    def _normalize_list(cls, v: Any) -> List[str]:
        if isinstance(v, list):
            res = []
            for item in v:
                if isinstance(item, str):
                    res.append(item)
                elif isinstance(item, dict):
                    res.append(json.dumps(item))
                else:
                    res.append(str(item))
            return res
        elif isinstance(v, dict):
            return [f"{k}: {json.dumps(val) if isinstance(val, (dict, list)) else val}" for k, val in v.items()]
        elif isinstance(v, str):
            return [v]
        return []


class MarketResearchAgent:
    def __init__(self):
        self.llm = get_llm_provider()
        self.tavily = get_tavily_search()

    def _gather_external_intelligence(
        self,
        start_date: date,
        end_date: date,
        platforms: List[str],
        festivals: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Gather external intelligence using Tavily"""
        intelligence = {
            "competitor_insights": [],
            "market_trends": [],
            "festival_relevance": {},
            "content_gaps": [],
            "sources": []
        }

        try:
            # Search for competitor patterns
            competitor_results = self.tavily.search_competitors("Qicdock", "car wireless charger")
            for r in competitor_results:
                intelligence["competitor_insights"].append(r.get("content", "")[:300])
                intelligence["sources"].append(r.get("url", ""))

            # Search for trends on each platform
            for platform in platforms[:2]:
                trend_results = self.tavily.search_trends("car wireless charger automotive accessories", platform)
                for r in trend_results:
                    intelligence["market_trends"].append(f"[{platform}] {r.get('content', '')[:200]}")
                    intelligence["sources"].append(r.get("url", ""))

            # Search festival relevance (max 2 festivals)
            for festival in festivals[:2]:
                fest_results = self.tavily.search_festival_relevance(festival["name"], "Qicdock", "car accessories")
                intelligence["festival_relevance"][festival["name"]] = [
                    r.get("content", "")[:200] for r in fest_results
                ]
                for r in fest_results:
                    intelligence["sources"].append(r.get("url", ""))
        except Exception as e:
            logger.warning(f"[MARKET RESEARCH] External Tavily search skipped/failed: {e}")

        # Deduplicate sources
        intelligence["sources"] = list(set(intelligence["sources"]))

        return intelligence

    def _build_research_prompt(
        self,
        start_date: date,
        end_date: date,
        platforms: List[str],
        objective: Optional[str],
        festivals: List[Dict[str, str]],
        brand_context: str,
        external_intel: Dict[str, Any]
    ) -> str:
        festival_info = "\n".join([f"- {f['date']}: {f['name']}" for f in festivals]) if festivals else "None significant"

        competitor_info = "\n".join([f"- {c}" for c in external_intel.get("competitor_insights", [])[:5]]) or "No external competitor data available"
        trends_info = "\n".join([f"- {t}" for t in external_intel.get("market_trends", [])[:5]]) or "No external trend data available"
        gaps_info = "\n".join([f"- {g}" for g in external_intel.get("content_gaps", [])[:3]]) or "No external gap data available"

        festival_relevance_info = ""
        for fest_name, relevance in external_intel.get("festival_relevance", {}).items():
            if relevance:
                festival_relevance_info += f"\n{fest_name}: {'; '.join(relevance[:2])}"

        prompt = f"""
You are the Market & Audience Research Agent for Qicdock. Provide current marketing intelligence to inform the monthly calendar planning.

## PLANNING CONTEXT
**Period**: {start_date} to {end_date}
**Platforms**: {', '.join(platforms)}
**Objective**: {objective or "General brand awareness and engagement"}
**Key Festivals/Occasions**: 
{festival_info}

## BRAND CONTEXT (VERIFIED - DO NOT OVERRIDE)
{brand_context}

## EXTERNAL MARKET INTELLIGENCE (from Tavily web search)

### Competitor Insights:
{competitor_info}

### Market Trends (Instagram/LinkedIn):
{trends_info}

### Festival Relevance Research:
{festival_relevance_info or "No specific festival research available"}

### Content Gaps Identified:
{gaps_info}

Sources: {', '.join(external_intel.get('sources', [])[:5])}

## RESEARCH QUESTIONS
Answer these specific planning questions using the external intelligence above:

1. **Audience**: Who are the primary segments for car wireless chargers in India right now? What are their demographics, behaviors, platform preferences?

2. **Pain Points**: What are the current frustrations with car charging? Cable mess, slow charging, phone falling, incompatible mounts, overheating?

3. **Needs & Motivations**: What drives purchase decisions? Convenience, safety, aesthetics, status, technology adoption?

4. **Market Trends**: What content formats are gaining traction on Instagram/LinkedIn for automotive tech accessories? Reels vs carousels? Educational vs lifestyle? UGC vs polished?

5. **Competitor Patterns**: What are competing wireless charger brands doing? What messaging, formats, frequency?

6. **Market Gaps**: What's missing in current market communication? What audience needs are unaddressed?

7. **Opportunities**: Specific opportunities for Qicdock in this period? Festival relevance? Seasonal driving patterns? New car launches?

8. **Festival Relevance**: For each festival listed, assess: Is it relevant to car owners/commuters? Can Qicdock naturally participate? What angle would work?

## CONSTRAINTS
- Do NOT overwrite verified brand facts from Qicdock knowledge base
- External insights supplement, never replace, verified product specifications
- Focus on actionable insights for content planning
- Be specific to Indian market context

## OUTPUT
Return ONLY valid, complete JSON matching MarketResearchOutput schema. Keep string elements concise (1-2 sentences per point) so the JSON is completely formed.
"""
        return prompt

    def research(
        self,
        start_date: date,
        end_date: date,
        platforms: List[str],
        objective: Optional[str],
        festivals: List[Dict[str, str]],
        brand_context: str
    ) -> MarketResearchOutput:
        # Gather external intelligence first
        logger.info("Gathering external market intelligence via Tavily...")
        external_intel = self._gather_external_intelligence(start_date, end_date, platforms, festivals)

        prompt = self._build_research_prompt(
            start_date, end_date, platforms, objective, festivals, brand_context, external_intel
        )

        logger.info(f"Conducting market research for {start_date} to {end_date}")
        result = self.llm.generate_structured(prompt, MarketResearchOutput, temperature=0.5)
        
        # Add sources to result
        result.sources = external_intel.get("sources", [])
        
        logger.info(f"Market research complete: {len(result.opportunities)} opportunities identified")
        return result


def get_market_research_agent() -> MarketResearchAgent:
    return MarketResearchAgent()