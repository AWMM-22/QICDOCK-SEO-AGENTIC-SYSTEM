import time
import logging
import threading
from typing import Optional, List, Callable, Any
from datetime import datetime
from contextlib import contextmanager

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.core.database import get_db_session
from app.models import GenerationJob, JobStatus, JobType, CalendarEntry, EntryStatus, MarketingPlan, PlanStatus

logger = logging.getLogger(__name__)


class LocalQueue:
    def __init__(self, poll_interval: int = 2):
        self.poll_interval = poll_interval
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None
        self._handlers: dict[JobType, Callable] = {}
        self._shutdown_event = threading.Event()

    def register_handler(self, job_type: JobType, handler: Callable[[GenerationJob, Session], Any]):
        self._handlers[job_type] = handler
        logger.info(f"Registered handler for {job_type.value}")

    def enqueue(
        self,
        plan_id: int,
        job_type: JobType,
        payload: dict,
        calendar_entry_id: Optional[int] = None,
        priority: int = 0
    ) -> GenerationJob:
        with get_db_session() as db:
            job = GenerationJob(
                plan_id=plan_id,
                calendar_entry_id=calendar_entry_id,
                job_type=job_type,
                status=JobStatus.QUEUED,
                payload=payload,
                attempts=0
            )
            db.add(job)
            db.flush()
            job_id = job.id
            db.commit()
    def log_queue_status(self, db: Session, plan_id: Optional[int] = None):
        """Log queue state metrics."""
        query = db.query(GenerationJob)
        if plan_id:
            query = query.filter(GenerationJob.plan_id == plan_id)
        jobs = query.all()
        
        pending = sum(1 for j in jobs if j.status in [JobStatus.QUEUED, JobStatus.RETRYING])
        running = sum(1 for j in jobs if j.status == JobStatus.RUNNING)
        completed = sum(1 for j in jobs if j.status == JobStatus.COMPLETED)
        failed = sum(1 for j in jobs if j.status == JobStatus.FAILED)
        
        plan_str = f" for Plan #{plan_id}" if plan_id else ""
        logger.info(f"[QUEUE STATUS{plan_str}] Pending: {pending} | Running: {running} | Completed: {completed} | Failed: {failed}")

    def enqueue(
        self,
        plan_id: int,
        job_type: JobType,
        payload: dict,
        calendar_entry_id: Optional[int] = None,
        priority: int = 0
    ) -> GenerationJob:
        with get_db_session() as db:
            job = GenerationJob(
                plan_id=plan_id,
                calendar_entry_id=calendar_entry_id,
                job_type=job_type,
                status=JobStatus.QUEUED,
                payload=payload,
                attempts=0
            )
            db.add(job)
            db.flush()
            job_id = job.id
            db.commit()
            logger.info(f"[JOB ENQUEUED] Job #{job_id} ({job_type.value}) enqueued for Plan #{plan_id} (Entry #{calendar_entry_id})")
            self.log_queue_status(db, plan_id)
            return job

    def get_next_job(self, db: Session) -> Optional[GenerationJob]:
        job = db.query(GenerationJob).filter(
            GenerationJob.status.in_([JobStatus.QUEUED, JobStatus.RETRYING])
        ).order_by(GenerationJob.created_at).first()
        return job

    def process_job(self, job: GenerationJob, db: Session) -> bool:
        handler = self._handlers.get(job.job_type)
        if not handler:
            logger.error(f"[JOB FAILED] No handler for job type {job.job_type.value}")
            job.status = JobStatus.FAILED
            job.error = f"No handler for job type {job.job_type.value}"
            db.commit()
            return False

        job.status = JobStatus.RUNNING
        job.attempts += 1
        db.commit()
        logger.info(f"[JOB RUNNING] Executing Job #{job.id} ({job.job_type.value}) for Plan #{job.plan_id} (Attempt #{job.attempts})")
        self.log_queue_status(db, job.plan_id)

        try:
            result = handler(job, db)
            job.status = JobStatus.COMPLETED
            job.result = result
            db.commit()
            logger.info(f"[JOB COMPLETED] Job #{job.id} ({job.job_type.value}) completed successfully.")
            self.log_queue_status(db, job.plan_id)
            return True
        except Exception as e:
            logger.error(f"[FAILED ENTRY / JOB] Job #{job.id} ({job.job_type.value}) failed: {e}", exc_info=True)
            job.status = JobStatus.FAILED
            job.error = str(e)
            
            # If job is associated with a specific calendar entry, mark entry as FAILED as well
            if job.calendar_entry_id:
                entry = db.query(CalendarEntry).filter(CalendarEntry.id == job.calendar_entry_id).first()
                if entry:
                    entry.status = EntryStatus.FAILED
                    entry.error = str(e)
                    logger.warning(f"[FAILED ENTRY] Entry #{entry.id} ({entry.date} {entry.platform}) marked FAILED due to job error: {e}")
            
            db.commit()
            self.log_queue_status(db, job.plan_id)
            return False

    def retry_job(self, job: GenerationJob, db: Session):
        job.status = JobStatus.RETRYING
        job.error = None
        db.commit()
        logger.info(f"Job {job.id} queued for retry (attempt {job.attempts + 1})")

    def start(self):
        if self._running:
            return
        self._running = True
        self._shutdown_event.clear()
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()
        logger.info("[QUEUE WORKER] Local queue worker started (Concurrency = 1)")

    def stop(self):
        self._running = False
        self._shutdown_event.set()
        if self._worker_thread:
            self._worker_thread.join(timeout=10)
        logger.info("[QUEUE WORKER] Local queue worker stopped")

    def _worker_loop(self):
        while self._running and not self._shutdown_event.is_set():
            try:
                with get_db_session() as db:
                    job = self.get_next_job(db)
                    if job:
                        self.process_job(job, db)
                    else:
                        time.sleep(self.poll_interval)
            except Exception as e:
                logger.error(f"[QUEUE WORKER ERROR] {e}", exc_info=True)
                time.sleep(self.poll_interval)

    def get_job_status(self, job_id: int) -> Optional[dict]:
        with get_db_session() as db:
            job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
            if not job:
                return None
            return {
                "id": job.id,
                "job_type": job.job_type.value,
                "status": job.status.value,
                "attempts": job.attempts,
                "error": job.error,
                "result": job.result
            }

    def get_plan_jobs(self, plan_id: int) -> List[dict]:
        with get_db_session() as db:
            jobs = db.query(GenerationJob).filter(GenerationJob.plan_id == plan_id).all()
            return [
                {
                    "id": j.id,
                    "job_type": j.job_type.value,
                    "status": j.status.value,
                    "calendar_entry_id": j.calendar_entry_id,
                    "attempts": j.attempts,
                    "error": j.error,
                    "created_at": j.created_at.isoformat() if j.created_at else None
                }
                for j in jobs
            ]


_queue_instance: Optional[LocalQueue] = None


def get_queue() -> LocalQueue:
    global _queue_instance
    if _queue_instance is None:
        from app.core.config import settings
        _queue_instance = LocalQueue(poll_interval=settings.queue_poll_interval)
    return _queue_instance