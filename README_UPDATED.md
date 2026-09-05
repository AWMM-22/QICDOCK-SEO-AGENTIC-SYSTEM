# Qicdock Agentic Marketing Calendar System

## 1. Project Overview

The **Qicdock Agentic Marketing Calendar System** is a calendar-first AI
marketing planning and content recommendation system.

The system takes the Qicdock **Brand Knowledge Base**, product
information, audience context, and optional external market/trend
research and uses an LLM-driven marketing brain to decide:

-   **When** Qicdock should post
-   **Whether** a post is actually needed on a particular day
-   **What** type of content should be published
-   **Which** platform should receive it
-   **Which** product, audience segment, content pillar, or marketing
    objective should be used
-   **Why** the content is recommended
-   **What** the content should say
-   **What** visual should be created
-   **What image-generation prompt** should be sent to an image provider
    later

The primary user experience is a **monthly marketing calendar**, not a
traditional RAG/chat interface.

The user selects **Create Monthly Plan**, enters or confirms the month
start and end dates, and the system creates a practical content
schedule. The LLM is explicitly allowed to leave days empty. It must not
blindly generate one recommendation for every day.

The system should behave like a marketing strategist that understands
cadence, audience attention, platform differences, campaign sequencing,
product priorities, and relevant opportunities.

------------------------------------------------------------------------

# 2. Primary Product Experience

## 2.1 Calendar-first UI

The main dashboard should show a monthly calendar.

Example:

``` text
┌─────────────────────────────────────────────────────────────┐
│ Qicdock Marketing Calendar                                  │
│                                                             │
│                    [ Create Monthly Plan ]                  │
├─────────────────────────────────────────────────────────────┤
│                 September 2026                              │
│                                                             │
│ Mon     Tue     Wed     Thu     Fri     Sat     Sun         │
│  1       2       3       4       5       6       7          │
│         EMPTY           REEL                            POST│
│                                                             │
│  8       9      10      11      12      13      14          │
│                 CAROUSEL                STORY              │
│                                                             │
│ ...                                                         │
└─────────────────────────────────────────────────────────────┘
```

A calendar day can be:

-   **Empty** --- no post recommended
-   **Planned** --- recommendation exists
-   **Generating** --- content is being generated
-   **Ready** --- recommendation/content is available
-   **Failed** --- generation failed but the rest of the plan remains
    usable
-   **Skipped** --- intentionally left unused by the planner

The calendar is the source of truth for the user's marketing schedule.

------------------------------------------------------------------------

# 3. Create Monthly Plan Flow

When the user clicks **Create Monthly Plan**, open a dedicated planning
view/modal/tab.

Required inputs:

``` text
Month Start Date
Month End Date
Platforms
Marketing Objective (optional)
Additional Instructions (optional)
```

Example:

``` text
Create Monthly Plan

Start Date: 01/09/2026
End Date:   30/09/2026

Platforms:
[x] Instagram
[x] LinkedIn

Marketing Objective:
Increase product awareness and audience engagement

Additional Instructions:
Optional

                    [Create Plan]
```

The system must validate:

-   Start date exists
-   End date exists
-   Start date \<= end date
-   Date range is reasonable
-   At least one platform is selected

The user should not need to provide internal identifiers such as:

-   `org_id`
-   `organization_id`
-   `day_id`
-   generated UUIDs
-   internal database IDs

These identifiers must be internal implementation details only.

The UI and LLM workflow must not require the user to provide them.

------------------------------------------------------------------------

# 4. Core Planning Philosophy

The system must **not** follow this behavior:

``` text
September 1 → Post
September 2 → Post
September 3 → Post
September 4 → Post
...
September 30 → Post
```

That is not a practical marketing calendar.

Instead, the marketing brain must determine an appropriate cadence.

Example:

``` text
September 1 → No post
September 2 → No post
September 3 → Reel
September 4 → No post
September 5 → Carousel
September 6 → No post
September 7 → Story
September 8 → No post
...
```

The model should decide whether a day deserves content based on:

-   Marketing objective
-   Audience behavior
-   Platform
-   Content fatigue
-   Previous planned content
-   Product priorities
-   Content pillars
-   Campaign sequence
-   Relevant events/festivals/occasions
-   Market/trend information
-   Strategic gaps
-   Spacing between posts
-   Content format diversity
-   Historical performance when available

The system must prefer **quality and strategic timing over calendar
density**.

------------------------------------------------------------------------

# 5. Festival and Occasion Intelligence

The system must not hardcode a generic rule such as:

``` text
If festival exists → post
```

The LLM must evaluate whether an occasion is actually relevant to
Qicdock.

For every potential festival, holiday, event, or occasion, the planner
should consider:

1.  Is it relevant to Qicdock's audience?
2.  Is it relevant to the product category?
3.  Can Qicdock naturally participate in the conversation?
4.  Does it provide a meaningful marketing opportunity?
5.  Would posting feel forced?
6.  Does it conflict with another planned campaign?
7.  Is a promotional post appropriate?
8.  Would an educational, entertaining, contextual, or
    community-oriented post be better?

Example:

``` text
Occasion detected:
Ganesh Chaturthi

Decision:
Relevant

Reason:
The occasion has strong relevance to the target Indian audience
and can naturally connect with travel, convenience, or vehicle-use
content.

Recommendation:
Create a contextual Reel rather than a generic festival greeting.
```

An irrelevant international event must not automatically become a
Qicdock post.

------------------------------------------------------------------------

# 6. Marketing Brain / Calendar Planner Agent

The **Calendar Planner Agent** is the central intelligence responsible
for creating the monthly plan.

It replaces the previous report-first flow.

## Responsibilities

The Calendar Planner must:

-   Understand the requested date range
-   Retrieve relevant brand knowledge
-   Understand available products
-   Understand target audience
-   Understand marketing objectives
-   Review existing/planned content
-   Analyze relevant external information when available
-   Determine practical posting cadence
-   Select posting dates
-   Leave unnecessary dates empty
-   Select platforms
-   Select content formats
-   Select products/topics
-   Sequence content logically
-   Avoid repetitive recommendations
-   Create strategic rationale
-   Return structured calendar entries
-   Support incremental generation
-   Preserve successfully generated entries when later entries fail

