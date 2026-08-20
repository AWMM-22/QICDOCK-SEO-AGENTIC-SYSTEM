from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.db.models.agents import AgentRunStatus


class MarketingGenerateResponse(BaseModel):
    run_id: UUID
    status: AgentRunStatus
    message: str


class RunStatusResponse(BaseModel):
    run_id: UUID
    organization_id: UUID
    status: AgentRunStatus
    current_agent: Optional[str] = None
    progress: dict = {}
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    errors: list[str] = []


class ContentItemResponse(BaseModel):
    id: UUID
    content_type: str
    platform: str
    title: Optional[str] = None
    content: dict
    status: str
    review_score: Optional[float] = None
    created_at: datetime


class ReportResponse(BaseModel):
    id: UUID
    marketing_goal_id: UUID
    title: str
    status: str
    html_content: str
    email_status: str
    email_sent_at: Optional[datetime] = None
    created_at: datetime


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None