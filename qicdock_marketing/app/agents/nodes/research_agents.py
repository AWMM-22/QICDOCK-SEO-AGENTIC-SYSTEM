import logging

from app.agents.state.marketing_state import (
    MarketingState,
    ProductAnalysis,
    AudienceInsights,
    ResearchData,
    ResearchSourceItem,
    CompetitorInsights,
)
from app.agents.nodes.base import create_agent_run, complete_agent_run, llm_usage_kwargs
from app.core.providers.llm.factory import get_llm_provider
from app.core.providers.llm.base import LLMMessage
from app.core.providers.search.factory import get_search_provider
from app.db.models.agents import AgentType

logger = logging.getLogger(__name__)


def _brand_summary(state: MarketingState) -> str:
    if not state.brand_context:
        return "No brand context available."
    bc = state.brand_context
    return (
        f"Brand story: {bc.brand_story or 'N/A'}\n"
        f"Brand voice: {bc.brand_voice or 'N/A'}\n"
        f"Tone: {bc.tone or 'N/A'}\n"
        f"Target audience: {bc.target_audience or 'N/A'}\n"
        f"Positioning: {bc.positioning or 'N/A'}\n"
        f"USPs: {bc.usp}\n"
        f"Marketing claims (verified only): {bc.marketing_claims}"
    )


async def product_analyst_agent_node(state: MarketingState) -> dict:
    run = await create_agent_run(
        state,
        AgentType.PRODUCT_ANALYST,
        {"product_ids": [str(pid) for pid in state.product_ids]},
    )

    analysis = ProductAnalysis()

    try:
        if not state.product_context:
            raise ValueError("Product information unavailable")

        products_desc = "\n\n".join(
            f"Product: {p.name}\nDescription: {p.description or 'N/A'}\n"
            f"Features: {p.features}\nBenefits: {p.benefits}\nUSPs: {p.usp}\n"
            f"Pain points solved: {p.pain_points_solved}\nUse cases: {p.use_cases}"
            f"\nEmotional benefits: {p.emotional_benefits}"
            f"\nFunctional benefits: {p.functional_benefits}"
            f"\nDifferentiators: {p.differentiators}"
            for p in state.product_context
        )

        llm = get_llm_provider()
        messages = [
            LLMMessage(
                role="system",
                content=(
                    "You are the Product Analyst Agent for Qicdock. Analyze the product "
                    "information and extract marketing insights. CRITICAL RULES: never invent "
                    "features, specifications, or claims that are not supported by the provided "
                    "information. Only reframe and organize what is given.\n\n"
                    f"Brand context:\n{_brand_summary(state)}"
                ),
            ),
            LLMMessage(
                role="user",
                content=(
                    f"Analyze this product information:\n{products_desc}\n\n"
                    f"Marketing objective: {state.request.goal}\n\n"
                    "Extract: main USP, secondary USPs, primary pain point solved, ideal use case, "
                    "target audience, emotional benefit, functional benefit, differentiators, "
                    "marketing angles, content opportunities."
                ),
            ),
        ]

        analysis = await llm.generate_structured(messages, ProductAnalysis, temperature=0.4)
        usage = llm_usage_kwargs(analysis)
    except Exception as e:
        logger.warning("Product Analyst LLM failed, falling back to raw fields: %s", e)
        state.errors.append(f"Product Analyst error: {str(e)}")
        usage = {}

        if state.product_context:
            p = state.product_context[0]
            analysis = ProductAnalysis(
                main_usp=p.usp[0] if p.usp else "",
                secondary_usps=p.usp[1:] if len(p.usp) > 1 else [],
                pain_point_solved=p.pain_points_solved[0] if p.pain_points_solved else "",
                ideal_use_case=p.use_cases[0] if p.use_cases else "",
                target_audience=p.target_audience or "",
                emotional_benefit=p.emotional_benefits[0] if p.emotional_benefits else "",
                functional_benefit=p.functional_benefits[0] if p.functional_benefits else "",
                differentiators=p.differentiators,
            )

    metadata = dict(state.metadata)
    metadata["product_analysis"] = analysis.model_dump()

    await complete_agent_run(
        state, run["id"], {"analysis": metadata["product_analysis"]}, **usage
    )

    return {
        "metadata": metadata,
        "errors": state.errors,
        "agent_runs": state.agent_runs,
    }


