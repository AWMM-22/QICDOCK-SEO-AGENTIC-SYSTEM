Yes. The agent needs a **single source-of-truth Markdown specification** that explains not just the architecture, but also **what each agent is responsible for, what it receives, what it produces, how agents communicate, RAG usage, validation, and final delivery**.


# Qicdock Agentic Marketing System

## 1. Project Overview

The **Qicdock Agentic Marketing System** is a multi-agent AI marketing automation system designed to analyze the Qicdock brand, products, audience, market, competitors, and external marketing data, then automatically generate a complete marketing strategy and content plan.

The system uses a central **Marketing Manager Agent (Orchestrator)** to coordinate specialized agents.

The system must use the **Brand Knowledge Base (RAG)** as the source of truth for brand-specific information and use **external sources** for market intelligence, trends, competitor analysis, and social-media insights.

The final output is a structured **Marketing Report** containing:

* Marketing strategy
* Audience insights
* Product insights
* Content strategy
* Instagram content ideas
* Reels concepts and scripts
* Stories ideas
* Visual/image requirements
* Captions
* Content calendar
* Recommendations
* Strategy rationale
* Supporting insights

The completed report is then delivered through the **Email Agent** or a dashboard.

---

# 2. Primary Goal

Build an autonomous agentic marketing system that can take Qicdock's brand knowledge and external marketing intelligence as input and produce a **high-quality, brand-aligned, actionable marketing plan with platform-specific content**.

The system should minimize manual marketing planning.

The Marketing Manager Agent should determine:

1. What information is required.
2. Which agents need to be executed.
3. Which agents can run in parallel.
4. What information should be retrieved from the Brand Knowledge Base.
5. What external research is required.
6. How outputs from multiple agents should be combined.
7. Whether outputs satisfy brand rules.
8. What needs to be regenerated or corrected.
9. How the final report should be structured.
10. When the final report is ready for delivery.

---

# 3. System Goals

## 3.1 Brand Understanding

The system must understand the Qicdock brand before generating marketing content.

The Brand Knowledge Base should contain:

* Brand story
* Products
* Product features
* Product benefits
* Target audience
* Brand voice
* Visual identity
* USPs
* Positioning
* Competitors
* Marketing claims
* Do's and Don'ts
* Other relevant business information

Brand-specific information must primarily come from RAG rather than being invented by agents.

---

## 3.2 Product Understanding

The system must analyze Qicdock products and identify but thsi is not a repetitve pat of like this is a 1 time agent which is not called everythime a process runs this is like i will provide 1 time info and it will stor in knowlege base like features benefits etc and only if i want to update the knowledge base after adding any product then i will manually trigegr it and it will add the things or udate the knowledge base and after wareds other agents will extract agents info from this:

* Product features
* Product benefits
* Key differentiators
* USPs
* Customer value
* Possible marketing angles
* Problems solved by the product
* Relevant use cases
* Potential content opportunities

---

## 3.3 Market Understanding

The system must analyze :

* Target audience
* Audience segments
* Audience pain points
* Audience needs
* Market trends
* Competitors
* Competitor positioning
* Competitor content
* Relevant social-media trends
* Market opportunities

---

## 3.4 Content Strategy

The system must transform research and insights into a coherent content strategy.

The strategy should define:

* Content pillars
* Themes
* Marketing objectives
* Content formats
* Platform strategy
* Content frequency
* Audience-specific messaging
* Content priorities
* Recommended topics
* Content calendar

---

## 3.5 Platform-Specific Content

The system must generate content specifically optimized for:

* Instagram Feed
* Instagram Reels
* Instagram Stories
* Visual/image-based content

Content should not simply be duplicated across platforms.

Each platform agent should adapt the strategy to the platform's characteristics.

---

## 3.6 Brand Safety and Quality

Every generated output must be checked for:

