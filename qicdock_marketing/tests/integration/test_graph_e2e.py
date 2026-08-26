"""End-to-end graph execution test with mocked LLM provider.

Verifies: parallel research fan-out, parallel content fan-out, join merge,
brand review + revision routing, report generation, email status - without
needing API keys or a live database (persistence degrades gracefully).
"""
import pytest

from app.core.providers.llm.base import LLMProvider, LLMMessage, LLMResponse, LLMUsage


class FakeUsage(LLMUsage):
    pass


def _usage() -> LLMUsage:
    return LLMUsage(input_tokens=10, output_tokens=10, total_tokens=20, estimated_cost=0.0)


class FakeLLM(LLMProvider):
    @property
    def provider_name(self):
        return "fake"

    @property
    def default_model(self):
        return "fake-model"

    def estimate_cost(self, input_tokens, output_tokens):
        return 0.0

    async def generate(self, messages, model=None, temperature=0.7, max_tokens=4096, **kwargs):
        # Used by marketing_manager reasoning + report generator
        if any("Marketing Report Generator" in m.content for m in messages if m.role == "system"):
            return LLMResponse(
                content="<html><body><h1>Executive Summary</h1><p>Great campaign.</p></body></html>",
                usage=_usage(),
                model="fake-model",
                provider="fake",
            )
        return LLMResponse(content="plan reasoning", usage=_usage(), model="fake-model", provider="fake")

    async def generate_structured(self, messages, response_model, model=None, temperature=0.7, max_tokens=4096, **kwargs):
        name = response_model.__name__
        system = next((m.content for m in messages if m.role == "system"), "")

        if name == "ProductAnalysis":
            return response_model(main_usp="Custom-fit car dock", pain_point_solved="Cable clutter")
        if name == "ResearchData":
            if "Market Research Agent" in system:
                return response_model(trends=["Trend A"], consumer_insights=["Insight A"])
            return response_model()
        if name == "AudienceInsights":
            return response_model(audience="Drivers 25-45", pain_points=["Messy cables"])
        if name == "CompetitorInsights":
            return response_model(opportunities=["Car-console focus"], potential_hooks=["Hook X"])
        if name == "ContentStrategy":
            n = 3
            for m in messages:
                if m.role == "user" and "Quantity of items:" in m.content:
                    n = int(m.content.split("Quantity of items:")[1].split()[0])
            items = []
            formats = ["post", "reel", "story"]
            for i in range(n):
                fmt = formats[i % len(formats)]
                items.append({
                    "platform": "instagram",
                    "format": fmt,
                    "objective": "awareness",
                    "topic": f"Topic {i}",
                    "audience": "drivers",
                    "angle": f"angle {i}",
                    "hook": f"hook {i}",
                    "cta": "Shop now",
                    "priority": 1,
                    "reasoning": "because",
                    "hashtags": ["qicdock"],
                })
            return response_model(items=items, overall_theme="Clean car life")
        if name == "InstagramContentSet":
            return response_model(items=[{
                "hook": "h", "caption": "c", "cta": "Shop", "hashtags": ["q"],
                "visual_concept": "vc", "image_prompt": "ip",
            } for _ in range(_expected_count(messages))])
        if name == "ReelContentSet":
            count = _expected_count(messages)
            return response_model(items=[{
                "hook": "h", "duration": 15, "script": "s",
                "scenes": [{"duration": 3, "visual": "v", "voiceover": "vo", "text_overlay": "t"}],
                "caption": "c", "cta": "Shop", "hashtags": ["q"], "cover_image_prompt": "cip",
            } for _ in range(count)])
        if name == "StoryContentSet":
            count = _expected_count(messages)
            return response_model(items=[{
                "hook": "h",
                "frames": [{"frame_type": "question", "text": "Q?", "interactive_element": None}],
                "cta": "Shop", "caption": "c", "hashtags": ["q"], "cover_image_prompt": "cip",
            } for _ in range(count)])
        if name == "ReviewOutput":
            content_ids = _content_ids_from_prompt(messages)
            # Reject exactly one item on first pass to exercise the revision loop,
            # approve everything afterwards.
            verdicts = []
            for cid in content_ids:
                reject_this = cid == content_ids[0] and _review_pass["count"] == 0
                verdicts.append({
                    "content_id": cid,
                    "approved": not reject_this,
                    "score": 4.0 if reject_this else 8.5,
                    "issues": ["off-brand hook"] if reject_this else [],
                    "suggested_changes": ["soften hook"] if reject_this else [],
                })
            _review_pass["count"] += 1
            return response_model(verdicts=verdicts)
        raise AssertionError(f"Unexpected structured model requested: {name}")


