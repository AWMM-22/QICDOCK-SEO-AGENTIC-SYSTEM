from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.core.database import get_db
from app.schemas import (
    CreatePlanRequest, CreatePlanResponse, PlanResponse, CalendarResponse,
    CalendarEntryResponse, DayRecommendationResponse, RegenerateRequest,
    RegenerateResponse, ImageGenerateRequest, ImageGenerateResponse,
    BrandKnowledgeUpdateRequest, BrandKnowledgeUpdateResponse,
    ErrorResponse, HealthResponse
)
from app.models import Project, MarketingPlan, CalendarEntry, PlanStatus, EntryStatus, ImageStatus, ReviewStatus, JobType
from app.services.orchestrator import get_orchestrator
from app.knowledge.knowledge_base import get_knowledge_base

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check():
    from app.services.llm_provider import get_llm_provider
    from app.services.image_provider import get_image_provider
    
    llm = get_llm_provider()
    img_provider = get_image_provider()
    
    has_llm = (hasattr(llm, 'providers') and any(p.get('active') for p in llm.providers)) or bool(getattr(llm, 'api_key', None))
    return HealthResponse(
        status="healthy",
        database="connected",
        chromadb="connected",
        llm_configured=has_llm,
        image_provider_configured=bool(hasattr(img_provider, 'api_key') and img_provider.api_key)
    )


@router.post("/projects", response_model=dict)
def create_project(name: str = "Qicdock Marketing", db: Session = Depends(get_db)):
    project = Project(name=name)
    db.add(project)
    db.commit()
    db.refresh(project)
    return {"project_id": project.id, "name": project.name}


@router.get("/projects", response_model=List[dict])
def list_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).all()
    return [{"id": p.id, "name": p.name, "created_at": p.created_at.isoformat()} for p in projects]