* Brand alignment
* Brand voice
* Factual accuracy
* Product accuracy
* Marketing claim accuracy
* Visual consistency
* Compliance with brand Do's and Don'ts
* Unsupported claims
* Contradictions with the Brand Knowledge Base

The system must not knowingly invent product features, benefits, statistics, or marketing claims.

---

# 4. High-Level Architecture

```text
                         ┌──────────────────────┐
                         │  BRAND KNOWLEDGE BASE │
                         │        (RAG)          │
                         └──────────┬───────────┘
                                    │
                                    ▼
┌───────────────────┐      ┌────────────────────────┐
│ External Sources  │─────▶│ Marketing Manager Agent│
│                   │      │     Orchestrator       │
│ Instagram         │      └───────────┬────────────┘
│ YouTube           │                  │
│ Web/Search        │                  │
│ Competitors       │                  │
└───────────────────┘                  │
                                      ▼
       ┌──────────────┬───────────────┼──────────────┬───────────────┐
       ▼              ▼               ▼              ▼               ▼
 Product Analyst  Market &       Content        Instagram       Reels
    Agent         Audience       Strategy         Agent          Agent
                    Agent          Agent
       │              │               │              │               │
       └──────────────┴───────────────┴──────────────┴───────────────┘
                                      │
                                      ▼
                            Stories Agent
                                      │
                                      ▼
                         Visual Generation Agent
                                      │
                                      ▼
                           Brand Reviewer Agent
                                      │
                                      ▼
                      Marketing Report Agent
                                      │
                                      ▼
                              Email Agent
                                      │
                                      ▼
                              Final Recipient
```

---

# 5. Agent Architecture

There are 11 major components/agents.

1. Marketing Manager Agent
2. Product Analyst Agent
3. Market & Audience Agent
4. Content Strategy Agent
5. Instagram Agent
6. Reels Agent
7. Stories Agent
8. Visual/Image Generation Agent
9. Brand Reviewer Agent
10. Marketing Report Agent
11. Email Agent

Supporting infrastructure:

* PostgreSQL
* Vector Database
* Redis
* LangGraph
* Logging and Monitoring

---

# 6. Agent 1 — Marketing Manager Agent

## Role

The Marketing Manager Agent is the **central orchestrator** of the entire system.

It is responsible for understanding the marketing objective, retrieving required brand context, delegating work to specialized agents, monitoring their outputs, resolving dependencies, triggering revisions, and coordinating final report generation.

## Responsibilities

* Understand business/marketing goals.
* Retrieve relevant brand information through RAG.
* Determine required research.
* Delegate tasks to specialized agents.
* Run independent agents in parallel when possible.
* Track agent status.
* Pass outputs between agents.
* Detect missing information.
* Request additional research.
* Trigger reviewer validation.
* Handle failures.
* Resolve conflicts between outputs.
* Decide when the system is ready for final report generation.
* Send the final structured output to the Marketing Report Agent.

## Input

```text
Marketing Objective
Brand Context
Product Information
Target Audience
Requested Platforms
Time Period
Additional User Requirements
```

## Output

```text
Marketing Execution Plan
Agent Tasks
Research Requirements
Agent Outputs
Validated Results
Final Report Request
```

## Important Behavior

The Marketing Manager must NOT generate everything itself.

It should delegate specialized work to the appropriate agents.

---

# 7. Agent 2 — Product Analyst Agent

## Role

Analyze Qicdock products and convert product information into marketing-relevant insights.

## Responsibilities

* Analyze products.
* Extract features.
* Extract benefits.
* Identify USPs.
* Identify differentiators.
* Identify customer problems solved.
* Identify possible marketing angles.
* Identify product-specific content opportunities.

## Input

```text
Product Information
Brand Knowledge Base Context
Marketing Objective
```

## Output

```json
{
  "products": [],
  "features": [],
  "benefits": [],
  "usps": [],
  "differentiators": [],
  "customer_problems": [],
  "marketing_angles": [],
  "content_opportunities": []
}
```

The agent must not invent product capabilities.

---

