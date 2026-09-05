from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os

from app.core.config import settings
from app.core.database import init_db
from app.api.routes import router as api_router
from app.queue.local_queue import get_queue
from app.knowledge.knowledge_base import get_knowledge_base

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Qicdock Marketing Calendar System...")
    
    # Ensure data directories exist
    os.makedirs("data", exist_ok=True)
    os.makedirs(settings.chroma_persist_directory, exist_ok=True)
    
    # Initialize database
    init_db()
    logger.info("Database initialized")
    
    # Initialize knowledge base (ingest if empty)
    kb = get_knowledge_base()
    if kb.count_documents() == 0:
        logger.info("Knowledge base empty, ingesting brand data...")
        try:
            # Use absolute paths based on project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            brand_story_path = os.path.join(project_root, "docs", "brand_story.md")
            products_path = os.path.join(project_root, "docs", "qicdock_products.json")
            result = kb.ingest_all(brand_story_path, products_path)
            logger.info(f"Knowledge base ingested: {result}")
        except Exception as e:
            logger.warning(f"Could not ingest knowledge base: {e}")
    
    # Initialize orchestrator to register job handlers
    from app.services.orchestrator import get_orchestrator
    get_orchestrator()
    
    # Start queue worker
    queue = get_queue()
    queue.start()
    logger.info("Queue worker started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    queue.stop()


app = FastAPI(
    title="Qicdock Agentic Marketing Calendar",
    description="Calendar-first AI marketing planning system",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/")
def root():
    return {
        "name": "Qicdock Agentic Marketing Calendar",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }