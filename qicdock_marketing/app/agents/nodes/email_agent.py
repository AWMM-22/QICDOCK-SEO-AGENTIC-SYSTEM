import logging
from datetime import datetime, timezone

from app.agents.state.marketing_state import MarketingState
from app.agents.nodes.base import create_agent_run, complete_agent_run
from app.core.config.settings import settings
from app.core.providers.email.factory import get_email_provider
from app.db.models.agents import AgentType

logger = logging.getLogger(__name__)


def _build_email_html(state: MarketingState) -> tuple[str, list]:
    """Build a structured email: per-post cards with INLINE images + full report.

    Returns (html, attachments) where attachments include inline CID images.
    """
    import html as html_escape
    from pathlib import Path
    from app.core.providers.email.base import EmailAttachment

    items = state.generated_content.items if state.generated_content else []
    briefs = {
        str(i.content_item_id): i
        for i in (state.generated_images.images if state.generated_images else [])
    }

    attachments: list = []
    cards: list[str] = []

    for idx, item in enumerate(items, start=1):
        brief = briefs.get(str(item.content_id))
        prompt_text = (brief.prompt if brief else "") or item.image_prompt or ""
        ref_paths = (brief.url.split("|") if brief and brief.url else [])

        # Reference product photos inline so the user knows WHICH photos to use
        ref_tags = []
        for ridx, rp in enumerate(ref_paths[:3], start=1):
            path = Path(rp)
            if not path.exists():
                continue
            cid = f"ref{idx}_{ridx}"
            mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
            attachments.append(EmailAttachment(
                filename=path.name,
                content=path.read_bytes(),
                mime_type=mime,
                content_id=cid,
                inline=True,
            ))
            ref_tags.append(
                f"<img src='cid:{cid}' alt='{html_escape.escape(path.stem)}' "
                f"style='width:130px;border-radius:8px;margin:4px;border:1px solid #ddd;'>"
            )
        ref_block = (
            "<div style='margin:10px 0 4px;'><b style='font-size:13px;'>Reference photos "
            "(attach these in your image tool):</b><div>"
            + "".join(ref_tags) + "</div></div>"
            if ref_tags else ""
        )

        prompt_block = (
            "<div style='margin:10px 0;'>"
            "<b style='font-size:13px;'>Image prompt (copy-paste):</b>"
            f"<div style='background:#f6f8fa;border:1px solid #ddd;border-radius:8px;"
            f"padding:10px 12px;font-family:Consolas,monospace;font-size:12px;"
            f"white-space:pre-wrap;color:#24292f;margin-top:4px;'>{html_escape.escape(prompt_text)}</div>"
            f"<div style='font-size:11px;color:#666;margin-top:3px;'>"
            f"Aspect ratio: {brief.aspect_ratio if brief else '4:5'} "
            f"&#8226; use the reference photos above for product fidelity</div>"
            "</div>"
            if prompt_text else ""
        )

        caption = html_escape.escape(item.content.get("caption", "") or "").replace("\n", "<br>")
        hook = html_escape.escape(item.content.get("hook", "") or "")
        cta = html_escape.escape(item.cta or "")
        hashtags = " ".join(f"#{h.lstrip('#')}" for h in item.hashtags)
        score = f"{item.review_score}/10" if item.review_score else "pending"
        status_color = "#0a7d33" if item.status.value == "approved" else "#b58a00"

        script_block = ""
        scenes = item.content.get("scenes") or []
        if scenes:
            rows = "".join(
                f"<li style='margin:4px 0;'><b>{html_escape.escape(str(s.get('duration', '?')))}s</b> - "
                f"{html_escape.escape(s.get('visual', ''))} <i>({html_escape.escape(s.get('voiceover', ''))})</i></li>"
                for s in scenes if isinstance(s, dict)
            )
            script_block = f"<p style='margin:8px 0 2px;'><b>Script:</b></p><ul style='margin:4px 0;padding-left:20px;'>{rows}</ul>"
        frames = item.content.get("frames") or []
        if frames:
            rows = "".join(
                f"<li style='margin:4px 0;'>{html_escape.escape(f.get('text', ''))}"
                + (f" <span style='color:#555'>[{html_escape.escape(f.get('interactive_element'))}]</span>" if f.get("interactive_element") else "")
                + "</li>"
                for f in frames if isinstance(f, dict)
            )
            script_block = f"<p style='margin:8px 0 2px;'><b>Story frames:</b></p><ul style='margin:4px 0;padding-left:20px;'>{rows}</ul>"

        cards.append(f"""
        <tr><td style="padding:12px 0;">
          <table width="100%" style="border:1px solid #e2e2e2;border-radius:14px;border-collapse:separate;border-spacing:0;overflow:hidden;">
            <tr><td style="background:#111318;color:#fff;padding:10px 16px;font-family:Arial,sans-serif;">
              <span style="font-size:15px;font-weight:bold;">{idx}. {html_escape.escape(item.title or hook)}</span>
              <span style="float:right;font-size:12px;background:#2c3140;padding:3px 10px;border-radius:20px;">
                {item.platform} / {item.content_type.value}</span>
            </td></tr>
            <tr><td style="padding:16px;background:#ffffff;font-family:Arial,sans-serif;">
              <p style="margin:0 0 4px;font-size:16px;"><b>Hook:</b> {hook}</p>
              <p style="margin:4px 0;font-size:14px;color:#333;">{caption}</p>
              {script_block}
              <p style="margin:10px 0 2px;"><b>CTA:</b> <span style="background:#eef4ff;color:#1a56db;padding:3px 10px;border-radius:6px;">{cta}</span></p>
              <p style="margin:6px 0 0;color:#1a56db;font-size:13px;">{hashtags}</p>
              {ref_block}
              {prompt_block}
              <p style="margin:8px 0 0;font-size:12px;color:{status_color};">Brand review: {score} &#10003;</p>
            </td></tr>
          </table>
        </td></tr>""")

    human_note = ""
    if state.metadata.get("human_review_required"):
        human_note = (
            "<tr><td style='background:#fff3cd;border:1px solid #ffeeba;padding:12px 16px;"
            "border-radius:10px;font-family:Arial;color:#856404;'>"
            "<b>Human review required:</b> some content failed brand review after all retries.</td></tr>"
        )

    report_block = f"""
    <tr><td style="padding:18px 0;font-family:Arial,sans-serif;">
      <details {"open" if not items else ""}>
        <summary style="cursor:pointer;font-size:16px;font-weight:bold;">Full Marketing Report</summary>
        <div style="margin-top:10px;">{state.final_report or ""}</div>
      </details>
    </td></tr>"""

    html = f"""
    <html><body style="margin:0;background:#f4f5f7;">
    <div style="max-width:640px;margin:auto;padding:16px;">
      <table width="100%" style="border-collapse:collapse;">
        <tr><td style="padding:6px 0 14px;font-family:Arial,sans-serif;">
          <h1 style="margin:0;font-size:22px;">Qicdock Marketing Report</h1>
          <p style="margin:4px 0 0;color:#666;font-size:13px;">
            {html_escape.escape(state.request.goal)} &#8226; {len(items)} content items
          </p>
        </td></tr>
        {"".join(cards)}
        {human_note}
        {report_block}
        <tr><td style="padding:14px 0;color:#999;font-size:11px;font-family:Arial;">
          Generated by Qicdock AI Marketing Team - images are attached and embedded above.
        </td></tr>
      </table>
    </div>
    </body></html>
    """
    return html, attachments


