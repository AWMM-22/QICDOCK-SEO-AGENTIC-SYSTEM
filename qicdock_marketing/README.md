# Qicdock AI Marketing Team

An end-to-end LangGraph multi-agent marketing system for Qicdock. This system autonomously researches, strategizes, creates content, generates images, reviews, and delivers complete marketing campaigns via email.

## Features

- **Multi-Agent Architecture**: Specialized agents for research, strategy, content creation, visual generation, and review
- **LangGraph Orchestration**: Stateful, traceable workflow with conditional routing and revision loops
- **Provider Abstractions**: Configurable LLM, embedding, search, image, and email providers
- **PostgreSQL + pgvector**: Persistent storage with semantic knowledge retrieval
- **FastAPI Backend**: RESTful API with async support and background job processing
- **Docker Ready**: Complete containerization with PostgreSQL and Redis

## Architecture

```
FastAPI → LangGraph → Marketing Manager → Specialized Agents
                                    ├── Product Analyst
                                    ├── Brand Knowledge
                                    ├── Research Agent
                                    ├── Audience Agent
                                    ├── Competitor/Trend Agent
                                    ├── Content Strategy
                                    ├── Instagram Agent
                                    ├── Reels Agent
                                    ├── Stories Agent
                                    ├── Visual/Image Agent
                                    ├── Brand Reviewer
                                    ├── Report Generator
                                    └── Email Agent
```

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 16+ with pgvector extension
- Redis 7+ (optional)
- Gemini API key (or other LLM provider)

### Installation

1. Clone and navigate to the project:
```bash
cd qicdock_marketing
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

5. Start services with Docker Compose:
```bash
docker-compose up -d postgres redis
```

6. Run database migrations:
```bash
alembic upgrade head
```

7. Start the application:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000` with docs at `http://localhost:8000/docs`.

## API Endpoints

### Marketing Generation
```bash
POST /api/v1/marketing/generate
{
  "organization_id": "uuid",
  "product_ids": ["uuid"],
  "goal": "Increase Instagram awareness for wireless charger",
  "platforms": ["instagram"],
  "content_types": ["post", "carousel", "reel", "story"],
  "quantity": 5,
  "email": "founder@qicdock.com"
}
```

Response:
```json
{
  "run_id": "uuid",
  "status": "running",
  "message": "Marketing campaign generation started"
}
```

### Check Run Status
```bash
GET /api/v1/runs/{run_id}
```

### Create Product
```bash
POST /api/v1/products
{
  "organization_id": "uuid",
  "name": "Qicdock Wireless Charger",
  "slug": "wireless-charger",
  "description": "Custom-fit magnetic dock for car console",
  "features": ["Magnetic alignment", "Fast charging", "Cable-free"],
  "benefits": ["Clean console", "Hands-free charging", "Perfect fit"],
  "price": 79.99,
  "usp": ["Car-specific fit", "Modular stands", "Premium materials"]
}
```

### Ingest Knowledge
```bash
POST /api/v1/knowledge/ingest
{
  "organization_id": "uuid",
  "title": "Brand Guidelines",
  "content": "Qicdock brand voice is professional yet approachable...",
  "source_type": "brand_guide"
}
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://postgres:postgres@localhost:5432/qicdock_marketing` |
| `LLM_PROVIDER` | LLM provider (gemini/openai/anthropic/local) | `gemini` |
| `LLM_MODEL` | Model name | `gemini-1.5-pro` |
| `LLM_API_KEY` | API key for LLM provider | Required |
| `EMBEDDING_PROVIDER` | Embedding provider | `gemini` |
| `EMBEDDING_MODEL` | Embedding model | `text-embedding-004` |
| `SEARCH_PROVIDER` | Search provider | `tavily` |
| `IMAGE_PROVIDER` | Image generation provider | `gemini` |
| `EMAIL_PROVIDER` | Email provider | `resend` |
| `EMAIL_FROM` | From email address | `marketing@qicdock.com` |
| `EMAIL_TO` | Default recipient | `founder@qicdock.com` |

## Development

### Running Tests
```bash
pytest tests/ -v
```

### Code Quality
```bash
# Linting
ruff check .

# Type checking
mypy app/
```

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

## Project Structure

```
qicdock_marketing/
├── app/
│   ├── api/v1/           # API routes and endpoints
│   ├── agents/           # LangGraph agents and nodes
│   │   ├── nodes/        # Individual agent implementations
│   │   └── state/        # Typed state definitions
│   ├── core/
│   │   ├── config/       # Settings and configuration
│   │   └── providers/    # Provider abstractions (LLM, embedding, etc.)
│   ├── db/
│   │   ├── models/       # SQLAlchemy models
│   │   └── session/      # Database session management
│   ├── graph/            # LangGraph workflow definition
│   ├── schemas/          # Pydantic request/response models
│   └── main.py           # FastAPI application entry point
├── tests/                # Unit and integration tests
├── alembic/              # Database migrations
├── requirements.txt      # Python dependencies
├── Dockerfile            # Container definition
├── docker-compose.yml    # Local development stack
└── .env.example          # Environment template
```

## PHASE 1 Status (Current)

✅ **Completed:**
- Project structure and configuration
- FastAPI application with lifespan management
- PostgreSQL async connection with SQLAlchemy 2.0
- Core models: Organization, User, BrandProfile, Product, ProductImage
- Marketing models: MarketingGoal, ContentItem, GeneratedAsset, KnowledgeDocument
- Agent models: AgentRun, AgentMessage, ReviewResult, MarketingReport
- LLM Provider abstraction with Gemini implementation
- Embedding Provider abstraction with Gemini implementation
- LangGraph State with typed Pydantic models
- Marketing Manager node (orchestrator)
- Context loading nodes (organization, product)
- Research agents (Product Analyst, Brand Knowledge, Research, Audience, Competitor/Trend)
- Content Strategy agent
- Content agents (Instagram, Reels, Stories)
- Visual Strategy and Image Generation agents (placeholder)
- Brand Reviewer with revision loop (max 2)
- Report Generator
- Email Agent
- API endpoints for marketing generation, products, knowledge, content, reports
- Docker configuration with PostgreSQL and Redis
- Health check endpoint

## Next Steps (PHASE 2+)

- [ ] Implement actual research providers (Tavily, Serper)
- [ ] Implement RAG with pgvector for brand knowledge retrieval
- [ ] Implement real image generation with product reference images
- [ ] Add Server-Sent Events for live run streaming
- [ ] Build Next.js frontend (dashboard, campaign creation, content library)
- [ ] Add authentication and authorization
- [ ] Implement cost tracking and observability
- [ ] Add comprehensive test suite
- [ ] Production hardening (rate limiting, monitoring, logging)

## License

Proprietary - Qicdock Internal Use Only