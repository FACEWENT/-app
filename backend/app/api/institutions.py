from fastapi import APIRouter, HTTPException, Query

from app.core.response import success
from app.services.catalog import get_institution, get_institution_detail_with_history, list_institutions, build_filters

router = APIRouter(prefix="/api/v1/institutions", tags=["institutions"])


@router.get("/filters")
def get_filters():
    """获取筛选条件选项"""
    return success(build_filters())


@router.get("")
def institutions(
    keyword: str = "",
    province: str = "",
    city: str = "",
    school_level: str = "",
    school_type: str = "",
    discipline_code: str = "",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    return success(list_institutions(
        keyword=keyword,
        province=province,
        city=city,
        school_level=school_level,
        school_type=school_type,
        discipline_code=discipline_code,
        page=page,
        page_size=page_size,
    ))


@router.get("/{institution_id}")
def institution_detail(institution_id: str):
    item = get_institution(institution_id)
    if not item:
        raise HTTPException(status_code=404, detail="institution not found")
    return success(item)


@router.get("/{institution_id}/detail")
def institution_detail_with_history(institution_id: str):
    """获取院校详细信息，包括近三年招录数据、学费、参考书目等"""
    item = get_institution_detail_with_history(institution_id)
    if not item:
        raise HTTPException(status_code=404, detail="institution not found")
    return success(item)
