"""
浏览历史相关 API
"""
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional

from app.core.response import success
from app.services.browsing import add_browsing_history, get_browsing_history

router = APIRouter(prefix="/api/v1/browsing", tags=["browsing"])


class BrowsingHistoryRequest(BaseModel):
    user_id: str
    target_type: str  # school, major, enrollment_record, ai_session
    target_id: str
    source_page: str = ""
    duration_seconds: int = 0


@router.post("")
def add_history(payload: BrowsingHistoryRequest):
    """添加浏览历史"""
    if add_browsing_history(
        payload.user_id,
        payload.target_type,
        payload.target_id,
        payload.source_page,
        payload.duration_seconds,
    ):
        return success({"success": True})
    return success({"success": False})


@router.get("")
def get_history(
    user_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    """获取浏览历史"""
    return success(get_browsing_history(user_id, page, page_size))