## Input

``` json
{
  "start_date": "2026-09-01",
  "end_date": "2026-09-30",
  "platforms": ["instagram", "linkedin"],
  "marketing_objective": "...",
  "additional_instructions": "..."
}
```

The agent retrieves the required context from the knowledge base instead
of receiving the entire knowledge base unnecessarily.

## Output

``` json
{
  "plan_status": "ready",
  "date_range": {
    "start": "2026-09-01",
    "end": "2026-09-30"
  },
  "strategy_summary": "...",
  "recommended_frequency": {
    "instagram": "...",
    "linkedin": "..."
  },
  "calendar_entries": [
    {
      "date": "2026-09-04",
      "platform": "instagram",
      "content_type": "reel",
      "status": "planned",
      "title": "...",
      "objective": "...",
      "product": "...",
      "audience": "...",
      "reason": "...",
      "sequence_position": 1
    }
  ]
}
```

No `day_id` is required in the LLM output.

The date itself is sufficient to identify a calendar entry.

------------------------------------------------------------------------

# 7. Calendar Entry Model

Each planned post should contain enough information to display a useful
recommendation when the user clicks a calendar date.

Recommended structure:

``` json
{
  "date": "2026-09-04",
  "platform": "instagram",
  "content_type": "reel",
  "title": "The everyday problem your car setup can solve",
  "status": "planned",
  "objective": "awareness",
  "content_pillar": "problem_solution",
  "product": "Qicdock Wireless Charger",
  "target_audience": "daily commuters",
  "hook": "...",
  "concept": "...",
  "caption_direction": "...",
  "cta": "...",
  "visual_direction": "...",
  "image_prompt": "...",
  "reason": "...",
  "sequence_position": 1
}
```

The system should not generate all final content unless requested.

The first stage is **planning**.

------------------------------------------------------------------------

# 8. Clicking a Calendar Day

When the user clicks a date, open a detail panel.

Example:

``` text
September 4

Instagram Reel

"The everyday problem your car setup can solve"

Objective:
Awareness

Audience:
Daily commuters

Product:
Qicdock Wireless Charger

Why this day:
This follows the previous awareness content with a
problem-solution format and creates a natural transition
toward product consideration.

Hook:
"Still reaching for your phone while driving?"

Concept:
Show the common problem → introduce the product →
demonstrate the solution → CTA.

Visual Direction:
Realistic in-car product demonstration.

Image Prompt:
[Generated prompt]

[Generate Image]
[Edit Recommendation]
[Back to Calendar]
```

If the date is intentionally empty:

``` text
September 6

No post recommended.

Reason:
The previous two posts already provide sufficient audience
touchpoints. Leaving this day empty avoids unnecessary
content frequency and gives the audience breathing room.
```

An empty day is a valid and expected output.

------------------------------------------------------------------------

# 9. Content Types

The planner can choose from multiple formats.

Supported types should include:

### Instagram

-   Single image post
-   Carousel
-   Reel
-   Story
-   Story sequence
-   Product showcase
-   Educational post
-   Problem/solution post
-   Comparison
-   Community/engagement post
-   UGC-style concept
-   Promotional content when strategically justified

### LinkedIn

-   Text post
-   Image post
-   Carousel/document-style post
-   Educational post
-   Product/business insight
-   Founder/brand story
-   Industry insight
-   Case-study style content
-   Customer problem/solution content

The model should select the format based on the objective rather than
randomly cycling through formats.

------------------------------------------------------------------------
# 9A. Individual Day Regeneration

The user must be able to regenerate a recommendation for **one specific calendar day** without regenerating the entire monthly plan.

When a user opens a generated calendar entry and does not like the recommendation, the detail panel should provide:

```text
[ Regenerate Recommendation ]
```

## Regeneration Behavior

When the user clicks **Regenerate Recommendation**:

```text
User selects September 4
        ↓
Clicks "Regenerate Recommendation"
        ↓
Current recommendation is sent back to Calendar/Content Brain
        ↓
LLM generates a new recommendation
        ↓
Brand Reviewer validates it
        ↓
New recommendation replaces the previous recommendation
        ↓
Calendar updates
```

The rest of the monthly calendar must remain unchanged.

For example:

```text
September 4  → Regenerate
September 8  → unchanged
September 13 → unchanged
September 18 → unchanged
September 23 → unchanged
```

Only September 4 is regenerated.

## Regeneration Input

The regeneration process should receive:

```json
{
  "plan_id": "...",
  "date": "2026-09-04",
  "platform": "instagram",
  "current_recommendation": {},
  "existing_calendar_context": [],
  "brand_context": {},
  "user_feedback": ""
}
```

`plan_id` and database identifiers are internal backend values. The user and LLM should not manually provide or generate them.

## User Feedback

The user should optionally be able to explain why they disliked the recommendation.

Example:

```text
Why do you want to regenerate?

[ The idea is too promotional. Give me something
  more engaging and educational. ]

[ Regenerate ]
```

Other examples:

```text
"Make it more creative."

"Don't focus on the product directly."

"Use a carousel instead of a reel."

"Make this suitable for LinkedIn."

"Give me a stronger hook."

"Try a completely different concept."
```

If no feedback is provided, the LLM should still generate a **meaningfully different recommendation** rather than returning the same idea.

## Important Regeneration Rules

Regeneration must:

1. Affect only the selected calendar entry.
2. Preserve all other calendar entries.
3. Consider the surrounding calendar sequence.
4. Avoid repeating the rejected concept.
5. Maintain brand and product accuracy.
6. Respect the original marketing objective.
7. Consider existing content before selecting the replacement.
8. Pass the replacement through Brand Review.
9. Preserve the previous recommendation for audit/history where practical.
10. Not automatically regenerate the image.

The LLM should understand the context of the surrounding dates so that the new recommendation does not break the overall marketing sequence.

For example:

```text
Sep 2 → Awareness
Sep 4 → [USER REJECTED]
Sep 8 → Product Solution
```