# 8. Agent 3 — Market & Audience Agent

## Role

Analyze the target market, audience, trends, and competitors.

## Responsibilities

* Identify target audience segments.
* Analyze audience needs.
* Analyze pain points.
* Identify customer motivations.
* Identify market trends.
* Analyze competitor positioning.
* Analyze competitor content.
* Identify opportunities.
* Identify gaps in competitor strategies.
* Provide actionable audience insights.

## Data Sources

The agent may use:

* Web/Search
* Instagram
* YouTube
* Competitor websites
* Competitor social media
* Brand Knowledge Base

## Output

```json
{
  "audience_segments": [],
  "pain_points": [],
  "needs": [],
  "motivations": [],
  "market_trends": [],
  "competitors": [],
  "competitor_insights": [],
  "market_gaps": [],
  "opportunities": []
}
```

External information should be clearly separated from information retrieved from the Brand Knowledge Base.

---

# 9. Agent 4 — Content Strategy Agent

## Role

Convert product and market insights into an overall content strategy.

## Inputs

* Product Analyst output
* Market & Audience output
* Brand Knowledge Base
* Marketing objective

## Responsibilities

* Define content pillars.
* Define content themes.
* Map content to audience segments.
* Recommend platforms.
* Recommend content formats.
* Define messaging strategy.
* Define content priorities.
* Create content calendar structure.
* Determine which content should be Feed/Reel/Story.
* Create strategic rationale.

## Output

```json
{
  "content_pillars": [],
  "themes": [],
  "messaging_strategy": [],
  "platform_strategy": {},
  "content_formats": [],
  "priorities": [],
  "content_calendar": [],
  "recommendations": []
}
```

The Content Strategy Agent provides the strategic foundation for the downstream content agents.

---

# 10. Agent 5 — Instagram Agent

## Role

Generate Instagram Feed content based on the approved content strategy.

## Responsibilities

* Generate Instagram post ideas.
* Generate captions.
* Generate hooks.
* Recommend carousel concepts.
* Recommend post structure.
* Recommend CTA.
* Recommend visual direction.
* Optimize content for Instagram.

## Input

```text
Content Strategy
Product Insights
Audience Insights
Brand Voice
Brand Do's and Don'ts
```

## Output

```json
{
  "post_ideas": [],
  "captions": [],
  "hooks": [],
  "carousel_ideas": [],
  "visual_recommendations": [],
  "cta": [],
  "hashtags": []
}
```

---

# 11. Agent 6 — Reels Agent

## Role

Generate short-form video content for Instagram Reels.

## Responsibilities

* Generate Reel concepts.
* Generate hooks.
* Generate scripts.
* Suggest shot breakdowns.
* Suggest transitions.
* Suggest visual storytelling.
* Suggest CTA.
* Recommend duration.
* Identify trends when supported by external research.

## Output

```json
{
  "reel_concepts": [],
  "hooks": [],
  "scripts": [],
  "shot_breakdown": [],
  "visual_direction": [],
  "cta": [],
  "recommended_duration": ""
}
```

The agent should prioritize engaging storytelling rather than simply converting an Instagram post into a video.

---

# 12. Agent 7 — Stories Agent

## Role

Generate Instagram Stories strategies and sequences.

## Responsibilities

* Generate Story ideas.
* Create Story sequences.
* Generate polls.
* Generate questions.
* Generate interactive elements.
* Suggest CTAs.
* Create narrative flow.

## Output

```json
{
  "story_ideas": [],
  "story_sequences": [],
  "polls": [],
  "questions": [],
  "interactive_elements": [],
  "cta": []
}
```

Stories should be designed as a sequence when appropriate rather than isolated posts.

---

# 13. Agent 8 — Visual / Image Generation Agent

## Role

Convert content strategy and content ideas into visual requirements and, when supported, generated visual assets.

## Responsibilities

