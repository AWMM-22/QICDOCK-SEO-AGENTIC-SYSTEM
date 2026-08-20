from typing import Callable, Awaitable
from app.agents.state.marketing_state import MarketingState
from app.db.models.agents import AgentType


class NodeResult:
    def __init__(
        self,
        state: MarketingState,
        next_node: Optional[str] = None,
        error: Optional[str] = None,
    ):
        self.state = state
        self.next_node = next_node
        self.error = error


NodeFn = Callable[[MarketingState], Awaitable[NodeResult]]


async def create_agent_run(
    state: MarketingState,
    agent_type: AgentType,
    input_data: dict,
) -> dict:
    from uuid import uuid4
    from datetime import datetime

    run_data = {
        "id": str(uuid4()),
        "organization_id": str(state.organization_id),
        "marketing_goal_id": str(state.marketing_goal_id) if state.marketing_goal_id else None,
        "agent_type": agent_type.value,
        "status": "running",
        "input_data": input_data,
        "output_data": {},
        "started_at": datetime.utcnow().isoformat(),
        "tokens_input": 0,
        "tokens_output": 0,
        "estimated_cost": 0.0,
    }
    state.agent_runs.append(run_data)
    return run_data


async def complete_agent_run(
    state: MarketingState,
    run_id: str,
    output_data: dict,
    tokens_input: int = 0,
    tokens_output: int = 0,
    estimated_cost: float = 0.0,
    error: Optional[str] = None,
) -> None:
    from datetime import datetime

    for run in state.agent_runs:
        if run["id"] == run_id:
            run["status"] = "failed" if error else "completed"
            run["output_data"] = output_data
            run["completed_at"] = datetime.utcnow().isoformat()
            run["tokens_input"] = tokens_input
            run["tokens_output"] = tokens_output
            run["estimated_cost"] = estimated_cost
            run["error"] = error
            break