async def brand_knowledge_agent_node(state: MarketingState) -> dict:
    run = await create_agent_run(
        state,
        AgentType.BRAND_KNOWLEDGE,
        {"organization_id": str(state.organization_id)},
    )

    try:
        brand_info = {}
        if state.brand_context:
            brand_info = {
                "brand_story": state.brand_context.brand_story,
                "brand_voice": state.brand_context.brand_voice,
                "tone": state.brand_context.tone,
                "target_audience": state.brand_context.target_audience,
                "positioning": state.brand_context.positioning,
                "words_to_use": state.brand_context.words_to_use,
                "words_to_avoid": state.brand_context.words_to_avoid,
                "visual_style": state.brand_context.visual_style,
                "colors": state.brand_context.colors,
                "usp": state.brand_context.usp,
                "marketing_claims": state.brand_context.marketing_claims,
                "competitors": state.brand_context.competitors,
                "guidelines": state.brand_context.guidelines,
            }

        metadata = dict(state.metadata)
        metadata["brand_knowledge"] = brand_info

        await complete_agent_run(state, run["id"], {"brand_knowledge": brand_info})

        return {
            "metadata": metadata,
            "agent_runs": state.agent_runs,
            "current_agent": state.current_agent,
        }

    except Exception as e:
        await complete_agent_run(state, run["id"], {}, error=str(e))
        state.errors.append(f"Brand Knowledge error: {str(e)}")
        return {
            "errors": state.errors,
            "agent_runs": state.agent_runs,
        }


async def _run_search(queries: list[str], max_results_per_query: int = 4):
    from app.core.cache import cached

    provider = get_search_provider()
    results = []
    if not provider:
        return results
    for q in queries:
        found = await cached(
            namespace="search",
            key=f"{q}|{max_results_per_query}",
            ttl_seconds=3600,
            factory=lambda query=q: provider.search(query, max_results=max_results_per_query),
        )
        results.extend(found)
    return results


async def research_agent_node(state: MarketingState) -> dict:
    run = await create_agent_run(
        state,
        AgentType.RESEARCH,
        {"goal": state.request.goal, "platforms": state.request.platforms},
    )

    try:
        sources = await _run_search(
            [
                f"{state.request.goal} market trends 2026",
                f"social media trends {', '.join(state.request.platforms)} 2026"
                if state.request.platforms
                else "Instagram marketing trends 2026",
            ]
        )

        source_items = [
            ResearchSourceItem(
                title=s.title,
                url=s.url,
                source=s.source,
                summary=s.snippet[:500],
            )
            for s in sources
        ]

        research_data = ResearchData(sources=source_items)

        if sources:
            llm = get_llm_provider()
            messages = [
                LLMMessage(
                    role="system",
                    content=(
                        "You are the Market Research Agent for Qicdock. Summarize external "
                        "research into trends, consumer insights, industry news and search "
                        "trends. Base statements strictly on the provided sources. Each bullet "
                        "should be a short single sentence."
                    ),
                ),
                LLMMessage(
                    role="user",
                    content=(
                        f"Marketing goal: {state.request.goal}\n\n"
                        "Sources:\n"
                        + "\n".join(f"- {s.title}: {s.snippet[:300]}" for s in sources)
                        + "\n\nReturn JSON with keys: trends[], consumer_insights[], "
                        "industry_news[], search_trends[]."
                    ),
                ),
            ]
            summarized = await llm.generate_structured(messages, ResearchData, temperature=0.3)
            research_data.trends = summarized.trends
            research_data.consumer_insights = summarized.consumer_insights
            research_data.industry_news = summarized.industry_news
            research_data.search_trends = summarized.search_trends
        else:
            state.errors.append("Research Agent: no external sources available (search disabled or returned nothing)")

        state.research = research_data

        await complete_agent_run(
            state, run["id"], {"research": research_data.model_dump(mode="json")}
        )

        return {
            "research": research_data,
            "errors": state.errors,
            "agent_runs": state.agent_runs,
            "current_agent": state.current_agent,
        }

    except Exception as e:
        await complete_agent_run(state, run["id"], {}, error=str(e))
        state.errors.append(f"Research Agent error: {str(e)}")
        empty_research = ResearchData()
        state.research = empty_research
        return {
            "research": empty_research,
            "errors": state.errors,
            "agent_runs": state.agent_runs,
        }


