from fastapi import APIRouter

from app.core.response import success
from app.schemas.common import RecommendationRequest
from app.services.recommendation import generate_plan

router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])


@router.post("/plan")
def recommendation_plan(payload: RecommendationRequest):
    return success(generate_plan(payload.model_dump()))