@router.post("/projects/{project_id}/plans", response_model=CreatePlanResponse)
def create_plan(
    project_id: int,
    request: CreatePlanRequest,
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Validate dates
    if request.start_date > request.end_date:
        raise HTTPException(status_code=400, detail="Start date must be before or equal to end date")

    orchestrator = get_orchestrator()
    plan = orchestrator.create_plan(
        project_id=project_id,
        start_date=request.start_date,
        end_date=request.end_date,
        platforms=[p.value for p in request.platforms],
        objective=request.objective,
        additional_instructions=request.additional_instructions
    )

    return CreatePlanResponse(plan_id=plan.id, status=plan.status)


@router.get("/plans", response_model=List[PlanResponse])
def list_plans(db: Session = Depends(get_db)):
    plans = db.query(MarketingPlan).order_by(MarketingPlan.id.desc()).all()
    return [
        PlanResponse(
            plan_id=p.id,
            project_id=p.project_id,
            start_date=p.start_date,
            end_date=p.end_date,
            objective=p.objective,
            status=p.status,
            strategy_summary=p.strategy_summary,
            created_at=p.created_at,
            updated_at=p.updated_at
        )
        for p in plans
    ]


@router.get("/latest-plan", response_model=PlanResponse)
def get_latest_plan(db: Session = Depends(get_db)):
    plan = db.query(MarketingPlan).order_by(MarketingPlan.id.desc()).first()
    if not plan:
        raise HTTPException(status_code=404, detail="No plans found")
    return PlanResponse(
        plan_id=plan.id,
        project_id=plan.project_id,
        start_date=plan.start_date,
        end_date=plan.end_date,
        objective=plan.objective,
        status=plan.status,
        strategy_summary=plan.strategy_summary,
        created_at=plan.created_at,
        updated_at=plan.updated_at
    )



@router.get("/plans/{plan_id}", response_model=PlanResponse)
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(MarketingPlan).filter(MarketingPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    return PlanResponse(
        plan_id=plan.id,
        project_id=plan.project_id,
        start_date=plan.start_date,
        end_date=plan.end_date,
        objective=plan.objective,
        status=plan.status,
        strategy_summary=plan.strategy_summary,
        created_at=plan.created_at,
        updated_at=plan.updated_at
    )


@router.get("/plans/{plan_id}/calendar", response_model=CalendarResponse)
def get_calendar(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(MarketingPlan).filter(MarketingPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    entries = db.query(CalendarEntry).filter(
        CalendarEntry.plan_id == plan_id
    ).order_by(CalendarEntry.date, CalendarEntry.platform).all()

    entry_responses = [
        CalendarEntryResponse(
            id=e.id,
            plan_id=e.plan_id,
            date=e.date,
            platform=e.platform,
            content_type=e.content_type,
            status=e.status,
            title=e.title,
            objective=e.objective,
            content_pillar=e.content_pillar,
            product=e.product,
            audience=e.audience,
            hook=e.hook,
            concept=e.concept,
            caption_direction=e.caption_direction,
            cta=e.cta,
            visual_direction=e.visual_direction,
            image_prompt=e.image_prompt,
            reason=e.reason,
            sequence_position=e.sequence_position,
            campaign_thread=e.campaign_thread,
            follows_entry=e.follows_entry,
            supports_entry=e.supports_entry,
            review_status=e.review_status,
            review_score=e.review_score,
            review_issues=e.review_issues,
            review_corrections=e.review_corrections,
            review_attempts=e.review_attempts,
            error=e.error,
            image_status=e.image_status,
            image_url=e.image_url,
            image_prompt_used=e.image_prompt_used,
            image_prompts=e.image_prompts,
            image_urls=e.image_urls,
            image_prompts_used=e.image_prompts_used,
            created_at=e.created_at,
            updated_at=e.updated_at
        )
        for e in entries
    ]

    total_days = (plan.end_date - plan.start_date).days + 1
    planned_posts = len([e for e in entries if e.status != EntryStatus.SKIPPED])
    empty_days = total_days - planned_posts

    return CalendarResponse(
        plan_id=plan.id,
        start_date=plan.start_date,
        end_date=plan.end_date,
        strategy_summary=plan.strategy_summary,
        recommended_frequency={},
        entries=entry_responses,
        total_days=total_days,
        planned_posts=planned_posts,
        empty_days=empty_days
    )


@router.get("/plans/{plan_id}/entries/{entry_date}", response_model=DayRecommendationResponse)
def get_day_recommendation(
    plan_id: int,
    entry_date: date,
    platform: Optional[str] = None,
    db: Session = Depends(get_db)
):
    plan = db.query(MarketingPlan).filter(MarketingPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    query = db.query(CalendarEntry).filter(
        CalendarEntry.plan_id == plan_id,
        CalendarEntry.date == entry_date
    )
    if platform:
        query = query.filter(CalendarEntry.platform == platform)
    
    entry = query.first()
    
    if not entry:
        # Empty day
        return DayRecommendationResponse(
            date=entry_date,
            platform=platform or "instagram",
            is_empty=True,
            empty_reason="No post recommended for this day. The marketing strategist determined this day should remain empty to maintain optimal content cadence and avoid audience fatigue.",
            status=EntryStatus.SKIPPED,
            image_status=ImageStatus.NOT_REQUESTED,
            review_status=ReviewStatus.PENDING
        )

    return DayRecommendationResponse(
        id=entry.id,
        date=entry.date,
        platform=entry.platform,
        content_type=entry.content_type,
        title=entry.title,
        objective=entry.objective,
        audience=entry.audience,
        product=entry.product,
        content_pillar=entry.content_pillar,
        reason=entry.reason,
        hook=entry.hook,
        concept=entry.concept,
        caption_direction=entry.caption_direction,
        cta=entry.cta,
        visual_direction=entry.visual_direction,
        image_prompt=entry.image_prompt,
        review_status=entry.review_status,
        review_score=entry.review_score,
        review_issues=entry.review_issues,
        review_corrections=entry.review_corrections,
        image_status=entry.image_status,
        image_url=entry.image_url,
        image_prompt_used=entry.image_prompt_used,
        image_prompts=entry.image_prompts,
        image_urls=entry.image_urls,
        image_prompts_used=entry.image_prompts_used,
        status=entry.status,
        error=entry.error,
        is_empty=False
    )


@router.post("/plans/{plan_id}/entries/{entry_date}/regenerate", response_model=RegenerateResponse)
def regenerate_recommendation(
    plan_id: int,
    entry_date: date,
    request: RegenerateRequest,
    platform: str = "instagram",
    db: Session = Depends(get_db)
):
    plan = db.query(MarketingPlan).filter(MarketingPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    entry = db.query(CalendarEntry).filter(
        CalendarEntry.plan_id == plan_id,
        CalendarEntry.date == entry_date,
        CalendarEntry.platform == platform
    ).first()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Calendar entry not found")

    orchestrator = get_orchestrator()
    orchestrator.queue.enqueue(
        plan_id=plan_id,
        job_type=JobType.REGENERATE_ENTRY,
        payload={"entry_id": entry.id, "feedback": request.feedback},
        calendar_entry_id=entry.id
    )

    return RegenerateResponse(date=entry_date.isoformat(), status=EntryStatus.REGENERATING)


@router.post("/plans/{plan_id}/entries/{entry_date}/image", response_model=ImageGenerateResponse)
def generate_image(
    plan_id: int,
    entry_date: date,
    request: ImageGenerateRequest,
    platform: str = "instagram",
    db: Session = Depends(get_db)
):
    plan = db.query(MarketingPlan).filter(MarketingPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    entry = db.query(CalendarEntry).filter(
        CalendarEntry.plan_id == plan_id,
        CalendarEntry.date == entry_date,
        CalendarEntry.platform == platform
    ).first()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Calendar entry not found")

    orchestrator = get_orchestrator()
    orchestrator.queue.enqueue(
        plan_id=plan_id,
        job_type=JobType.IMAGE_GENERATION,
        payload={
            "entry_id": entry.id,
            "prompt": request.prompt,
            "aspect_ratio": request.aspect_ratio,
            "model": request.model,
            "quality": request.quality,
            "n": request.n
        },
        calendar_entry_id=entry.id
    )

    return ImageGenerateResponse(
        image_status=ImageStatus.QUEUED,
        image_prompt_used=request.prompt or entry.image_prompt
    )


@router.get("/calendar", response_model=CalendarResponse)
def get_unified_calendar(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    query = db.query(CalendarEntry)
    if start_date:
        query = query.filter(CalendarEntry.date >= start_date)
    if end_date:
        query = query.filter(CalendarEntry.date <= end_date)
        
    entries = query.order_by(CalendarEntry.date, CalendarEntry.platform).all()

    entry_responses = [
        CalendarEntryResponse(
            id=e.id,
            plan_id=e.plan_id,
            date=e.date,
            platform=e.platform,
            content_type=e.content_type,
            status=e.status,
            title=e.title,
            objective=e.objective,
            content_pillar=e.content_pillar,
            product=e.product,
            audience=e.audience,
            hook=e.hook,
            concept=e.concept,
            caption_direction=e.caption_direction,
            cta=e.cta,
            visual_direction=e.visual_direction,
            image_prompt=e.image_prompt,
            reason=e.reason,
            sequence_position=e.sequence_position,
            campaign_thread=e.campaign_thread,
            follows_entry=e.follows_entry,
            supports_entry=e.supports_entry,
            review_status=e.review_status,
            review_score=e.review_score,
            review_issues=e.review_issues,
            review_corrections=e.review_corrections,
            review_attempts=e.review_attempts,
            error=e.error,
            image_status=e.image_status,
            image_url=e.image_url,
            image_prompt_used=e.image_prompt_used,
            image_prompts=e.image_prompts,
            image_urls=e.image_urls,
            image_prompts_used=e.image_prompts_used,
            created_at=e.created_at,
            updated_at=e.updated_at
        )
        for e in entries
    ]

    min_date = min([e.date for e in entries]) if entries else date.today()
    max_date = max([e.date for e in entries]) if entries else date.today()
    total_days = (max_date - min_date).days + 1 if entries else 0
    planned_posts = len([e for e in entries if e.status != EntryStatus.SKIPPED])
    empty_days = max(0, total_days - planned_posts)

    latest_plan = db.query(MarketingPlan).order_by(MarketingPlan.id.desc()).first()

    return CalendarResponse(
        plan_id=latest_plan.id if latest_plan else 0,
        start_date=min_date,
        end_date=max_date,
        strategy_summary=latest_plan.strategy_summary if latest_plan else "Unified Marketing Calendar across all plans",
        recommended_frequency={},
        entries=entry_responses,
        total_days=total_days,
        planned_posts=planned_posts,
        empty_days=empty_days
    )


@router.get("/entries/{entry_date}", response_model=List[DayRecommendationResponse])
def get_entries_by_date(
    entry_date: date,
    platform: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(CalendarEntry).filter(CalendarEntry.date == entry_date)
    if platform:
        query = query.filter(CalendarEntry.platform == platform)
    
    entries = query.all()
    if not entries:
        return [
            DayRecommendationResponse(
                date=entry_date,
                platform=platform or "instagram",
                is_empty=True,
                empty_reason="No post recommended for this day. The marketing strategist determined this day should remain empty to maintain optimal content cadence and avoid audience fatigue.",
                status=EntryStatus.SKIPPED,
                image_status=ImageStatus.NOT_REQUESTED,
                review_status=ReviewStatus.PENDING
            )
        ]
    
    return [
        DayRecommendationResponse(
            id=e.id,
            date=e.date,
            platform=e.platform,
            content_type=e.content_type,
            title=e.title,
            objective=e.objective,
            audience=e.audience,
            product=e.product,
            content_pillar=e.content_pillar,
            reason=e.reason,
            hook=e.hook,
            concept=e.concept,
            caption_direction=e.caption_direction,
            cta=e.cta,
            visual_direction=e.visual_direction,
            image_prompt=e.image_prompt,
            review_status=e.review_status,
            review_score=e.review_score,
            review_issues=e.review_issues,
            review_corrections=e.review_corrections,
            image_status=e.image_status,
            image_url=e.image_url,
            image_prompt_used=e.image_prompt_used,
            image_prompts=e.image_prompts,
            image_urls=e.image_urls,
            image_prompts_used=e.image_prompts_used,
            status=e.status,
            error=e.error,
            is_empty=False
        )
        for e in entries
    ]


@router.post("/entries/by-id/{entry_id}/regenerate", response_model=RegenerateResponse)
def regenerate_entry_by_id(
    entry_id: int,
    request: RegenerateRequest,
    db: Session = Depends(get_db)
):
    entry = db.query(CalendarEntry).filter(CalendarEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Calendar entry not found")

    orchestrator = get_orchestrator()
    orchestrator.queue.enqueue(
        plan_id=entry.plan_id,
        job_type=JobType.REGENERATE_ENTRY,
        payload={"entry_id": entry.id, "feedback": request.feedback},
        calendar_entry_id=entry.id
    )

    return RegenerateResponse(date=entry.date.isoformat(), status=EntryStatus.REGENERATING)


@router.post("/entries/by-id/{entry_id}/image", response_model=ImageGenerateResponse)
def generate_image_by_id(
    entry_id: int,
    request: ImageGenerateRequest,
    db: Session = Depends(get_db)
):
    entry = db.query(CalendarEntry).filter(CalendarEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Calendar entry not found")

    orchestrator = get_orchestrator()
    orchestrator.queue.enqueue(
        plan_id=entry.plan_id,
        job_type=JobType.IMAGE_GENERATION,
        payload={
            "entry_id": entry.id,
            "prompt": request.prompt,
            "aspect_ratio": request.aspect_ratio,
            "model": request.model,
            "quality": request.quality,
            "n": request.n
        },
        calendar_entry_id=entry.id
    )

    return ImageGenerateResponse(
        image_status=ImageStatus.QUEUED,
        image_prompt_used=request.prompt or entry.image_prompt
    )


@router.post("/entries/by-id/{entry_id}/regenerate-image-prompt")
def regenerate_image_prompt(
    entry_id: int,
    db: Session = Depends(get_db)
):
    entry = db.query(CalendarEntry).filter(CalendarEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Calendar entry not found")

    from app.agents.visual_prompt import get_visual_prompt_agent
    visual_agent = get_visual_prompt_agent()
    
    recommendation = {
        "hook": entry.hook,
        "concept": entry.concept,
        "caption_direction": entry.caption_direction,
        "cta": entry.cta,
        "visual_direction": entry.visual_direction,
        "image_prompt": entry.image_prompt
    }

    entry_plan = {
        "date": entry.date.isoformat(),
        "platform": entry.platform,
        "content_type": entry.content_type,
        "product": entry.product,
        "objective": entry.objective,
        "content_pillar": entry.content_pillar
    }

    try:
        visual_result = visual_agent.generate_visual_prompt(recommendation, entry_plan)
        entry.image_prompt = visual_result.image_prompt
        entry.image_prompts = visual_result.image_prompts
        entry.image_status = ImageStatus.NOT_REQUESTED
        db.commit()
        return {"entry_id": entry.id, "image_prompt": entry.image_prompt, "image_prompts": entry.image_prompts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/knowledge/update", response_model=BrandKnowledgeUpdateResponse)
def update_knowledge_base(request: BrandKnowledgeUpdateRequest):
    kb = get_knowledge_base()
    
    # Use absolute paths based on project root
    import os
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    brand_story_path = os.path.join(project_root, "docs", "brand_story.md")
    products_path = os.path.join(project_root, "docs", "qicdock_products.json")
    
    try:
        result = kb.ingest_all(brand_story_path, products_path)
        return BrandKnowledgeUpdateResponse(
            success=True,
            message=f"Knowledge base updated: {result['brand_story_chunks']} brand chunks, {result['products']} products",
            version=1
        )
    except Exception as e:
        return BrandKnowledgeUpdateResponse(
            success=False,
            message=f"Failed to update knowledge base: {str(e)}"
        )


@router.get("/knowledge/status")
def knowledge_status():
    kb = get_knowledge_base()
    count = kb.count_documents()
    products = kb.get_all_products_summary()
    return {
        "total_documents": count,
        "products": products
    }


@router.get("/plans/{plan_id}/jobs")
def get_plan_jobs(plan_id: int):
    orchestrator = get_orchestrator()
    jobs = orchestrator.queue.get_plan_jobs(plan_id)
    return {"jobs": jobs}