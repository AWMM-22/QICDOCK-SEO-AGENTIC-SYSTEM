import logging
from typing import List, Dict, Any, Optional
from datetime import date, datetime
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.models import (
    Project, MarketingPlan, CalendarEntry, GenerationJob,
    PlanStatus, EntryStatus, JobType, JobStatus, ReviewStatus, ImageStatus
)
from app.agents.calendar_planner import get_calendar_planner, CalendarPlanOutput
from app.agents.content_recommendation import get_content_recommendation_agent
from app.agents.brand_reviewer import get_brand_reviewer
from app.agents.visual_prompt import get_visual_prompt_agent
from app.agents.market_research import get_market_research_agent
from app.queue.local_queue import get_queue
from app.knowledge.knowledge_base import get_knowledge_base
from app.core.config import settings

logger = logging.getLogger(__name__)


class CalendarOrchestrator:
    def __init__(self):
        self.planner = get_calendar_planner()
        self.content_agent = get_content_recommendation_agent()
        self.reviewer = get_brand_reviewer()
        self.visual_agent = get_visual_prompt_agent()
        self.research_agent = get_market_research_agent()
        self.queue = get_queue()
        self.knowledge_base = get_knowledge_base()
        
        self._register_handlers()

    def _register_handlers(self):
        self.queue.register_handler(JobType.CALENDAR_PLAN, self._handle_calendar_plan)
        self.queue.register_handler(JobType.CONTENT_RECOMMENDATION, self._handle_content_recommendation)
        self.queue.register_handler(JobType.REVIEW, self._handle_review)
        self.queue.register_handler(JobType.IMAGE_GENERATION, self._handle_image_generation)
        self.queue.register_handler(JobType.REGENERATE_ENTRY, self._handle_regenerate_entry)

    def create_plan(
        self,
        project_id: int,
        start_date: date,
        end_date: date,
        platforms: List[str],
        objective: Optional[str],
        additional_instructions: Optional[str]
    ) -> MarketingPlan:
        with get_db_session() as db:
            plan = MarketingPlan(
                project_id=project_id,
                start_date=start_date,
                end_date=end_date,
                objective=objective,
                status=PlanStatus.GENERATING
            )
            db.add(plan)
            db.flush()
            plan_id = plan.id
            plan_status = plan.status
            db.expunge(plan)
            db.commit()
            
            # Enqueue calendar planning job
            self.queue.enqueue(
                plan_id=plan_id,
                job_type=JobType.CALENDAR_PLAN,
                payload={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "platforms": platforms,
                    "objective": objective,
                    "additional_instructions": additional_instructions
                }
            )
            
            logger.info(f"Created plan {plan_id} and enqueued calendar planning job")
            return plan

    def _handle_calendar_plan(self, job: GenerationJob, db: Session) -> Dict[str, Any]:
        payload = job.payload
        start_date = date.fromisoformat(payload["start_date"])
        end_date = date.fromisoformat(payload["end_date"])
        platforms = payload["platforms"]
        objective = payload.get("objective")
        additional_instructions = payload.get("additional_instructions")
        plan_id = job.plan_id

        # Get existing entries if any (for regeneration context)
        existing_entries = db.query(CalendarEntry).filter(
            CalendarEntry.plan_id == plan_id
        ).all()
        existing_list = [
            {
                "date": e.date.isoformat(),
                "platform": e.platform,
                "content_type": e.content_type,
                "title": e.title,
                "reason": e.reason
            }
            for e in existing_entries
        ]

        # Conduct market research (safely wrapped so network/Tavily failure doesn't block calendar planning)
        festivals = self.planner._get_relevant_festivals(start_date, end_date)
        try:
            brand_context = "\n".join([
                item['content'][:200] for item in 
                self.knowledge_base.query_brand_context("Qicdock brand", n_results=2)
            ])
            market_research = self.research_agent.research(
                start_date, end_date, platforms, objective, festivals, brand_context
            )
        except Exception as research_err:
            logger.warning(f"Market research agent skipped or failed: {research_err}. Proceeding with core planner...")

        # Strategic planning call (1 LLM call to decide selected dates & content types for entire month)
        plan_output: CalendarPlanOutput = self.planner.plan_month(
            start_date, end_date, platforms, objective, additional_instructions, existing_list
        )

        # Persist plan metadata
        plan = db.query(MarketingPlan).filter(MarketingPlan.id == plan_id).first()
        if plan:
            plan.strategy_summary = plan_output.strategy_summary
            plan.status = PlanStatus.GENERATING

        # Persist calendar entries for selected dates ONLY
        created_entries = []
        for i, entry_plan in enumerate(plan_output.calendar_entries):
            entry = CalendarEntry(
                plan_id=plan_id,
                date=date.fromisoformat(entry_plan.date),
                platform=entry_plan.platform,
                content_type=entry_plan.content_type,
                status=EntryStatus.QUEUED,
                title=entry_plan.title,
                objective=entry_plan.objective,
                content_pillar=entry_plan.content_pillar,
                product=entry_plan.product,
                audience=entry_plan.audience,
                reason=entry_plan.reason,
                sequence_position=entry_plan.sequence_position,
                campaign_thread=entry_plan.campaign_thread,
                follows_entry=entry_plan.follows_entry,
                supports_entry=entry_plan.supports_entry
            )
            db.add(entry)
            created_entries.append(entry)

        db.commit()

        # Enqueue content recommendation jobs for selected entries
        for entry in created_entries:
            self.queue.enqueue(
                plan_id=plan_id,
                job_type=JobType.CONTENT_RECOMMENDATION,
                payload={"entry_id": entry.id},
                calendar_entry_id=entry.id
            )

        logger.info(f"[PLAN CREATED] Plan #{plan_id} created with {len(created_entries)} strategic entries queued.")
        return {"entries_created": len(created_entries), "strategy_summary": plan_output.strategy_summary}

    def _handle_content_recommendation(self, job: GenerationJob, db: Session) -> Dict[str, Any]:
        entry_id = job.payload["entry_id"]
        user_feedback = job.payload.get("user_feedback")
        entry = db.query(CalendarEntry).filter(CalendarEntry.id == entry_id).first()
        if not entry:
            raise ValueError(f"Calendar entry {entry_id} not found")

        plan = db.query(MarketingPlan).filter(MarketingPlan.id == entry.plan_id).first()
        
        # Update entry status
        entry.status = EntryStatus.GENERATING
        db.commit()

        # Build entry plan dict
        entry_plan = {
            "date": entry.date.isoformat(),
            "platform": entry.platform,
            "content_type": entry.content_type,
            "title": entry.title,
            "objective": entry.objective,
            "content_pillar": entry.content_pillar,
            "product": entry.product,
            "audience": entry.audience,
            "reason": entry.reason,
            "sequence_position": entry.sequence_position,
            "campaign_thread": entry.campaign_thread
        }

        # Get surrounding entries for context
        surrounding = db.query(CalendarEntry).filter(
            CalendarEntry.plan_id == entry.plan_id,
            CalendarEntry.id != entry_id
        ).order_by(CalendarEntry.date).all()
        surrounding_list = [
            {
                "date": e.date.isoformat(),
                "platform": e.platform,
                "content_type": e.content_type,
                "title": e.title,
                "reason": e.reason
            }
            for e in surrounding
        ]

        # Generate recommendation with compact context
        recommendation = self.content_agent.generate_recommendation(
            entry_plan, surrounding_list, user_feedback=user_feedback
        )

        # Save recommendation directly to entry (new format → existing DB columns)
        entry.hook = recommendation.hook
        entry.concept = recommendation.angle              # angle → concept column
        entry.caption_direction = recommendation.content   # content structure → caption_direction column
        entry.cta = recommendation.cta
        entry.visual_direction = recommendation.caption    # publish-ready caption → visual_direction column
        # Generate visual prompts immediately after content recommendation
        try:
            visual_result = self.visual_agent.generate_visual_prompt(recommendation.dict(), entry_plan)
            entry.image_prompt = visual_result.image_prompt
            entry.image_prompts = visual_result.image_prompts
        except Exception as e:
            logger.error(f"Failed to generate visual prompt for entry {entry_id}: {e}")
            entry.image_prompt = recommendation.creative_prompt
            entry.image_prompts = []

        # Combine hashtags, primary_kpi, and why into reason column
        reason_parts = []
        if recommendation.why:
            reason_parts.append(recommendation.why)
        if recommendation.primary_kpi:
            reason_parts.append(f"Primary KPI: {recommendation.primary_kpi}")
        if recommendation.hashtags:
            reason_parts.append(f"Hashtags: {recommendation.hashtags}")
        entry.reason = "\n".join(reason_parts)
        entry.review_status = ReviewStatus.APPROVED
        entry.review_score = 1.0
        entry.image_status = ImageStatus.NOT_REQUESTED
        entry.status = EntryStatus.READY
        entry.error = None
        
        # PERSIST IMMEDIATELY
        db.commit()
        logger.info(
            f"[SUCCESSFUL ENTRY] Entry #{entry.id} ({entry.date} {entry.platform}) "
            f"generated and saved immediately: '{entry.title}'"
        )

        # Check if all entries for this plan are completed
        all_entries = db.query(CalendarEntry).filter(CalendarEntry.plan_id == entry.plan_id).all()
        non_pending = [e for e in all_entries if e.status in [EntryStatus.READY, EntryStatus.FAILED, EntryStatus.SKIPPED]]
        if plan and len(non_pending) == len(all_entries):
            plan.status = PlanStatus.READY
            db.commit()
            logger.info(f"[PLAN COMPLETED] Plan #{plan.id} all entries processed ({len(non_pending)}/{len(all_entries)} ready/failed).")

        return {"entry_id": entry.id, "recommendation_generated": True, "status": "ready"}

    def _handle_review(self, job: GenerationJob, db: Session) -> Dict[str, Any]:
        entry_id = job.payload["entry_id"]
        entry = db.query(CalendarEntry).filter(CalendarEntry.id == entry_id).first()
        if not entry:
            raise ValueError(f"Calendar entry {entry_id} not found")

        plan = db.query(MarketingPlan).filter(MarketingPlan.id == entry.plan_id).first()
        
        # Build recommendation dict
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

        # Get surrounding entries
        surrounding = db.query(CalendarEntry).filter(
            CalendarEntry.plan_id == entry.plan_id,
            CalendarEntry.id != entry_id
        ).order_by(CalendarEntry.date).all()
        surrounding_list = [
            {
                "date": e.date.isoformat(),
                "platform": e.platform,
                "content_type": e.content_type,
                "title": e.title,
                "reason": e.reason
            }
            for e in surrounding
        ]

        # Review
        review_result = self.reviewer.review_recommendation(
            recommendation, entry_plan, surrounding_list
        )

        # Save review result
        entry.review_status = ReviewStatus(review_result.status)
        entry.review_score = review_result.score
        entry.review_issues = review_result.issues
        entry.review_corrections = review_result.corrections
        entry.review_attempts += 1

        if review_result.status == "approved":
            entry.status = EntryStatus.READY
            
            # Generate visual prompt
            visual_result = self.visual_agent.generate_visual_prompt(recommendation, entry_plan)
            entry.image_prompt = visual_result.image_prompt
            entry.image_prompts = visual_result.image_prompts
            entry.image_status = ImageStatus.NOT_REQUESTED
            
            logger.info(f"Entry {entry_id} approved and ready")
        elif review_result.status == "needs_revision" and entry.review_attempts < settings.max_review_retries:
            # Regenerate
            entry.status = EntryStatus.RETRYING
            self.queue.enqueue(
                plan_id=entry.plan_id,
                job_type=JobType.CONTENT_RECOMMENDATION,
                payload={"entry_id": entry.id},
                calendar_entry_id=entry.id
            )
            logger.info(f"Entry {entry_id} needs revision, re-queued (attempt {entry.review_attempts})")
        else:
            entry.status = EntryStatus.FAILED
            entry.error = f"Review failed after {entry.review_attempts} attempts: {review_result.issues}"
            logger.warning(f"Entry {entry_id} failed review: {review_result.issues}")

        db.commit()
        return {"entry_id": entry.id, "review_status": review_result.status, "score": review_result.score}

    def _handle_image_generation(self, job: GenerationJob, db: Session) -> Dict[str, Any]:
        from app.services.image_provider import get_image_provider
        
        entry_id = job.payload["entry_id"]
        entry = db.query(CalendarEntry).filter(CalendarEntry.id == entry_id).first()
        if not entry:
            raise ValueError(f"Calendar entry {entry_id} not found")

        prompt = job.payload.get("prompt") or entry.image_prompt
        aspect_ratio = job.payload.get("aspect_ratio", "1:1")
        model = job.payload.get("model")
        quality = job.payload.get("quality", "standard")
        n = job.payload.get("n", 1)

        prompts_to_use = entry.image_prompts if entry.image_prompts and len(entry.image_prompts) > 0 else [prompt]
        
        entry.image_status = ImageStatus.GENERATING
        entry.image_prompt_used = prompt
        entry.image_prompts_used = prompts_to_use
        db.commit()

        try:
            provider = get_image_provider()
            all_urls = []
            
            for p in prompts_to_use:
                # We always ask for 1 image per distinct prompt
                urls = provider.generate(p, aspect_ratio, model, quality, 1)
                if urls:
                    all_urls.extend(urls)
            
            if all_urls:
                entry.image_status = ImageStatus.READY
                entry.image_url = all_urls[0]
                entry.image_urls = all_urls
                logger.info(f"Generated {len(all_urls)} images for entry {entry_id}")
            else:
                entry.image_status = ImageStatus.FAILED
                entry.error = "Image generation returned no URLs"
                
        except Exception as e:
            entry.image_status = ImageStatus.FAILED
            entry.error = f"Image generation failed: {str(e)}"
            logger.error(f"Image generation failed for entry {entry_id}: {e}")

        db.commit()
        return {"entry_id": entry.id, "image_status": entry.image_status.value, "image_url": entry.image_url}

    def _handle_regenerate_entry(self, job: GenerationJob, db: Session) -> Dict[str, Any]:
        entry_id = job.payload["entry_id"]
        user_feedback = job.payload.get("feedback")
        
        entry = db.query(CalendarEntry).filter(CalendarEntry.id == entry_id).first()
        if not entry:
            raise ValueError(f"Calendar entry {entry_id} not found")

        # Save current version to history
        from app.models import RecommendationVersion
        current_version = db.query(RecommendationVersion).filter(
            RecommendationVersion.calendar_entry_id == entry_id,
            RecommendationVersion.is_current == True
        ).first()
        
        next_version = 1
        if current_version:
            current_version.is_current = False
            next_version = current_version.version + 1

        version_record = RecommendationVersion(
            calendar_entry_id=entry_id,
            version=next_version,
            title=entry.title,
            objective=entry.objective,
            content_pillar=entry.content_pillar,
            product=entry.product,
            audience=entry.audience,
            hook=entry.hook,
            concept=entry.concept,
            caption_direction=entry.caption_direction,
            cta=entry.cta,
            visual_direction=entry.visual_direction,
            image_prompt=entry.image_prompt,
            image_prompts=entry.image_prompts,
            reason=entry.reason,
            sequence_position=entry.sequence_position,
            campaign_thread=entry.campaign_thread,
            follows_entry=entry.follows_entry,
            supports_entry=entry.supports_entry,
            user_feedback=user_feedback,
            review_status=entry.review_status,
            review_score=entry.review_score,
            review_issues=entry.review_issues,
            review_corrections=entry.review_corrections,
            is_current=True
        )
        db.add(version_record)

        # Reset entry for regeneration
        entry.status = EntryStatus.REGENERATING
        entry.review_status = ReviewStatus.PENDING
        entry.review_attempts = 0
        entry.image_status = ImageStatus.NOT_REQUESTED
        entry.image_url = None
        entry.image_urls = None
        entry.image_prompt_used = None
        entry.image_prompts_used = None
        entry.error = None
        db.commit()

        # Re-run content recommendation with feedback
        self.queue.enqueue(
            plan_id=entry.plan_id,
            job_type=JobType.CONTENT_RECOMMENDATION,
            payload={"entry_id": entry.id, "user_feedback": user_feedback},
            calendar_entry_id=entry.id
        )

        logger.info(f"Regeneration started for entry {entry_id}")
        return {"entry_id": entry.id, "regeneration_started": True}


_orchestrator_instance: Optional[CalendarOrchestrator] = None


def get_orchestrator() -> CalendarOrchestrator:
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = CalendarOrchestrator()
    return _orchestrator_instance