from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID, uuid4
from datetime import datetime

from app.db.session.database import get_async_session
from app.db.models.organization import Organization
from app.db.models.product import Product
from app.db.models.marketing import MarketingGoal, MarketingGoalStatus
from app.db.models.agents import AgentRun, AgentRunStatus, AgentType
from app.graph.marketing_graph import marketing_graph
from app.agents.state.marketing_state import MarketingState, MarketingRequest
from app.schemas.request.marketing import MarketingGenerateRequest, MarketingStrategyRequest
from app.schemas.response.marketing import MarketingGenerateResponse, RunStatusResponse, ErrorResponse


router = APIRouter()


async def validate_organization(session: AsyncSession, org_id: UUID) -> Organization:
    result = await session.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    if not org.is_active:
        raise HTTPException(status_code=400, detail="Organization is not active")
    return org


async def validate_products(session: AsyncSession, org_id: UUID, product_ids: list[UUID]) -> list[Product]:
    result = await session.execute(
        select(Product).where(Product.id.in_(product_ids), Product.organization_id == org_id)
    )
    products = result.scalars().all()
    if len(products) != len(product_ids):
        raise HTTPException(status_code=404, detail="One or more products not found")
    return list(products)


@router.post("/marketing/generate", response_model=MarketingGenerateResponse)
async def generate_marketing_campaign(
    request: MarketingGenerateRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session),
):
    await validate_organization(session, request.organization_id)
    await validate_products(session, request.organization_id, request.product_ids)

    marketing_goal = None
    if request.marketing_goal_id:
        result = await session.execute(
            select(MarketingGoal).where(MarketingGoal.id == request.marketing_goal_id)
        )
        marketing_goal = result.scalar_one_or_none()
        if not marketing_goal:
            raise HTTPException(status_code=404, detail="Marketing goal not found")

    run_id = uuid4()
    agent_run = AgentRun(
        id=run_id,
        organization_id=request.organization_id,
        marketing_goal_id=request.marketing_goal_id,
        agent_type=AgentType.MARKETING_MANAGER,
        status=AgentRunStatus.RUNNING,
        input_data=request.model_dump(),
        started_at=datetime.utcnow(),
    )
    session.add(agent_run)
    await session.commit()

    if not marketing_goal:
        marketing_goal = MarketingGoal(
            organization_id=request.organization_id,
            title=f"Marketing Campaign - {datetime.utcnow().strftime('%Y-%m-%d')}",
            description=request.goal,
            objective=request.goal,
            target_platforms=request.platforms,
            content_types=[ct.value for ct in request.content_types],
            target_quantity=request.quantity,
            status=MarketingGoalStatus.ACTIVE,
        )
        session.add(marketing_goal)
        await session.commit()
        await session.refresh(marketing_goal)

    marketing_request = MarketingRequest(
        organization_id=request.organization_id,
        user_id=request.user_id,
        product_ids=request.product_ids,
        marketing_goal_id=marketing_goal.id,
        goal=request.goal,
        platforms=request.platforms,
        content_types=request.content_types,
        quantity=request.quantity,
        email=request.email,
        date_range=request.date_range,
        meta=request.meta,
    )

    initial_state = MarketingState(
        request=marketing_request,
        organization_id=request.organization_id,
        user_id=request.user_id,
        product_ids=request.product_ids,
        marketing_goal_id=marketing_goal.id,
    )

    background_tasks.add_task(run_marketing_workflow, run_id, initial_state)

    return MarketingGenerateResponse(
        run_id=run_id,
        status=AgentRunStatus.RUNNING,
        message="Marketing campaign generation started",
    )


async def run_marketing_workflow(run_id: UUID, initial_state: MarketingState):
    from app.db.session.database import async_session_maker
    from app.db.models.agents import AgentRun, AgentRunStatus
    from sqlalchemy import select

    try:
        final_state = await marketing_graph.ainvoke(initial_state)

        def _get(key, default=None):
            if isinstance(final_state, dict):
                return final_state.get(key, default)
            return getattr(final_state, key, default)

        errors = _get("errors", [])
        generated_content = _get("generated_content")
        generated_images = _get("generated_images")

        async with async_session_maker() as session:
            result = await session.execute(select(AgentRun).where(AgentRun.id == run_id))
            agent_run = result.scalar_one_or_none()
            if agent_run:
                agent_run.status = AgentRunStatus.COMPLETED if not errors else AgentRunStatus.FAILED
                agent_run.completed_at = datetime.utcnow()
                agent_run.output_data = {
                    "content_generated": len(generated_content.items) if generated_content else 0,
                    "images_generated": len(generated_images.images) if generated_images else 0,
                    "email_status": _get("email_status"),
                    "report_id": (_get("metadata") or {}).get("report_id"),
                    "errors": list(errors),
                }
                agent_run.meta = {
                    "current_agent": str(_get("current_agent").value) if _get("current_agent") else None,
                    "agent_runs_count": len(_get("agent_runs", [])),
                }
                await session.commit()

    except Exception as e:
        async with async_session_maker() as session:
            result = await session.execute(select(AgentRun).where(AgentRun.id == run_id))
            agent_run = result.scalar_one_or_none()
            if agent_run:
                agent_run.status = AgentRunStatus.FAILED
                agent_run.completed_at = datetime.utcnow()
                agent_run.error = str(e)
                await session.commit()


@router.get("/runs/{run_id}", response_model=RunStatusResponse)
async def get_run_status(
    run_id: UUID,
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(select(AgentRun).where(AgentRun.id == run_id))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    return RunStatusResponse(
        run_id=run.id,
        organization_id=run.organization_id,
        status=run.status,
        current_agent=run.meta.get("current_agent"),
        progress=run.meta.get("progress", {}),
        started_at=run.started_at,
        completed_at=run.completed_at,
        errors=[run.error] if run.error else [],
    )


@router.post("/marketing/strategy")
async def generate_strategy_only(
    request: MarketingStrategyRequest,
    session: AsyncSession = Depends(get_async_session),
):
    await validate_organization(session, request.organization_id)
    await validate_products(session, request.organization_id, request.product_ids)

    marketing_request = MarketingRequest(
        organization_id=request.organization_id,
        product_ids=request.product_ids,
        goal=request.goal,
        platforms=request.platforms,
        content_types=request.content_types,
        quantity=request.quantity,
    )

    initial_state = MarketingState(
        request=marketing_request,
        organization_id=request.organization_id,
        product_ids=request.product_ids,
    )

    # Strategy-only pipeline: context -> research -> audience -> competitors -> strategy
    from app.agents.nodes.load_context import load_organization_context_node
    from app.agents.nodes.load_product import load_product_context_node
    from app.agents.nodes.research_agents import (
        product_analyst_agent_node,
        brand_knowledge_agent_node,
        research_agent_node,
        audience_agent_node,
        competitor_trend_agent_node,
    )
    from app.agents.nodes.content_strategy import content_strategy_agent_node

    state = initial_state
    for node in (
        load_organization_context_node,
        load_product_context_node,
        brand_knowledge_agent_node,
        product_analyst_agent_node,
        research_agent_node,
        audience_agent_node,
        competitor_trend_agent_node,
        content_strategy_agent_node,
    ):
        updates = await node(state)
        if isinstance(updates, dict):
            for key, value in updates.items():
                setattr(state, key, value)

    strategy = state.content_strategy
    return {
        "status": "completed",
        "goal": request.goal,
        "strategy": strategy.model_dump(mode="json") if strategy else None,
        "errors": list(state.errors),
    }