async def audience_agent_node(state: MarketingState) -> dict:
    run = await create_agent_run(
        state,
        AgentType.AUDIENCE,
        {"product_ids": [str(pid) for pid in state.product_ids]},
    )

    audience = None
    usage = {}
    try:
        product_desc = (
            state.product_context[0].name
            + (f": {state.product_context[0].description}" if state.product_context else "")
        ) if state.product_context else "No product context"

        research_context = ""
        if state.research:
            research_context = (
                f"Research trends: {state.research.trends}\n"
                f"Consumer insights: {state.research.consumer_insights}"
            )

        llm = get_llm_provider()
        messages = [
            LLMMessage(
                role="system",
                content=(
                    "You are the Audience Insights Agent for Qicdock. Build a precise picture "
                    "of the target audience from brand context, product information and "
                    "external research. Do not invent statistics.\n\n"
                    f"Brand context:\n{_brand_summary(state)}"
                ),
            ),
            LLMMessage(
                role="user",
                content=(
                    f"Product: {product_desc}\n"
                    f"Marketing goal: {state.request.goal}\n"
                    f"{research_context}\n\n"
                    "Define: audience description, pain points, motivations, objections, "
                    "buying triggers, demographics, psychographics."
                ),
            ),
        ]

        audience = await llm.generate_structured(messages, AudienceInsights, temperature=0.5)
        usage = llm_usage_kwargs(audience)
    except Exception as e:
        logger.warning("Audience Agent LLM failed: %s", e)
        state.errors.append(f"Audience Agent error: {str(e)}")
        fallback_brand_audience = (
            state.brand_context.target_audience
            if state.brand_context and state.brand_context.target_audience
            else "Audience unavailable - brand profile missing target_audience"
        )
        audience = AudienceInsights(audience=fallback_brand_audience)

    state.audience_insights = audience

    await complete_agent_run(
        state, run["id"], {"audience": audience.model_dump()}, **usage
    )

    return {
        "audience_insights": audience,
        "errors": state.errors,
        "agent_runs": state.agent_runs,
        "current_agent": state.current_agent,
    }


async def competitor_trend_agent_node(state: MarketingState) -> dict:
    known_competitors = []
    if state.brand_context and state.brand_context.competitors:
        known_competitors = [
            c.get("name") if isinstance(c, dict) else str(c)
            for c in state.brand_context.competitors
        ]

    run = await create_agent_run(
        state,
        AgentType.COMPETITOR_TREND,
        {"platforms": state.request.platforms, "known_competitors": known_competitors},
    )

    insights = None
    usage = {}
    try:
        competitor_names = ", ".join(known_competitors) if known_competitors else "main competitors"

        sources = await _run_search(
            [
                f"{competitor_names} Instagram marketing strategy",
                "wireless charger car dock competitors social media content",
            ],
            max_results_per_query=4,
        )

        sources_text = "\n".join(f"- {s.title}: {s.snippet[:250]} ({s.url})" for s in sources)

        llm = get_llm_provider()
        messages = [
            LLMMessage(
                role="system",
                content=(
                    "You are the Competitor & Trend Analysis Agent for Qicdock. Analyze "
                    "competitor positioning and social media trends. Distinguish clearly "
                    "between what comes from the provided sources versus your inference.\n\n"
                    f"Known competitors from brand knowledge base: {known_competitors}\n"
                    f"Brand positioning: {state.brand_context.positioning if state.brand_context else 'N/A'}"
                ),
            ),
            LLMMessage(
                role="user",
                content=(
                    f"Platforms of interest: {state.request.platforms}\n"
                    f"Our product: {state.product_context[0].name if state.product_context else 'N/A'}\n\n"
                    f"External sources:\n{sources_text or '(no external sources available)'}\n\n"
                    "Return JSON: competitors[{name, focus}], common_angles[], "
                    "overused_angles[], content_gaps[], opportunities[], trending_formats[], "
                    "potential_hooks[]."
                ),
            ),
        ]

        insights = await llm.generate_structured(messages, CompetitorInsights, temperature=0.4)
        usage = llm_usage_kwargs(insights)
    except Exception as e:
        logger.warning("Competitor/Trend Agent failed: %s", e)
        state.errors.append(f"Competitor/Trend Agent error: {str(e)}")
        insights = CompetitorInsights()

    state.competitor_insights = insights
    state.trend_insights = insights

    await complete_agent_run(
        state, run["id"], {"insights": insights.model_dump()}, **usage
    )

    return {
        "competitor_insights": insights,
        "trend_insights": insights,
        "errors": state.errors,
        "agent_runs": state.agent_runs,
        "current_agent": state.current_agent,
    }
