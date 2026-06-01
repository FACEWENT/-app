from fastapi import APIRouter, HTTPException, Query

from app.core.response import success
from app.services.catalog import get_offering, get_offering_score_lines, list_offerings

router = APIRouter(prefix="/api/v1/offerings", tags=["offerings"])


@router.get("")
def offerings(
    year: int | None = None,
    institution_id: str = "",
    program_id: str = "",
    keyword: str = "",
    province: str = "",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    return success(list_offerings(
        year=year,
        institution_id=institution_id,
        program_id=program_id,
        keyword=keyword,
        province=province,
        page=page,
        page_size=page_size,
    ))


@router.get("/{offering_id}")
def offering_detail(offering_id: str):
    item = get_offering(offering_id)
    if not item:
        raise HTTPException(status_code=404, detail="offering not found")
    return success(item)


@router.get("/{offering_id}/score-lines")
def offering_score_lines(offering_id: str):
    item = get_offering_score_lines(offering_id)
    if not item:
        raise HTTPException(status_code=404, detail="offering not found")
    return success(item)