* Generate visual concepts.
* Create product visual concepts.
* Generate image prompts.
* Create carousel visual directions.
* Create infographic concepts.
* Maintain visual identity.
* Ensure product representation is accurate.
* Follow brand visual guidelines.

## Input

```text
Brand Visual Identity
Product Information
Content Ideas
Platform
Content Type
```

## Output

```json
{
  "visual_concepts": [],
  "image_prompts": [],
  "carousel_designs": [],
  "infographic_ideas": [],
  "visual_requirements": []
}
```

The agent must never alter important product characteristics incorrectly.

---

# 14. Agent 9 — Brand Reviewer Agent

## Role

The Brand Reviewer is the **quality-control layer**.

Every major content output should pass through this agent before being included in the final report.

## Responsibilities

Check:

### Brand Alignment

* Is the content consistent with the brand?
* Does it follow the brand voice?
* Does it follow positioning?

### Product Accuracy

* Are product features correct?
* Are benefits supported?
* Are claims supported?

### Brand Compliance

* Does it follow Do's and Don'ts?
* Does it violate visual identity requirements?
* Does it use unsupported claims?

### Content Quality

* Is the content useful?
* Is it relevant to the audience?
* Is the messaging clear?
* Is the CTA appropriate?

## Output

```json
{
  "status": "approved | needs_revision",
  "score": 0,
  "issues": [],
  "corrections": [],
  "approved_content": []
}
```

If `needs_revision`, the Marketing Manager must send the relevant output back to the responsible agent for regeneration.

---

# 15. Agent 10 — Marketing Report Agent

## Role

Compile all validated outputs into one complete marketing report.

## Responsibilities

* Collect validated outputs.
* Organize information.
* Remove duplicate content.
* Organize content by platform.
* Add strategic rationale.
* Include audience insights.
* Include product insights.
* Include content calendar.
* Include recommendations.
* Include visual requirements.
* Ensure report completeness.

## Report Structure

```text
1. Executive Summary

2. Marketing Objective

3. Brand Overview

4. Product Insights

5. Target Audience

6. Market & Competitor Insights

7. Marketing Opportunities

8. Content Strategy

9. Content Pillars

10. Instagram Feed Strategy

11. Instagram Post Ideas

12. Reels Strategy

13. Reels Concepts & Scripts

14. Stories Strategy

15. Stories Ideas

16. Visual Strategy

17. Visual/Image Requirements

18. Content Calendar

19. Recommendations

20. Key Insights

21. Next Steps
```

---

# 16. Agent 11 — Email Agent

## Role

Deliver the final marketing report to the specified recipient.

## Responsibilities

* Receive finalized report.
* Format the report for email delivery.
* Attach required files.
* Attach generated visuals when required.
* Include content calendar.
* Send email.
* Confirm delivery status.

## Input

```text
Final Marketing Report
Attachments
Recipient
```

## Output

```json
{
  "status": "sent | failed",
  "recipient": "",
  "attachments": [],
  "timestamp": "",
  "error": null
}
```

The Email Agent should not modify the strategic content.

---

# 17. Brand Knowledge Base / RAG

The Brand Knowledge Base is the primary source of truth for brand-specific information.

## Knowledge Categories

```text
Brand
├── Brand Story
├── Brand Voice
├── Visual Identity
├── Positioning
├── USPs
├── Target Audience
├── Products
│   ├── Product Information
│   ├── Features
│   ├── Benefits
│   └── Use Cases
├── Competitors
├── Marketing Claims
├── Do's
├── Don'ts
└── Business Information
```

## RAG Rules

Agents should retrieve only the information relevant to their task.

Examples:

```text
Product Agent
→ Product features + benefits + USPs

Market Agent
→ Target audience + positioning + competitors

Instagram Agent
→ Brand voice + visual identity + product information

Visual Agent
→ Visual identity + product information

Brand Reviewer
→ Entire relevant brand policy + Do's/Don'ts + claims
```

The system should avoid sending the entire knowledge base to every agent unnecessarily.

---

# 18. External Sources

