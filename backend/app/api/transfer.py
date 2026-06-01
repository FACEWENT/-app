"""
考研调剂相关 API
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.core.response import success
from app.services.transfer import get_transfer_opportunities, get_transfer_guide

router = APIRouter(prefix="/api/v1/transfer", tags=["transfer"])


class TransferQueryRequest(BaseModel):
    score_total: int
    program_code: str
    degree_type: str = ""
    preferred_provinces: list[str] = []
    exclude_school_ids: list[str] = []


@router.post("/opportunities")
def query_opportunities(payload: TransferQueryRequest):
    """查询调剂机会"""
    return success(get_transfer_opportunities(
        score_total=payload.score_total,
        program_code=payload.program_code,
        degree_type=payload.degree_type,
        preferred_provinces=payload.preferred_provinces,
        exclude_school_ids=payload.exclude_school_ids,
    ))


@router.get("/guide")
def transfer_guide(program_code: str = ""):
    """获取调剂指南"""
    return success(get_transfer_guide(program_code))
