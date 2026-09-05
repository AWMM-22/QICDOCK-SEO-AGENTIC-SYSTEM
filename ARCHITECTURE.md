# Qicdock AI Marketing Engine - System Architecture & API Key Distribution

> **Comprehensive Technical Specification**  
> Documenting system components, multi-provider LLM load balancing, autonomous AI agents, background job queueing, and API key responsibilities.

---

## 1. Executive Summary

The **Qicdock Marketing Calendar & Recommendation System** is an enterprise-grade AI engine designed to generate data-driven marketing calendars, platform-tailored content recommendations, brand consistency reviews, and visual generation prompts for Qicdock car wireless chargers across multiple channels (Instagram, LinkedIn, etc.).

To ensure high availability, zero downtime, and immunity to API rate limits (HTTP 429 / Tokens-Per-Minute bounds), the system utilizes a **Multi-Provider LLM Load Balancer & Failover Pool** that dynamically distributes LLM inference tasks across multiple API keys and provider models.

---

## 2. API Keys & Responsibility Matrix

| API Key Name | Provider / Engine | Target Model | Primary Responsibilities & Role | Failover Strategy |
| :--- | :--- | :--- | :--- | :--- |
| `GROQ_API_KEY` (Key 1) | **Groq Inc.** | `openai/gpt-oss-20b` | **Round-Robin Pool Slot 1**: Executes market research analysis, calendar planning, content recommendations, brand reviews, and visual prompts. | Fails over instantly to Groq Key 2 on 429/413 rate limit. |
| `GROQ_API_KEY_2` (Key 2) | **Groq Inc.** | `openai/gpt-oss-20b` | **Round-Robin Pool Slot 2**: Parallel load balancer slot. Handles concurrent job queue processing and distributes token throughput. | Fails over instantly to Gemini 3.6 Flash on 429/413 rate limit. |
| `GEMINI_API_KEY` | **Google AI Studio** | `gemini-3.6-flash` | **Round-Robin Pool Slot 3**: High-speed, high-capacity inference engine via OpenAI-compatible REST endpoint (`https://generativelanguage.googleapis.com/v1beta/openai/`). | Fails over to OpenAI / Groq Pool on error. |
| `OPENAI_API_KEY` | **OpenAI** | `gpt-4o-mini` | **Backup Pool Slot**: Automatic fallback provider slot. Dynamically re-enabled when billing credits are present. | Disabled gracefully on `insufficient_quota` without blocking execution. |
| `TAVILY_API_KEY` | **Tavily AI** | Web Intelligence API | **Market Research Engine**: Used by `MarketResearchAgent` to fetch real-time web search results regarding automotive trends, car accessory market insights, and Indian festival calendar events. | Uses local knowledge base fallback if search fails. |

---

## 3. System Architecture Diagram

```mermaid
flowchart TD
    subgraph ClientLayer ["Client Layer"]
        User UI["Web Frontend / API Clients"]
    end

    subgraph FastAPIServer ["FastAPI Backend (Host: 127.0.0.1:8000)"]
        Routes["API Router (/api/projects, /api/plans)"]
        Orchestrator["Orchestrator Service"]
    end

    subgraph QueueWorker ["Async Queue & Job Management"]
        LocalQueue["LocalQueue Worker Thread"]
        JobsDB[("SQLite Database\ngeneration_jobs / calendar_entries")]
    end

    subgraph AgentLayer ["Autonomous AI Agent System"]
        MRAgent["Market Research Agent"]
        CPAgent["Calendar Planner Agent"]
        CRAgent["Content Recommendation Agent"]
        BRAgent["Brand Reviewer Agent"]
        VPAgent["Visual Prompt Agent"]
    end

    subgraph LLMPool ["Multi-Provider Load Balancer & Failover Engine"]
        MultiLLM["MultiProviderLLM Router"]
        Groq1["Groq Key 1 (gpt-oss-20b)"]
        Groq2["Groq Key 2 (gpt-oss-20b)"]
        Gemini["Google Gemini 3.6 Flash"]
        OpenAIClient["OpenAI gpt-4o-mini (Backup)"]
    end

    subgraph ExternalServices ["External Intelligence & KB"]
        Tavily["Tavily Web Search API"]
        ChromaKB[("ChromaDB Vector Store\nBrand & Product Knowledge")]
    end

    User UI -->|POST /api/projects/1/plans| Routes
    Routes -->|1. Create Plan & Expunge ORM| Orchestrator
    Orchestrator -->|2. Enqueue Job| LocalQueue
    LocalQueue -->|Poll Jobs| JobsDB

    LocalQueue -->|3. Run Research| MRAgent
    LocalQueue -->|4. Generate Plan| CPAgent
    LocalQueue -->|5. Draft Content| CRAgent
    LocalQueue -->|6. Review Brand Compliance| BRAgent
    LocalQueue -->|7. Build Visual Prompts| VPAgent

    MRAgent -->|Fetch Live Trends| Tavily
    AgentLayer -->|Retrieve Product Specs| ChromaKB

    AgentLayer -->|8. Generate LLM Responses| MultiLLM
    MultiLLM -->|Round-Robin / Failover 1| Groq1
    MultiLLM -->|Round-Robin / Failover 2| Groq2
    MultiLLM -->|Round-Robin / Failover 3| Gemini
    MultiLLM -->|Fallback| OpenAIClient

    AgentLayer -->|9. Save Outputs & Scores| JobsDB
```