The system can collect external information from:

## Instagram

Use for:

* Content trends
* Engagement patterns
* Competitor content
* Content formats
* Audience signals

## YouTube

Use for:

* Video trends
* Competitor videos
* Educational content
* Content ideas
* Audience interests

## Web / Search

Use for:

* Market trends
* Industry news
* Consumer trends
* Competitor research
* Relevant topics

## Competitors

Use for:

* Product positioning
* Marketing strategy
* Social content
* Messaging
* Offers
* Content gaps

External data must not override confirmed brand information.

---

# 19. Agent Execution Strategy

The system should use a graph-based orchestration approach.

Recommended flow:

```text
START
  │
  ▼
Marketing Manager
  │
  ├──────────────► Product Analyst
  │
  ├──────────────► Market & Audience
  │
  └──────────────► Brand Context Retrieval
                         │
                         ▼
              Content Strategy Agent
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
         Instagram     Reels      Stories
              │          │          │
              └──────────┼──────────┘
                         ▼
                  Visual Agent
                         │
                         ▼
                  Brand Reviewer
                         │
              ┌──────────┴──────────┐
              │                     │
          Approved             Needs Revision
              │                     │
              ▼                     └──► Responsible Agent
      Marketing Report                     │
              │                            └──► Reviewer
              ▼
          Email Agent
              │
              ▼
             END
```

---

# 20. Parallel Execution

The following agents should be capable of running in parallel when their dependencies are satisfied:

```text
Product Analyst
Market & Audience Agent
```

After Content Strategy is generated:

```text
Instagram Agent
Reels Agent
Stories Agent
```

may run in parallel.

Visual generation can then process the resulting content requirements.

This reduces overall execution time.

---

# 21. Dependency Rules

```text
Marketing Manager
        ↓
Product Analyst + Market Agent
        ↓
Content Strategy
        ↓
Instagram + Reels + Stories
        ↓
Visual Agent
        ↓
Brand Reviewer
        ↓
Marketing Report
        ↓
Email
```

No downstream agent should execute using incomplete critical dependencies.

---

# 22. State Management

The system should maintain a shared state containing:

```python
MarketingState = {
    "marketing_objective": {},
    "brand_context": {},
    "product_analysis": {},
    "market_analysis": {},
    "audience_analysis": {},
    "content_strategy": {},
    "instagram_content": {},
    "reels_content": {},
    "stories_content": {},
    "visual_content": {},
    "review_results": {},
    "final_report": {},
    "email_status": {},
    "errors": [],
    "execution_metadata": {}
}
```

LangGraph should manage transitions between agents.

---

# 23. Agent Communication Rules

Every agent should have:

### Input Contract

Clearly defined data it expects.

### Task

Clearly defined responsibility.

### Output Contract

Structured output that downstream agents can consume.

### Validation

Check whether required information exists before execution.

### Error State

Return structured errors rather than silently failing.

Example:

```json
{
  "status": "error",
  "agent": "product_analyst",
  "error": "Product information unavailable",
  "recoverable": true,
  "recommended_action": "Retrieve product information from RAG"
}
```

---

# 24. Quality Control Loop

The Brand Reviewer should create a feedback loop.

```text
Generated Content
       ↓
Brand Reviewer
       ↓
   ┌───┴────┐
   │        │
APPROVED  REJECTED
   │        │
   │        ▼
   │   Identify Issues
   │        │
   │        ▼
   │  Responsible Agent
   │        │
   │        ▼
   │   Regenerate
   │        │
   └────────┘
       ↓
Marketing Report
```

The system should have a configurable maximum retry count to prevent infinite loops.

Recommended default:

```text
MAX_REVIEW_RETRIES = 2
```

If the content still fails after the maximum retries, the Marketing Manager should flag it for human review instead of repeatedly regenerating it.

---

# 25. Hallucination Prevention

The system must follow these rules:

