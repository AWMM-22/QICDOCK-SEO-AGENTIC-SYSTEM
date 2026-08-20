from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.db.session.database import get_async_session
from app.db.models.agents import MarketingReport, ReportStatus
from app.schemas.response.marketing import ReportResponse, ErrorResponse


router = APIRouter()


@router.get("/reports/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: UUID,
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(select(MarketingReport).where(MarketingReport.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return ReportResponse(
        id=report.id,
        marketing_goal_id=report.marketing_goal_id,
        title=report.title,
        status=report.status.value,
        html_content=report.html_content,
        email_status=report.email_status,
        email_sent_at=report.email_sent_at,
        created_at=report.created_at,
    )


@router.post("/reports/{report_id}/email")
async def email_report(
    report_id: UUID,
    recipient_email: str,
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(select(MarketingReport).where(MarketingReport.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return {
        "message": "Email sending endpoint - to be implemented",
        "report_id": report_id,
        "recipient": recipient_email,
    }