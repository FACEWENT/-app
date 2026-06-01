from fastapi import APIRouter, HTTPException, Query

from app.core.response import success
from app.services.catalog import get_program, list_programs

router = APIRouter(prefix="/api/v1/programs", tags=["programs"])


@router.get("")
def programs(
    keyword: str = "",
    degree_type: str = "",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    return success(list_programs(keyword=keyword, degree_type=degree_type, page=page, page_size=page_size))


@router.get("/{program_id}")
def program_detail(program_id: str):
    item = get_program(program_id)
    if not item:
        raise HTTPException(status_code=404, detail="program not found")
    return success(item)
