from typing import Literal

from pydantic import BaseModel, Field


class PaginationQuery(BaseModel):
    page: int = 1
    page_size: int = 20


class RecommendationRequest(BaseModel):
    score_total: int = Field(ge=0, le=500)
    program_code: str
    preferred_provinces: list[str] = []
    school_levels: list[str] = []
    risk_preference: Literal["conservative", "balanced", "aggressive"] = "balanced"
    degree_type: str | None = None


class AIInterpretRequest(BaseModel):
    question: str
    score_total: int | None = None
    program_code: str | None = None
    preferred_provinces: list[str] = []