_expected_count_cache = {}


def _expected_count(messages) -> int:
    for m in messages:
        if m.role == "user" and "Strategy items (" in m.content:
            try:
                return int(m.content.split("Strategy items (")[1].split(")")[0])
            except Exception:
                pass
    return 1


_content_ids_seen = []


def _content_ids_from_prompt(messages) -> list:
    import ast, re
    ids = []
    for m in messages:
        if m.role != "user":
            continue
        found = re.findall(r"'content_id': '([0-9a-f\-]{36})'", m.content)
        if found:
            return found
        found2 = re.findall(r'"content_id": "([0-9a-f\-]{36})"', m.content)
        if found2:
            return found2
    return ids


_review_pass = {"count": 0}


@pytest.fixture
def fake_llm(monkeypatch):
    _review_pass["count"] = 0
    monkeypatch.setattr(
        "app.core.providers.llm.factory.get_llm_provider", lambda: FakeLLM()
    )
    monkeypatch.setattr(
        "app.core.providers.search.factory.get_search_provider", lambda: None
    )
    monkeypatch.setattr(
        "app.core.providers.image.factory.get_image_provider", lambda: None
    )
    monkeypatch.setattr(
        "app.core.providers.email.factory.get_email_provider", lambda: None
    )
    return FakeLLM()


@pytest.mark.asyncio
async def test_full_workflow_runs_end_to_end(fake_llm, monkeypatch):
    from uuid import uuid4
    import app.agents.nodes.base as base_mod

    # Disable DB persistence gracefully (no postgres in unit env)
    async def _no_db(*args, **kwargs):
        raise RuntimeError("db disabled in test")

    monkeypatch.setattr(base_mod, "async_session_maker", _no_db, raising=False)

    org_id = uuid4()
    product_id = uuid4()

    from app.agents.state.marketing_state import (
        MarketingState,
        MarketingRequest,
        BrandContext,
        ProductContext,
    )
    from app.db.models.marketing import ContentType

    request = MarketingRequest(
        organization_id=org_id,
        product_ids=[product_id],
        goal="30 day instagram launch campaign",
        platforms=["instagram"],
        content_types=[ContentType.POST, ContentType.REEL, ContentType.STORY],
        quantity=3,
    )

    state = MarketingState(
        request=request,
        organization_id=org_id,
        product_ids=[product_id],
        brand_context=BrandContext(brand_voice="Friendly expert"),
        product_context=[
            ProductContext(product_id=product_id, name="QiDock Pro")
        ],
    )

    from app.graph.marketing_graph import marketing_graph

    final = await marketing_graph.ainvoke(state, config={"recursion_limit": 60})

    def _get(key, default=None):
        if isinstance(final, dict):
            return final.get(key, default)
        return getattr(final, key, default)

    report = _get("final_report")
    content = _get("generated_content")
    assert report and "<html>" in report
    assert content is not None and len(content.items) >= 1
    assert _get("generated_images") is not None
    assert _get("email_status") in {"sent", "failed", "skipped_no_recipient", "skipped_unconfigured"}
    assert _get("revision_count") >= 1  # reviewer rejected once -> revision ran
    assert len(_get("agent_runs")) >= 10
