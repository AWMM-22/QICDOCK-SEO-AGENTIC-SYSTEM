import logging
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional

from app.agents.state.marketing_state import MarketingState
from app.db.models.agents import AgentType

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def create_agent_run(
    state: MarketingState,
    agent_type: AgentType,
    input_data: dict,
    parent_run_id: Optional[str] = None,
) -> dict:
    run_id = uuid4()
    run_data = {
        "id": str(run_id),
        "organization_id": str(state.organization_id),
        "marketing_goal_id": str(state.marketing_goal_id) if state.marketing_goal_id else None,
        "agent_type": agent_type.value,
        "status": "running",
        "input_data": input_data,
        "output_data": {},
        "started_at": _utcnow().isoformat(),
        "completed_at": None,
        "tokens_input": 0,
        "tokens_output": 0,
        "estimated_cost": 0.0,
        "model_used": None,
        "provider_used": None,
        "error": None,
    }
    state.agent_runs.append(run_data)
    state.current_agent = agent_type

    try:
        from app.db.session.database import async_session_maker
        from app.db.models.agents import AgentRun, AgentRunStatus

        async with async_session_maker() as session:
            session.add(
                AgentRun(
                    id=run_id,
                    organization_id=state.organization_id,
                    marketing_goal_id=state.marketing_goal_id,
                    parent_run_id=UUID(parent_run_id) if parent_run_id else None,
                    agent_type=agent_type,
                    status=AgentRunStatus.RUNNING,
                    input_data=input_data,
                    output_data={},
                    started_at=_utcnow(),
                )
            )
            await session.commit()
    except Exception as e:
        logger.warning("Failed to persist agent run start: %s", e)

    return run_data


async def complete_agent_run(
    state: MarketingState,
    run_id: str,
    output_data: dict,
    tokens_input: int = 0,
    tokens_output: int = 0,
    estimated_cost: float = 0.0,
    model_used: Optional[str] = None,
    provider_used: Optional[str] = None,
    error: Optional[str] = None,
) -> None:
    completed_at = _utcnow()

    for run in state.agent_runs:
        if run["id"] == run_id:
            run["status"] = "failed" if error else "completed"
            run["output_data"] = output_data
            run["completed_at"] = completed_at.isoformat()
            run["tokens_input"] = tokens_input
            run["tokens_output"] = tokens_output
            run["estimated_cost"] = estimated_cost
            run["model_used"] = model_used or run.get("model_used")
            run["provider_used"] = provider_used or run.get("provider_used")
            run["error"] = error
            break

    try:
        from app.db.session.database import async_session_maker
        from app.db.models.agents import AgentRun, AgentRunStatus
        from sqlalchemy import select

        async with async_session_maker() as session:
            result = await session.execute(select(AgentRun).where(AgentRun.id == UUID(run_id)))
            db_run = result.scalar_one_or_none()
            if db_run:
                db_run.status = AgentRunStatus.FAILED if error else AgentRunStatus.COMPLETED
                db_run.output_data = output_data
                db_run.completed_at = completed_at
                started = db_run.started_at or completed_at
                db_run.duration_ms = int((completed_at - started).total_seconds() * 1000)
                db_run.tokens_input = tokens_input
                db_run.tokens_output = tokens_output
                db_run.estimated_cost = estimated_cost
                if model_used:
                    db_run.model_used = model_used
                if provider_used:
                    db_run.provider_used = provider_used
                db_run.error = error
                await session.commit()
    except Exception as e:
        logger.warning("Failed to persist agent run completion: %s", e)


def llm_usage_kwargs(response) -> dict:
    usage = getattr(response, "usage", None)
    if usage is None:
        return {}
    return {
        "tokens_input": getattr(usage, "input_tokens", 0),
        "tokens_output": getattr(usage, "output_tokens", 0),
        "estimated_cost": getattr(usage, "estimated_cost", 0.0),
        "model_used": getattr(response, "model", None),
        "provider_used": getattr(response, "provider", None),
    }