---

## 4. How the Multi-Provider Load Balancer Works

### A. Round-Robin Key Rotation
Every incoming request to `llm_provider.py` increments an internal index `current_idx`:
- **Request 1** ➔ Handled by `Groq-Key-1`
- **Request 2** ➔ Handled by `Groq-Key-2`
- **Request 3** ➔ Handled by `Gemini-3.6-Flash`
- **Request 4** ➔ Handled by `Groq-Key-1` ...

This distributes token consumption evenly across separate API quotas, preventing any single key from hitting rate limits.

### B. Instant Zero-Latency Failover
If a provider encounters:
- `HTTP 429` (Too Many Requests)
- `HTTP 413` (Request / TPM Limit Exceeded)
- Connection timeout or model capacity saturation

The `MultiProviderLLM` engine logs a warning and **immediately passes the request to the next active provider in the pool** without throwing runtime exceptions or causing background job failures.

### C. Quota Protection
If a provider returns `insufficient_quota` or `credit_balance_exhausted` (e.g. an uncredited key), the load balancer marks that provider `active = False` for the remainder of the session, eliminating unnecessary delay attempts.

---

## 5. End-to-End Execution Flow

1. **Plan Initiation (`POST /api/projects/{id}/plans`)**:
   - The user requests a marketing calendar for a specific date range (e.g., `2026-09-01` to `2026-09-10`), target platforms (Instagram, LinkedIn), and strategic objectives.
   - FastAPI validates inputs, initializes a `MarketingPlan` database row, expunges the SQLAlchemy instance to avoid detached session errors, and enqueues a `CALENDAR_PLAN` background job.

2. **Market Research Phase (`MarketResearchAgent`)**:
   - Queries Tavily API for current industry trends, car accessory market news, and upcoming Indian festival dates in the targeted month.
   - Vector-searches ChromaDB for relevant Qicdock product knowledge.
   - Synthesizes strategic market opportunities via `MultiProviderLLM`.

3. **Calendar Planning Phase (`CalendarPlannerAgent`)**:
   - Constructs a structured monthly marketing schedule with platform cadence, title, content pillar, target product, and audience segment.
   - Writes `calendar_entries` records to SQLite and enqueues `CONTENT_RECOMMENDATION` jobs for each date.

4. **Content Recommendation Phase (`ContentRecommendationAgent`)**:
   - For each entry, generates an attention-grabbing **Hook**, full **Narrative Concept**, **Caption Writing Direction**, **Call-To-Action (CTA)**, and **Visual Direction**.
   - Applies automated Pydantic schema normalization (normalizing camelCase/PascalCase keys and converting nested dictionaries/lists to strings).

5. **Brand Consistency Review Phase (`BrandReviewerAgent`)**:
   - Evaluates the generated content against Qicdock brand guidelines, technical product accuracy (e.g. Qi/MagSafe specs, 6-month warranty), and platform tone.
   - Assigns a quality score (`0.0 - 1.0`). If approved, triggers the `VisualPromptAgent`. If revisions are required, re-enqueues for refinement.

6. **Visual Prompt Generation (`VisualPromptAgent`)**:
   - Generates precise, high-resolution AI image prompts tailored to aspect ratios (e.g. 9:16 vertical Reels/Stories or 1:1 carousels) and visual aesthetic standards.