The replacement for Sep 4 should still logically connect:

```text
Sep 2 → Awareness
Sep 4 → New Problem/Education concept
Sep 8 → Product Solution
```

rather than generating an unrelated post.

## Regeneration Status

The selected entry should have its own generation status:

```text
ready
regenerating
ready
failed
```

While regenerating:

```text
September 4

Regenerating recommendation...

[ Disable Regenerate Button ]
```

Other calendar entries must remain fully usable.

## Failure Behavior

If regeneration fails:

```text
September 4
Previous recommendation
      ↓
Regeneration failed
```

The system should **not delete the previous working recommendation**.

Instead:

```json
{
  "status": "failed",
  "previous_recommendation_preserved": true,
  "error": "...",
  "retryable": true
}
```

The user can then retry:

```text
[ Try Again ]
```

## Recommendation History

Where practical, maintain previous versions:

```text
September 4

Version 1 — Rejected
Version 2 — Rejected
Version 3 — Current
```

The current version should be displayed by default.

This allows the system to maintain an audit trail and prevents accidental loss of previous generated recommendations.

## Image Behavior

Regenerating a recommendation must **not automatically call the image-generation API**.

The new flow remains:

```text
Regenerate Recommendation
        ↓
New Recommendation
        ↓
New Image Prompt
        ↓
User decides
        ↓
[ Generate Image ]
```

If an image had already been generated for the previous recommendation, the system should mark that image as belonging to the previous recommendation/version rather than silently attaching it to the new recommendation.

The user must explicitly generate a new image for the new recommendation.

## API

Recommended endpoint:

```http
POST /api/plans/{plan_id}/entries/{date}/regenerate
```

Request:

```json
{
  "feedback": "Make it more educational and less promotional."
}
```

Response:

```json
{
  "date": "2026-09-04",
  "status": "regenerating"
}
```

The operation should be processed through the same queue mechanism so that rate limits and failures do not affect the rest of the calendar.

## Core Principle

> **Regeneration is entry-level, not plan-level.**

The user should never have to regenerate the entire month just because they dislike one day's recommendation.


# 10. Platform Strategy

Instagram and LinkedIn must not receive identical content.

## Instagram

Prioritize:

-   Visual storytelling
-   Reels
-   Carousels
-   Short hooks
-   Product demonstrations
-   Educational visual content
-   Audience interaction
-   Stories
-   Strong visual identity

## LinkedIn

Prioritize:

-   Business relevance
-   Professional insights
-   Educational content
-   Industry perspectives
-   Product/business problem solving
-   Founder/brand storytelling
-   Thought leadership
-   Practical takeaways

A single idea may be adapted between platforms, but it must be rewritten
for the platform.

------------------------------------------------------------------------

# 11. Content Sequencing

The planner must think about the calendar as a **sequence**, not a
collection of independent posts.

Example:

``` text
Day 1
Awareness
    ↓
Day 4
Problem / Pain Point
    ↓
Day 8
Product Solution
    ↓
Day 13
Educational / Value
    ↓
Day 18
Engagement
    ↓
Day 23
Product Demonstration
    ↓
Day 28
Conversion / CTA
```

This creates a marketing journey.

The planner should track relationships between entries through:

``` json
{
  "sequence_position": 3,
  "campaign_thread": "wireless_charging_awareness",
  "follows_entry": "2026-09-04",
  "supports_entry": "2026-09-13"
}
```

These are optional internal fields and must never be exposed as required
user input.

------------------------------------------------------------------------

# 12. Queue-Based Incremental Execution

A major requirement is that the system must work even when the LLM/API
has rate limits, timeouts, or partial failures.

The system must **never discard successful work because a later task
fails**.

Example:

``` text
Create Monthly Plan
        ↓
Planner creates 10 recommended dates
        ↓
Queue
        ↓
Entry 1 → SUCCESS → visible
Entry 2 → SUCCESS → visible
Entry 3 → SUCCESS → visible
Entry 4 → API LIMIT
        ↓
Pause/retry later
        ↓
Entries 1–3 remain visible
```

The user should be able to open the calendar while generation is still
running.

Calendar entries must be persisted individually.

------------------------------------------------------------------------

# 13. Generation States

Every calendar entry should have a status.

Recommended values:

``` text
planned
queued
generating
ready
failed
retrying
skipped
```

Example:

``` json
{
  "date": "2026-09-04",
  "status": "ready"
}
```

If an API call fails:

``` json
{
  "date": "2026-09-08",
  "status": "failed",
  "error": "Provider rate limit",
  "retryable": true
}
```

The failed entry must not delete or invalidate other entries.

------------------------------------------------------------------------

# 14. Queue Implementation

Redis must **not** be required for the local/default setup.

The initial implementation should use a local queue that requires no
external infrastructure.

Recommended implementation:

``` text
FastAPI / Backend
      ↓
Database-backed job queue
      ↓
Worker
      ↓
LLM / Image Provider
```

The queue can be implemented using:

-   Database job records
-   A lightweight in-process worker
-   Background tasks
-   Polling
-   Thread/async worker where appropriate

The implementation should be simple enough to run locally with one
command.

Redis can be introduced later as an optional production queue backend.

### Local default

``` text
Redis = OFF
External queue = OFF
Database queue = ON
```

### Future production

``` text
Redis = optional
Celery/RQ/other worker system = optional
```

Do not make Redis a prerequisite for the application to start.

------------------------------------------------------------------------

# 15. Database Strategy

The system should be easy to run locally.

## Default local database

Use **SQLite** for the default development/local configuration.

SQLite is sufficient for:

-   Projects
-   Brand metadata
-   Marketing plans
-   Calendar entries
-   Job records
-   Execution status
-   Generated recommendations
-   Error records
-   User configuration
-   Image-generation requests
-   Audit information

Example:

``` text
data/
└── qicdock.db
```

## PostgreSQL

PostgreSQL should remain supported as an optional database backend.

Use PostgreSQL later for:

-   Production deployments
-   Higher concurrency
-   Larger datasets
-   Stronger database infrastructure
-   Multi-user deployments
-   Advanced querying

