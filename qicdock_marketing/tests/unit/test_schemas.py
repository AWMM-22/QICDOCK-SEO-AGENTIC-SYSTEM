import pytest
from uuid import uuid4
from app.schemas.request.marketing import MarketingGenerateRequest
from app.db.models.marketing import ContentType


def test_marketing_generate_request_validation():
    org_id = uuid4()
    product_id = uuid4()

    request = MarketingGenerateRequest(
        organization_id=org_id,
        product_ids=[product_id],
        goal="Increase Instagram awareness for wireless charger",
        platforms=["instagram"],
        content_types=[ContentType.POST, ContentType.CAROUSEL],
        quantity=5,
        email="founder@qicdock.com",
    )

    assert request.organization_id == org_id
    assert request.product_ids == [product_id]
    assert request.goal == "Increase Instagram awareness for wireless charger"
    assert request.platforms == ["instagram"]
    assert request.content_types == [ContentType.POST, ContentType.CAROUSEL]
    assert request.quantity == 5
    assert request.email == "founder@qicdock.com"


def test_marketing_generate_request_defaults():
    org_id = uuid4()
    product_id = uuid4()

    request = MarketingGenerateRequest(
        organization_id=org_id,
        product_ids=[product_id],
        goal="Test marketing goal for validation",
    )

    assert request.platforms == []
    assert request.content_types == []
    assert request.quantity == 5
    assert request.email is None


def test_marketing_generate_request_quantity_validation():
    org_id = uuid4()
    product_id = uuid4()

    with pytest.raises(ValueError):
        MarketingGenerateRequest(
            organization_id=org_id,
            product_ids=[product_id],
            goal="Test marketing goal for validation",
            quantity=0,
        )

    with pytest.raises(ValueError):
        MarketingGenerateRequest(
            organization_id=org_id,
            product_ids=[product_id],
            goal="Test marketing goal for validation",
            quantity=21,
        )


def test_marketing_generate_request_product_ids_required():
    org_id = uuid4()

    with pytest.raises(ValueError):
        MarketingGenerateRequest(
            organization_id=org_id,
            product_ids=[],
            goal="Test marketing goal for validation",
        )