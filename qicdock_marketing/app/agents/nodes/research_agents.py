from app.agents.state.marketing_state import MarketingState
from app.agents.nodes.base import NodeResult, create_agent_run, complete_agent_run
from app.db.models.agents import AgentType


async def product_analyst_agent_node(state: MarketingState) -> NodeResult:
    run = await create_agent_run(
        state,
        AgentType.PRODUCT_ANALYST,
        {"product_ids": [str(pid) for pid in state.product_ids]},
    )

    try:
        analysis = {
            "main_usp": "",
            "secondary_usps": [],
            "pain_point_solved": "",
            "ideal_use_case": "",
            "target_audience": "",
            "emotional_benefit": "",
            "functional_benefit": "",
            "differentiators": [],
        }

        if state.product_context:
            product = state.product_context[0]
            analysis = {
                "main_usp": product.usp[0] if product.usp else "",
                "secondary_usps": product.usp[1:] if len(product.usp) > 1 else [],
                "pain_point_solved": product.pain_points_solved[0] if product.pain_points_solved else "",
                "ideal_use_case": product.use_cases[0] if product.use_cases else "",
                "target_audience": product.target_audience or "",
                "emotional_benefit": product.emotional_benefits[0] if product.emotional_benefits else "",
                "functional_benefit": product.functional_benefits[0] if product.functional_benefits else "",
                "differentiators": product.differentiators,
            }

        state.metadata["product_analysis"] = analysis

        await complete_agent_run(
            state,
            run["id"],
            {"analysis": analysis},
        )

        return NodeResult(state=state, next_node="execute_research_agent")

    except Exception as e:
        await complete_agent_run(state, run["id"], {}, error=str(e))
        state.errors.append(f"Product Analyst error: {str(e)}")
        return NodeResult(state=state, next_node="execute_research_agent")


async def brand_knowledge_agent_node(state: MarketingState) -> NodeResult:
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
            }

        state.metadata["brand_knowledge"] = brand_info

        await complete_agent_run(
            state,
            run["id"],
            {"brand_knowledge": brand_info},
        )

        return NodeResult(state=state, next_node="execute_research_agent")

    except Exception as e:
        await complete_agent_run(state, run["id"], {}, error=str(e))
        state.errors.append(f"Brand Knowledge error: {str(e)}")
        return NodeResult(state=state, next_node="execute_research_agent")


async def research_agent_node(state: MarketingState) -> NodeResult:
    run = await create_agent_run(
        state,
        AgentType.RESEARCH,
        {"goal": state.request.goal, "platforms": state.request.platforms},
    )

    try:
        from app.agents.state.marketing_state import ResearchData, ResearchSourceItem

        research_data = ResearchData(
            sources=[],
            trends=["Wireless charging adoption growing", "Minimalist desk setups trending"],
            consumer_insights=["Users value convenience", "Cable clutter is a major pain point"],
            industry_news=[],
            search_trends=["wireless charger", "magSafe", "desk setup"],
        )

        state.research = research_data

        await complete_agent_run(
            state,
            run["id"],
            {"research": research_data.model_dump()},
        )

        return NodeResult(state=state, next_node="execute_research_agent")

    except Exception as e:
        await complete_agent_run(state, run["id"], {}, error=str(e))
        state.errors.append(f"Research Agent error: {str(e)}")
        return NodeResult(state=state, next_node="execute_research_agent")


async def audience_agent_node(state: MarketingState) -> NodeResult:
    run = await create_agent_run(
        state,
        AgentType.AUDIENCE,
        {"product_ids": [str(pid) for pid in state.product_ids]},
    )

    try:
        from app.agents.state.marketing_state import AudienceInsights

        audience = AudienceInsights(
            audience="Young professionals and tech enthusiasts",
            pain_points=["Cable clutter", "Slow charging", "Inconvenient placement"],
            motivations=["Convenience", "Clean aesthetic", "Fast charging"],
            objections=["Price", "Compatibility concerns", "Charging speed"],
            buying_triggers=["New phone purchase", "Desk upgrade", "Gift occasions"],
            demographics={"age_range": "25-45", "income": "middle-high"},
            psychographics={"values": ["minimalism", "efficiency", "quality"]},
        )

        state.audience_insights = audience

        await complete_agent_run(
            state,
            run["id"],
            {"audience": audience.model_dump()},
        )

        return NodeResult(state=state, next_node="execute_research_agent")

    except Exception as e:
        await complete_agent_run(state, run["id"], {}, error=str(e))
        state.errors.append(f"Audience Agent error: {str(e)}")
        return NodeResult(state=state, next_node="execute_research_agent")


async def competitor_trend_agent_node(state: MarketingState) -> NodeResult:
    run = await create_agent_run(
        state,
        AgentType.COMPETITOR_TREND,
        {"category": "wireless charging", "platforms": state.request.platforms},
    )

    try:
        from app.agents.state.marketing_state import CompetitorInsights

        insights = CompetitorInsights(
            competitors=[
                {"name": "Belkin", "focus": "premium pricing"},
                {"name": "Anker", "focus": "value/performance"},
                {"name": "Apple", "focus": "ecosystem integration"},
            ],
            common_angles=["Fast charging speeds", "Multiple device charging", "Travel friendly"],
            overused_angles=["Fast charging", "Qi certified"],
            content_gaps=["Car-specific integration", "Custom fit solutions", "Cable-free lifestyle"],
            opportunities=["Car console integration focus", "Modular system approach", "Design-forward positioning"],
            trending_formats=["Problem/solution reels", "Desk setup videos", "Before/after car organization"],
            potential_hooks=["Your console doesn't need cables", "Made for your exact car", "One dock, every drive"],
        )

        state.competitor_insights = insights
        state.trend_insights = insights

        await complete_agent_run(
            state,
            run["id"],
            {"insights": insights.model_dump()},
        )

        return NodeResult(state=state, next_node="execute_research_agent")

    except Exception as e:
        await complete_agent_run(state, run["id"], {}, error=str(e))
        state.errors.append(f"Competitor/Trend Agent error: {str(e)}")
        return NodeResult(state=state, next_node="execute_research_agent")