The application must not fail simply because PostgreSQL is not
configured.

------------------------------------------------------------------------

# 16. Vector Database / RAG

Use **ChromaDB** as the default vector database.

ChromaDB should run locally and must not require a hosted vector
service.

Example:

``` text
data/
└── chroma/
```

The vector database contains:

-   Brand story
-   Brand voice
-   Visual identity
-   Product information
-   Product features
-   Product benefits
-   USPs
-   Use cases
-   Target audience
-   Positioning
-   Marketing claims
-   Do's
-   Don'ts
-   Historical marketing information when available

------------------------------------------------------------------------

# 17. Knowledge Base Lifecycle

Product and brand analysis should **not run on every monthly calendar
generation**.

The product/brand knowledge ingestion process is a one-time or manually
triggered process.

## Initial setup

``` text
Brand/Product Information
        ↓
Knowledge Ingestion
        ↓
LLM analysis
        ↓
Structured knowledge
        ↓
ChromaDB
```

The system stores:

-   Features
-   Benefits
-   USPs
-   Differentiators
-   Problems solved
-   Use cases
-   Marketing angles
-   Brand rules
-   Product facts

## Later updates

When the user adds or changes a product:

``` text
User adds product
        ↓
Update Knowledge Base
        ↓
Re-analyze affected knowledge
        ↓
Update ChromaDB
        ↓
Future plans use updated knowledge
```

This process is manually triggered.

Do not run the full product analyst pipeline every time the user creates
a monthly calendar.

------------------------------------------------------------------------

# 18. RAG Usage

RAG is a supporting knowledge mechanism, not the primary user
experience.

The old system was effectively report/RAG-first.

The new direction is:

``` text
                 ┌──────────────────────┐
                 │ Brand Knowledge Base │
                 │      ChromaDB        │
                 └──────────┬───────────┘
                            │
                            ▼
                    Calendar Brain
                            │
                 ┌──────────┴──────────┐
                 ▼                     ▼
          Marketing Plan         Content Ideas
                 │                     │
                 └──────────┬──────────┘
                            ▼
                     Calendar UI
```

Agents retrieve only the information they need.

Example:

``` text
Calendar Planner
→ relevant products
→ audience
→ brand voice
→ marketing objectives
→ visual rules
→ previous content
```

The system must not pass the complete knowledge base to every LLM call.

------------------------------------------------------------------------

# 19. Knowledge Source Priority

The system should follow this priority:

``` text
1. Verified Brand Knowledge
2. Current User Input
3. External Research
4. Model Reasoning / Recommendation
```

External research must not overwrite confirmed product facts.

For example:

``` text
Brand Knowledge:
Product supports wireless charging.

External Source:
Competitor claims a different charging specification.

Result:
Do not change Qicdock's product specification.
```

------------------------------------------------------------------------

# 20. External Research

External research is optional and should be used where it materially
improves the plan.

Possible sources:

-   Web/search
-   Competitor websites
-   Instagram trends
-   YouTube
-   Industry information
-   Relevant social trends
-   Seasonal events
-   Market information

The planner should not search randomly.

Research should answer a specific planning question.

Examples:

``` text
What content formats are currently gaining attention
for this audience?

Is this event relevant to the target market?

What are competitors talking about?

What content gap exists?

Is there a relevant seasonal opportunity?
```

------------------------------------------------------------------------

# 21. Agent Architecture

The previous report-centric 11-agent architecture is replaced by a
calendar-centric workflow.

Recommended components:

1.  **Marketing Manager / Calendar Orchestrator**
2.  **Knowledge Retrieval Layer**
3.  **Market & Audience Research Agent**
4.  **Calendar Planning Agent**
5.  **Content Recommendation Agent**
6.  **Platform Adaptation Agent**
7.  **Visual Prompt Agent**
8.  **Brand Reviewer**
9.  **Queue/Worker**
10. **Image Generation Controller**

Not every component needs to be a separate LLM call.

The system should avoid unnecessary agent calls.

The key principle is:

> Use an agent when specialized reasoning is valuable, not simply
> because the architecture can contain more agents.

------------------------------------------------------------------------

# 22. Marketing Manager / Calendar Orchestrator

## Role

Coordinates the complete monthly planning workflow.

## Responsibilities

-   Validate the request
-   Load brand context
-   Determine required research
-   Start market research if required
-   Call the calendar planner
-   Persist the plan
-   Queue content-generation work
-   Monitor jobs
-   Preserve partial results
-   Handle failures
-   Trigger review
-   Update calendar status

The orchestrator should not generate every piece of content itself.

------------------------------------------------------------------------

# 23. Market & Audience Agent

## Role

Provide current marketing context when necessary.

## Responsibilities

-   Analyze audience needs
-   Analyze pain points
-   Identify relevant trends
-   Identify competitor patterns
-   Identify content gaps
-   Identify relevant opportunities
-   Assess whether an event/occasion is actually relevant

## Output

``` json
{
  "audience_segments": [],
  "pain_points": [],
  "needs": [],
  "motivations": [],
  "market_trends": [],
  "competitor_insights": [],
  "market_gaps": [],
  "opportunities": [],
  "sources": []
}
```

This agent should not modify verified brand facts.

------------------------------------------------------------------------

# 24. Calendar Planning Agent

## Role

This is the most important LLM component.

It decides the actual calendar.

It must reason over:

``` text
Date range
+
Brand knowledge
+
Products
+
Audience
+
Marketing objective
+
Market intelligence
+
Previous/planned content
+
Platform behavior
+
Content cadence
+
Occasions/events
```

Then produce a practical schedule.

The planner must be allowed to return fewer entries than the number of
days.

Example:

``` text
30-day period
→ 11 planned content entries
→ 19 empty days
```

That is a successful result if the strategy justifies it.

------------------------------------------------------------------------

# 25. Content Recommendation Agent

Once a calendar entry exists, this agent expands the recommendation.

It generates:

-   Hook
-   Concept
-   Messaging
-   Caption direction
-   CTA
-   Content structure
-   Audience angle
-   Product angle
-   Platform-specific recommendations
-   Visual direction
-   Image prompt