1. Never invent product features.
2. Never invent product specifications.
3. Never invent statistics.
4. Never invent customer testimonials.
5. Never create unsupported marketing claims.
6. Never contradict the Brand Knowledge Base.
7. Distinguish external research from verified brand information.
8. If information is unavailable, explicitly report that it is unavailable.
9. Do not assume unknown business information.
10. Use retrieved context when making brand-specific claims.

---

# 26. Source Attribution

Research-based insights should maintain source metadata.

Recommended structure:

```json
{
  "insight": "Example market insight",
  "source_type": "web",
  "source": "source_identifier",
  "confidence": 0.87
}
```

Brand Knowledge Base information should also retain retrieval metadata where possible.

This allows the final report to distinguish:

```text
Brand Knowledge
External Research
Agent Inference
Recommendation
```

---

# 27. Supporting Infrastructure

## PostgreSQL

Use PostgreSQL for:

* Agent execution records
* Marketing campaigns
* Reports
* Content metadata
* User/project configuration
* Audit records

---

## Vector Database

Use the vector database for:

* Brand Knowledge Base embeddings
* Semantic retrieval
* Product knowledge
* Brand guidelines
* Historical marketing information

---

## Redis

Use Redis for:

* Short-term state
* Caching
* Frequently accessed RAG results
* Task queues where required
* Temporary agent execution data

---

## LangGraph

Use LangGraph for:

* Agent orchestration
* State management
* Conditional routing
* Parallel execution
* Retry loops
* Human-review checkpoints
* Workflow persistence

---

## Logging & Monitoring

Every agent execution should log:

```text
execution_id
campaign_id
agent_name
start_time
end_time
status
input_summary
output_summary
tokens_used
model_used
errors
retry_count
```

Sensitive information should not be unnecessarily logged.

---

# 28. Recommended Project Structure

```text
qicdock-agentic-marketing/
│
├── agents/
│   ├── marketing_manager/
│   ├── product_analyst/
│   ├── market_audience/
│   ├── content_strategy/
│   ├── instagram/
│   ├── reels/
│   ├── stories/
│   ├── visual_generation/
│   ├── brand_reviewer/
│   ├── marketing_report/
│   └── email/
│
├── orchestration/
│   ├── graph.py
│   ├── state.py
│   └── routing.py
│
├── rag/
│   ├── ingestion/
│   ├── retrieval/
│   ├── embeddings/
│   └── vector_store/
│
├── external_sources/
│   ├── instagram/
│   ├── youtube/
│   ├── web_search/
│   └── competitors/
│
├── database/
│   ├── postgres/
│   └── redis/
│
├── models/
│   └── schemas/
│
├── prompts/
│   ├── marketing_manager.md
│   ├── product_analyst.md
│   ├── market_audience.md
│   ├── content_strategy.md
│   ├── instagram.md
│   ├── reels.md
│   ├── stories.md
│   ├── visual_generation.md
│   ├── brand_reviewer.md
│   ├── marketing_report.md
│   └── email.md
│
├── monitoring/
│
├── tests/
│
├── config/
│
├── .env.example
├── requirements.txt
├── README.md
└── AGENT_PLAN.md
```

---

# 29. Implementation Principles

## Principle 1 — Orchestrator, Not Monolith

The Marketing Manager should coordinate agents rather than doing every task itself.

## Principle 2 — Specialized Agents

Each agent should have one clearly defined responsibility.

## Principle 3 — Structured Communication

Agents should communicate through structured state/schema rather than uncontrolled natural-language outputs.

## Principle 4 — RAG as Source of Truth

Brand-specific facts must come from the Brand Knowledge Base.

## Principle 5 — Parallel Where Possible

Independent tasks should execute concurrently.

## Principle 6 — Validation Before Finalization

Content must pass Brand Review before entering the final report.

## Principle 7 — Traceability

Important insights should be traceable to their source or originating agent.

## Principle 8 — Failure Recovery

A single agent failure should not unnecessarily crash the entire workflow.

## Principle 9 — Human-in-the-Loop

