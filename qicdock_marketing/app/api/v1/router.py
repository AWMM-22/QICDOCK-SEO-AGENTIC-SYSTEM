from fastapi import APIRouter

from app.api.v1.endpoints import marketing, content, products, reports

api_router = APIRouter()

api_router.include_router(marketing.router, prefix="/marketing", tags=["marketing"])
api_router.include_router(content.router, prefix="/content", tags=["content"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])