It should not automatically generate an image.

------------------------------------------------------------------------

# 26. Visual Prompt Agent

The visual agent is now a **prompt-generation component**, not an
automatic image-generation component.

Its responsibility is to generate:

``` text
Visual Concept
Image Prompt
Carousel Visual Directions
Shot/Scene Requirements
Product Representation Requirements
```

Example:

``` json
{
  "visual_concept": "...",
  "image_prompt": "...",
  "carousel_design": [],
  "visual_requirements": []
}
```

The image prompt should preserve critical product characteristics from
verified product knowledge.

------------------------------------------------------------------------

# 27. Image Generation Control

The image provider must **not automatically generate an image
immediately after the recommendation is created**.

Instead:

``` text
LLM Recommendation
        ↓
Image Prompt
        ↓
User sees prompt
        ↓
User clicks "Generate Image"
        ↓
Backend sends prompt to selected image provider
        ↓
Image returned
        ↓
Image displayed in calendar entry
```

This gives the user control over image-generation cost and timing.

The UI should expose:

``` text
Image Prompt

[ Generate Image ]
```

Optional future controls:

``` text
Provider
Model
Aspect Ratio
Number of Images
Quality
```

These controls must be optional and provider-specific.

------------------------------------------------------------------------

# 28. Image Generation States

Image generation should have independent status from the calendar
recommendation.

``` text
not_requested
queued
generating
ready
failed
```

Example:

``` json
{
  "image_status": "not_requested",
  "image_prompt": "...",
  "image_url": null
}
```

After clicking Generate Image:

``` json
{
  "image_status": "generating"
}
```

After success:

``` json
{
  "image_status": "ready",
  "image_url": "..."
}
```

A failed image generation must not delete the marketing recommendation.

------------------------------------------------------------------------

# 29. Brand Reviewer

Every generated recommendation should be checked before being marked
ready.

Review:

### Brand alignment

-   Brand voice
-   Positioning
-   Messaging

### Product accuracy

-   Features
-   Benefits
-   Specifications
-   Product claims

### Marketing quality

-   Relevance
-   Usefulness
-   Audience fit
-   CTA
-   Originality

### Calendar quality

-   Repetition
-   Excessive frequency
-   Platform fit
-   Sequence quality
-   Strategic relevance

### Occasion quality

-   Is the event actually relevant?
-   Is the connection natural?
-   Is the recommendation forced?

Output:

``` json
{
  "status": "approved",
  "score": 0.92,
  "issues": [],
  "corrections": []
}
```

If revision is required, only the affected entry should be regenerated.

------------------------------------------------------------------------

# 30. Review Retry Policy

Use a configurable retry limit.

Default:

``` text
MAX_REVIEW_RETRIES = 2
```

If an entry fails repeatedly:

``` text
Generated
   ↓
Reviewer
   ↓
Needs Revision
   ↓
Regenerate
   ↓
Reviewer
   ↓
Needs Revision
   ↓
Human Review
```

Do not create infinite loops.

------------------------------------------------------------------------

# 31. Partial Results Are Mandatory

The system must persist results immediately.

Bad behavior:

``` text
Generate 30 entries
      ↓
Entry 29 fails
      ↓
Return entire operation as failed
      ↓
User sees nothing
```

Required behavior:

``` text
Entry 1 → saved
Entry 2 → saved
Entry 3 → saved
...
Entry 28 → saved
Entry 29 → failed
Entry 30 → queued

User can still view entries 1–28.
```

The UI should display progress:

``` text
Monthly Plan
12 / 15 recommendations ready

██████████████░░░
```

------------------------------------------------------------------------

# 32. Queue Ordering

The queue should respect calendar sequence.

Example:

``` text
Plan:
September 4
September 8
September 13
September 18
September 23

Queue:
1 → September 4
2 → September 8
3 → September 13
4 → September 18
5 → September 23
```

Do not require all jobs to complete before showing the first result.

If the API limit occurs at job 3:

``` text
September 4 → Ready
September 8 → Ready
September 13 → Waiting / Retry
September 18 → Queued
September 23 → Queued
```

The already completed entries remain available.

------------------------------------------------------------------------

# 33. Avoiding `org_id` / `day_id` Errors

The previous implementation experienced errors around identifiers such
as organization IDs and day IDs.

The new design must simplify identity handling.

## User-facing identity

Use:

``` text
project
plan
date
```

A calendar entry is logically identified by:

``` text
plan_id + date + platform
```

If the database requires an internal primary key, generate it
internally.

The LLM must never be responsible for generating database IDs.

Do not ask the model to produce:

``` text
org_id
day_id
UUID
database primary key
```

The backend/database owns these values.

------------------------------------------------------------------------

# 34. Recommended Database Schema

## projects

``` text
id
name
created_at
updated_at
```

## brand_knowledge_versions

``` text
id
project_id
version
status
created_at
updated_at
```

## marketing_plans

``` text
id
project_id
start_date
end_date
objective
status
strategy_summary
created_at
updated_at
```

## calendar_entries

``` text
id
plan_id
date
platform
content_type
status
title
objective
content_pillar
product
audience
hook
concept
caption_direction
cta
visual_direction
image_prompt
reason
sequence_position
campaign_thread
review_status
error
created_at
updated_at
```

Recommended uniqueness:

``` text
(plan_id, date, platform)
```

This avoids duplicate entries without exposing internal IDs to the LLM.

## generation_jobs

``` text
id
plan_id
calendar_entry_id
job_type
status
attempts
payload
result
error
created_at
updated_at
```

Possible `job_type`:

``` text
calendar_plan
content_recommendation
review
image_generation
```

------------------------------------------------------------------------

# 35. No Redis Dependency

The application must run locally without Redis.

Required local stack:

``` text
Frontend
Backend
SQLite
ChromaDB
LLM API
```

Optional:

``` text
PostgreSQL
Redis
External queue
```

The README and setup instructions must make the default local path the
easiest path.

Do not require the developer to install PostgreSQL and Redis just to
test the calendar.

------------------------------------------------------------------------

# 36. Configuration

The system should use environment variables for external providers.