async def email_agent_node(state: MarketingState) -> dict:
    recipient = state.request.email or settings.EMAIL_TO

    run = await create_agent_run(
        state,
        AgentType.EMAIL,
        {"recipient": recipient},
    )

    subject = f"Qicdock AI Marketing Report - {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
    html_body, attachments = _build_email_html(state)

    provider = get_email_provider()

    # Attach generated visual assets (local files only) per plan section 16
    # Videos (if any) attached as regular files - inline images already added
    if state.metadata.get("generated_videos"):
        from pathlib import Path
        from app.core.providers.email.base import EmailAttachment

        for vid in state.metadata.get("generated_videos", []):
            path = Path(vid.get("path", ""))
            if vid.get("path") and path.exists():
                attachments.append(
                    EmailAttachment(
                        filename=path.name,
                        content=path.read_bytes(),
                        mime_type="video/mp4",
                    )
                )

    if not recipient:
        state.email_status = "skipped_no_recipient"
        send_result_status = "skipped"
        error = "No recipient configured"
    elif provider is None:
        state.email_status = "skipped_unconfigured"
        send_result_status = "skipped"
        error = f"Email provider '{settings.EMAIL_PROVIDER}' not configured"
    else:
        result = await provider.send(
            to=recipient, subject=subject, html=html_body, attachments=attachments or None
        )
        if result.status == "sent":
            state.email_status = "sent"
            error = None
        else:
            state.email_status = "failed"
            error = result.error
        send_result_status = result.status

    metadata = dict(state.metadata)
    metadata["email"] = {
        "to": recipient,
        "subject": subject,
        "status": send_result_status,
        "attachments": len(attachments),
        "error": error,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    await complete_agent_run(
        state,
        run["id"],
        {"email_status": state.email_status, "recipient": recipient},
        error=error,
    )

    # Update persisted report with email status
    report_id = state.metadata.get("report_id")
    if report_id:
        try:
            from uuid import UUID
            from sqlalchemy import select
            from app.db.session.database import async_session_maker
            from app.db.models.agents import MarketingReport

            async with async_session_maker() as session:
                result = await session.execute(
                    select(MarketingReport).where(MarketingReport.id == UUID(report_id))
                )
                db_report = result.scalar_one_or_none()
                if db_report:
                    db_report.email_status = state.email_status
                    if state.email_status == "sent":
                        db_report.email_sent_at = datetime.now(timezone.utc)
                        db_report.email_recipient = recipient
                        from app.db.models.agents import ReportStatus
                        db_report.status = ReportStatus.EMAILED
                    await session.commit()
        except Exception as e:
            logger.warning("Failed to update report email status: %s", e)

    return {
        "email_status": state.email_status,
        "metadata": metadata,
        "errors": state.errors,
        "agent_runs": state.agent_runs,
        "current_agent": state.current_agent,
    }