The system should support human approval for:

* High-risk marketing claims
* Repeated review failures
* Important strategic decisions
* Final campaign approval

---

# 30. End-to-End Example

Suppose the user requests:

> "Create a 30-day Instagram marketing strategy for Qicdock."

The system should execute approximately as follows:

### Step 1 — Marketing Manager

Understands:

```text
Objective:
30-day Instagram marketing strategy

Platform:
Instagram

Duration:
30 days
```

Retrieves relevant brand context.

---

### Step 2 — Product Analyst

Analyzes Qicdock products and returns:

```text
Features
Benefits
USPs
Differentiators
Marketing angles
```

---

### Step 3 — Market & Audience Agent

Researches:

```text
Target audience
Pain points
Competitors
Current trends
Market opportunities
```

---

### Step 4 — Content Strategy Agent

Creates:

```text
Content pillars
Themes
Platform strategy
Messaging
30-day content structure
```

---

### Step 5 — Content Agents

Instagram Agent:

```text
Feed posts
Carousels
Captions
CTAs
```

Reels Agent:

```text
Reel concepts
Hooks
Scripts
Shot breakdowns
```

Stories Agent:

```text
Stories
Polls
Questions
Interactive sequences
```

---

### Step 6 — Visual Agent

Creates:

```text
Image concepts
Image prompts
Carousel designs
Visual directions
```

---

### Step 7 — Brand Reviewer

Checks everything against:

```text
Brand voice
Brand identity
Product information
USPs
Marketing claims
Do's & Don'ts
```

Rejected content goes back to the responsible agent.

---

### Step 8 — Marketing Report Agent

Creates:

```text
Executive Summary
Strategy
Audience Insights
Product Insights
Content Pillars
30-Day Calendar
Instagram Posts
Reels
Stories
Visual Requirements
Recommendations
```

---

### Step 9 — Email Agent

Formats and sends the completed marketing report to the configured recipient.

---

# 31. Definition of Done

The system is considered successfully implemented when:

* [ ] Marketing Manager can orchestrate the complete workflow.
* [ ] Brand Knowledge Base can be queried through RAG.
* [ ] Product Analyst produces structured product insights.
* [ ] Market & Audience Agent performs external research.
* [ ] Content Strategy Agent creates a coherent strategy.
* [ ] Instagram Agent generates feed content.
* [ ] Reels Agent generates Reel concepts and scripts.
* [ ] Stories Agent generates Story sequences.
* [ ] Visual Agent generates visual requirements/prompts.
* [ ] Brand Reviewer validates outputs.
* [ ] Failed content can be regenerated.
* [ ] Marketing Report Agent compiles the final report.
* [ ] Email Agent delivers the report.
* [ ] Agent state is persisted.
* [ ] Agent executions are logged.
* [ ] Errors are handled gracefully.
* [ ] Retry limits prevent infinite loops.
* [ ] Brand-specific claims are grounded in RAG.
* [ ] External research is distinguishable from brand knowledge.
* [ ] Human review can be triggered when required.
* [ ] Complete end-to-end workflow can run successfully.

---

# 32. Core System Objective

The final system should behave like a **virtual marketing team**, not a collection of independent chatbots.

The desired behavior is:

```text
UNDERSTAND
    ↓
RESEARCH
    ↓
ANALYZE
    ↓
STRATEGIZE
    ↓
CREATE
    ↓
VISUALIZE
    ↓
REVIEW
    ↓
REFINE
    ↓
COMPILE
    ↓
DELIVER
```

The Marketing Manager Agent is responsible for coordinating this entire lifecycle.

The specialized agents are responsible for their respective domains.

The Brand Knowledge Base provides brand truth.

External sources provide market intelligence.

The Brand Reviewer provides quality control.

The Marketing Report Agent produces the final business deliverable.

The Email Agent delivers it.

The entire architecture should be implemented as a reliable, observable, modular, and extensible agentic workflow.