Example:

``` env
LLM_API_KEY=
LLM_MODEL=

IMAGE_PROVIDER_API_KEY=
IMAGE_MODEL=

DATABASE_URL=sqlite:///./data/qicdock.db

CHROMA_PERSIST_DIRECTORY=./data/chroma

REDIS_ENABLED=false
REDIS_URL=

POSTGRES_ENABLED=false
```

Secrets must never be hardcoded.

The application should have safe local defaults.

------------------------------------------------------------------------

# 37. Error Handling

Errors must be structured.

Example:

``` json
{
  "status": "error",
  "component": "calendar_planner",
  "error_code": "PROVIDER_RATE_LIMIT",
  "message": "The provider rate limit was reached.",
  "recoverable": true,
  "retry_after": null
}
```

Possible categories:

``` text
VALIDATION_ERROR
LLM_ERROR
RATE_LIMIT
TIMEOUT
RAG_ERROR
DATABASE_ERROR
IMAGE_PROVIDER_ERROR
REVIEW_ERROR
QUEUE_ERROR
```

The UI should show useful messages rather than raw stack traces.

------------------------------------------------------------------------

# 38. Provider Failure Behavior

If an LLM call fails:

``` text
Save current state
        ↓
Mark job failed/retryable
        ↓
Keep existing entries
        ↓
Continue other independent jobs where possible
```

If the image provider fails:

``` text
Recommendation remains Ready
Image remains Failed
User can retry Generate Image
```

The image provider must never control whether the calendar
recommendation survives.

------------------------------------------------------------------------

# 39. Frontend Requirements

The frontend should be calendar-first.

Recommended pages:

``` text
/
└── Marketing Calendar

/create-plan
└── Create Monthly Plan

/plan/:planId
└── Monthly Calendar

/plan/:planId/day/:date
└── Day Recommendation
```

Internal routes may use IDs, but the user does not manually enter them.

------------------------------------------------------------------------

# 40. Calendar UI Requirements

Each calendar cell should display:

``` text
Date

[Reel]
Title

Platform icon
Status
```

Example:

``` text
┌─────────────┐
│ 4           │
│             │
│ 🎬 REEL     │
│ Problem →   │
│ Solution    │
│             │
│ ✓ Ready     │
└─────────────┘
```

Empty days should remain visually clear:

``` text
┌─────────────┐
│ 6           │
│             │
│ No post     │
│ recommended│
└─────────────┘
```

------------------------------------------------------------------------

# 41. Recommendation Detail UI

Clicking a planned day should show:

``` text
Date
Platform
Content Type
Title
Objective
Audience
Product
Content Pillar
Reason
Hook
Concept
Caption Direction
CTA
Visual Direction
Image Prompt
Review Status
Generation Status
```

Actions:

``` text
[ Generate Image ]
[ Regenerate Recommendation ]
[ Edit ]
[ Save ]
```

If the entry is still generating:

``` text
Generating recommendation...

The calendar remains usable.
```

------------------------------------------------------------------------

# 42. Monthly Plan Summary

After the plan is generated, display:

``` text
September 2026

Total Days: 30
Recommended Posts: 10
Empty Days: 20

Instagram:
6 posts
2 reels
2 carousels
2 stories

LinkedIn:
4 posts

Objectives:
Awareness: 4
Engagement: 3
Consideration: 2
Conversion: 1
```

These numbers are examples only.

They must be calculated from actual generated recommendations.

------------------------------------------------------------------------

# 43. Calendar Quality Rules

The planner should enforce practical constraints through reasoning and
validation.

Examples:

-   Avoid excessive consecutive posting
-   Avoid repeating the same format too frequently
-   Avoid repeatedly promoting the same product
-   Maintain content-pillar diversity
-   Maintain platform-specific behavior
-   Avoid generic filler posts
-   Avoid forcing an event into the calendar
-   Avoid posting merely because a day is empty
-   Consider the relationship between adjacent posts
-   Leave intentional gaps
-   Prioritize strategically valuable posts

These should be configurable rather than hardcoded into an inflexible
rule engine.

The LLM should make the strategic decision; deterministic validation
should catch obvious violations.

------------------------------------------------------------------------

# 44. Content Diversity

The monthly planner should balance content across:

``` text
Education
Awareness
Problem/Solution
Product
Engagement
Storytelling
Social proof when verified
Community
Trend-based content when relevant
Promotion
Conversion
```

The system should not simply output:

``` text
Product post
Product post
Product post
Product post
```

------------------------------------------------------------------------

# 45. Hallucination Prevention

The system must never invent:

-   Product features
-   Product specifications
-   Pricing
-   Statistics
-   Testimonials
-   Customer results
-   Certifications
-   Performance claims
-   Competitor facts
-   Brand history

unless verified by the knowledge base or a trustworthy external source.

If information is unavailable:

``` text
Information unavailable
```

is preferable to fabrication.

------------------------------------------------------------------------

# 46. Source Attribution

Important recommendations should retain their origin.

Example:

``` json
{
  "insight": "...",
  "source_type": "brand_knowledge",
  "source": "product_knowledge",
  "confidence": 0.95
}
```

Possible source types:

``` text
brand_knowledge
external_research
agent_inference
user_input
recommendation
```

This metadata is useful for debugging and future explainability.

------------------------------------------------------------------------

# 47. State Model

Recommended application state:

``` python
MarketingState = {
    "project": {},
    "plan": {},
    "brand_context": {},
    "market_analysis": {},
    "calendar_strategy": {},
    "calendar_entries": [],
    "generation_jobs": [],
    "review_results": {},
    "image_jobs": [],
    "errors": [],
    "execution_metadata": {}
}
```

The state should be persisted where appropriate.

Do not place secrets inside shared LLM state.

------------------------------------------------------------------------

# 48. End-to-End Workflow

## Step 1 --- User opens dashboard

``` text
Marketing Calendar
```

## Step 2 --- User clicks Create Monthly Plan

``` text
Start Date
End Date
Platforms
Objective
Additional Instructions
```

## Step 3 --- Backend validates request

No `org_id` or `day_id` is required from the user.

