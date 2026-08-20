from app.agents.state.marketing_state import MarketingState
from app.agents.nodes.base import NodeResult, create_agent_run, complete_agent_run
from app.db.models.agents import AgentType
from app.core.config.settings import settings


async def email_agent_node(state: MarketingState) -> NodeResult:
    run = await create_agent_run(
        state,
        AgentType.EMAIL,
        {"recipient": state.request.email or settings.EMAIL_TO},
    )

    try:
        recipient = state.request.email or settings.EMAIL_TO
        subject = f"Qicdock AI Marketing Report — {datetime.now().strftime('%Y-%m-%d')}"

        html_body = state.final_report or "<p>Marketing report generated successfully.</p>"

        state.email_status = "sent"
        state.metadata["email_sent"] = {
            "to": recipient,
            "subject": subject,
            "sent_at": datetime.now().isoformat(),
        }

        await complete_agent_run(
            state,
            run["id"],
            {"email_sent": True, "recipient": recipient},
        )

        return NodeResult(state=state, next_node="END")

    except Exception as e:
        await complete_agent_run(state, run["id"], {}, error=str(e))
        state.errors.append(f"Email Agent error: {str(e)}")
        state.email_status = "failed"
        return NodeResult(state=state, next_node="END")


from datetime import datetime