## Step 4 --- Retrieve Brand Knowledge

Use ChromaDB.

``` text
Brand
Products
Audience
Voice
Visual Identity
Do's / Don'ts
```

## Step 5 --- Research when required

The Market & Audience Agent gathers relevant external intelligence.

## Step 6 --- Calendar Brain plans the month

It decides:

``` text
Which days deserve content?
Which days should remain empty?
Which platform?
Which format?
Which product?
Which objective?
Which sequence?
Why?
```

## Step 7 --- Persist the calendar immediately

Calendar entries are saved one by one.

## Step 8 --- Queue detailed recommendation generation

Each planned entry becomes a job.

## Step 9 --- Process queue sequentially or with controlled concurrency

``` text
Entry 1
 ↓
Entry 2
 ↓
Entry 3
...
```

or controlled parallelism when safe.

## Step 10 --- Save each completed result

The calendar updates in real time.

## Step 11 --- Brand Reviewer checks the recommendation

Approved → ready.

Needs revision → regenerate only that entry.

## Step 12 --- User clicks a calendar day

The recommendation is displayed.

## Step 13 --- User clicks Generate Image

Only now is the image API called.

## Step 14 --- Image result is saved

The calendar entry now contains the generated image.

------------------------------------------------------------------------

# 49. Example Monthly Planning Reasoning

Given:

``` text
Month: September
Platform: Instagram + LinkedIn
Goal: Increase awareness and engagement
```

The system might reason:

``` text
Week 1:
Introduce problem and brand value.

Week 2:
Show product solution.

Week 3:
Educational / audience value.

Week 4:
Engagement + conversion.
```

The final calendar might contain:

``` text
Sep 2  → Instagram Reel
Sep 5  → LinkedIn Educational Post
Sep 8  → Instagram Carousel
Sep 12 → Instagram Story Sequence
Sep 15 → LinkedIn Brand Insight
Sep 18 → Instagram Product Demonstration
Sep 22 → LinkedIn Problem/Solution
Sep 25 → Instagram Engagement Post
Sep 28 → Instagram Reel
Sep 30 → LinkedIn Conversion-oriented post
```

All other days may remain empty.

This is an example of output structure, not a hardcoded schedule.

------------------------------------------------------------------------

# 50. Important: Do Not Hardcode Marketing Decisions

The system must not contain rules such as:

``` python
if day == 1:
    create_post()

if festival:
    create_festival_post()

if sunday:
    create_story()

for every_day in month:
    generate_content()
```

These decisions belong to the marketing brain.

Deterministic code should handle:

-   Date validation
-   Persistence
-   Queueing
-   Status
-   Deduplication
-   Retry limits
-   Provider calls
-   UI rendering
-   Database constraints

LLM reasoning should handle:

-   Strategic cadence
-   Content selection
-   Format selection
-   Platform choice
-   Occasion relevance
-   Audience angle
-   Product angle
-   Sequence
-   Rationale

------------------------------------------------------------------------

# 51. Separation of Planning and Generation

This separation is critical.

## Planning

``` text
What should happen?
When should it happen?
Why?
```

## Recommendation Generation

``` text
How should this specific post be executed?
```

## Image Generation

``` text
Create the actual visual only when the user asks.
```

The system must not automatically jump from:

``` text
Calendar
→ image generation
```

without user control.

------------------------------------------------------------------------

# 52. Production Upgrade Path

The initial system must work locally with minimal configuration.

### Phase 1 --- Local

``` text
Frontend
FastAPI
SQLite
ChromaDB
LLM API
Local queue
```

### Phase 2 --- Production

``` text
Frontend
FastAPI
PostgreSQL
ChromaDB or hosted vector DB
Redis
Dedicated workers
Object storage
Monitoring
```

The architecture should allow these upgrades without rewriting the
business logic.

------------------------------------------------------------------------

# 53. Optional PostgreSQL Compatibility

The repository may support:

``` env
DATABASE_URL=sqlite:///./data/qicdock.db
```

for local development.

Production can use:

``` env
DATABASE_URL=postgresql://...
```

The application should use an abstraction/ORM so business logic does not
depend directly on SQLite-specific SQL.

------------------------------------------------------------------------

# 54. Optional Redis Compatibility

Redis should be an optional infrastructure adapter.

Example:

``` text
Queue interface
      │
      ├── LocalDatabaseQueue
      │
      └── RedisQueue
```

Default:

``` text
LocalDatabaseQueue
```

Future production:

``` text
RedisQueue
```

The calendar planner and content-generation logic should not care which
queue implementation is active.

------------------------------------------------------------------------

# 55. API Design

Recommended endpoints:

## Create Plan

``` http
POST /api/plans
```

Request:

``` json
{
  "start_date": "2026-09-01",
  "end_date": "2026-09-30",
  "platforms": ["instagram", "linkedin"],
  "objective": "Increase awareness"
}
```

Response:

``` json
{
  "plan_id": "...",
  "status": "generating"
}
```

## Get Plan

``` http
GET /api/plans/{plan_id}
```

## Get Calendar

``` http
GET /api/plans/{plan_id}/calendar
```

## Get Day Recommendation

``` http
GET /api/plans/{plan_id}/entries/{date}
```

## Regenerate Recommendation

``` http
POST /api/plans/{plan_id}/entries/{date}/regenerate
```

## Generate Image

``` http
POST /api/plans/{plan_id}/entries/{date}/image
```

## Update Knowledge Base

``` http
POST /api/knowledge/update
```

These routes are examples. Internal identifiers may be used by the
backend, but users should not manually manage them.

------------------------------------------------------------------------

# 56. Image Provider Interface

The image-generation layer should use a provider abstraction.

Example:

``` python
class ImageProvider:
    def generate(self, prompt: str, **options):
        ...
```

Possible future providers:

``` text
Provider A
Provider B
Provider C
```

The marketing system should only provide:

``` text
Prompt
Aspect Ratio
Optional model
Optional generation settings
```

The provider implementation handles the actual API call.

------------------------------------------------------------------------

# 57. LLM Provider Interface

Similarly, the LLM should be abstracted.

``` python
class LLMProvider:
    def generate(self, prompt, schema=None):
        ...
```

This makes it possible to change providers without rewriting the
planner.

Structured output should be preferred for:

-   Calendar entries
-   Recommendations
-   Reviews
-   Errors
-   Job results

------------------------------------------------------------------------

# 58. Observability

The system should log:

-   Plan creation
-   Planner execution
-   RAG retrieval
-   External research
-   Recommendation generation
-   Review result
-   Queue state
-   API failures
-   Retry attempts
-   Image generation
-   Completion time

Do not log API secrets or sensitive credentials.

Example execution log:

``` text
17:30:02 PLAN_CREATED
17:30:03 BRAND_CONTEXT_RETRIEVED
17:30:06 MARKET_RESEARCH_COMPLETE
17:30:10 CALENDAR_PLAN_CREATED
17:30:11 ENTRY_2026-09-04_QUEUED
17:30:14 ENTRY_2026-09-04_READY
17:30:15 ENTRY_2026-09-08_QUEUED
```

------------------------------------------------------------------------

# 59. Definition of Done

The new system is considered successfully implemented when:

-   [ ] Application starts locally without PostgreSQL
-   [ ] Application starts locally without Redis
-   [ ] SQLite works as the default database
-   [ ] ChromaDB works locally
-   [ ] Brand knowledge can be ingested manually
-   [ ] Product knowledge can be updated manually
-   [ ] Calendar is the primary UI
-   [ ] Create Monthly Plan button exists
-   [ ] Start/end dates can be selected
-   [ ] Instagram is supported
-   [ ] LinkedIn is supported
-   [ ] LLM decides posting dates
-   [ ] LLM can intentionally leave days empty
-   [ ] LLM decides content format
-   [ ] LLM considers sequencing
-   [ ] Festival/occasion relevance is reasoned about
-   [ ] Content is not generated for every day automatically
-   [ ] Calendar entries are persisted incrementally
-   [ ] Queue supports partial completion
-   [ ] Successful entries remain visible after later failures
-   [ ] Rate-limit failures do not destroy successful results
-   [ ] `org_id` is not required from the user
-   [ ] `day_id` is not required from the LLM
-   [ ] Database IDs are generated internally
-   [ ] Clicking a day opens its recommendation
-   [ ] Empty days show a meaningful explanation
-   [ ] Detailed recommendations are generated after planning
-   [ ] Brand review is performed
-   [ ] Failed recommendations can be retried individually
-   [ ] Image prompt is generated as part of the recommendation
-   [ ] Image generation is NOT automatic
-   [ ] User can explicitly click Generate Image
-   [ ] Image generation has its own queue/status
-   [ ] Image failure does not remove the recommendation
-   [ ] PostgreSQL can be added later
-   [ ] Redis can be added later
-   [ ] External providers use environment variables
-   [ ] Errors are structured and user-readable
-   [ ] Execution is observable

------------------------------------------------------------------------

# 60. Final Architecture

The intended architecture is:

``` text
                         ┌───────────────────────┐
                         │       Calendar UI     │
                         │                       │
                         │ Create Monthly Plan   │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │ Calendar Orchestrator │
                         └───────────┬───────────┘
                                     │
                ┌────────────────────┼────────────────────┐
                │                    │                    │
                ▼                    ▼                    ▼
       ┌────────────────┐   ┌─────────────────┐  ┌───────────────┐
       │   ChromaDB     │   │ Market/Audience │  │ Existing Plan │
       │ Brand Knowledge│   │     Research    │  │   History     │
       └───────┬────────┘   └────────┬────────┘  └───────┬───────┘
               │                     │                   │
               └─────────────────────┼───────────────────┘
                                     ▼
                         ┌───────────────────────┐
                         │   Calendar Brain LLM  │
                         │                       │
                         │ When?                 │
                         │ What?                 │
                         │ Which platform?       │
                         │ Which format?         │
                         │ Why?                  │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │   Persist Calendar    │
                         │       Entries         │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │    Local Job Queue    │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │ Content Recommendation│
                         │        Agent          │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │    Brand Reviewer     │
                         └───────────┬───────────┘
                                     │
                           ┌─────────┴─────────┐
                           ▼                   ▼
                       Approved           Revision
                           │                   │
                           │                   └──► Regenerate
                           ▼
                         Calendar
                           │
                           ▼
                   User clicks day
                           │
                           ▼
                    Recommendation
                           │
                           ▼
                    Image Prompt
                           │
                     User clicks
                  "Generate Image"
                           │
                           ▼
                 ┌──────────────────┐
                 │ Image Provider   │
                 └────────┬─────────┘
                          │
                          ▼
                     Generated Image
```

------------------------------------------------------------------------

# 61. Core System Objective

The final product should feel like:

> **An AI marketing strategist that plans a realistic month on a
> calendar and helps the user execute each selected piece of content.**

It should **not** feel like:

-   A generic chatbot
-   A daily-post generator
-   A static hardcoded calendar
-   A RAG demo
-   An automatic image-generation pipeline
-   A system that requires PostgreSQL and Redis before it can run

The desired lifecycle is:

``` text
UNDERSTAND
    ↓
RETRIEVE
    ↓
RESEARCH WHEN NEEDED
    ↓
THINK
    ↓
PLAN THE MONTH
    ↓
CHOOSE ONLY VALUABLE DATES
    ↓
SEQUENCE CONTENT
    ↓
SHOW CALENDAR
    ↓
GENERATE RECOMMENDATIONS
    ↓
REVIEW
    ↓
SAVE PARTIAL RESULTS
    ↓
USER SELECTS VISUAL
    ↓
GENERATE IMAGE ON DEMAND
```

The system's central intelligence is the **Calendar Brain**.

The Brand Knowledge Base provides verified brand truth.

External research provides current market intelligence.

The queue provides reliable incremental execution.

The calendar provides the primary user experience.

The user controls expensive image generation.

The backend owns identifiers and infrastructure details.

The entire system must remain functional locally first, while
PostgreSQL, Redis, dedicated workers, and more advanced infrastructure
remain optional future upgrades.
