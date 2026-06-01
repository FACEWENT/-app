"""
灵魂匹配API路由
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from app.core.response import success
from app.services.soul_matching import (
    set_matching_preferences,
    get_matching_preferences,
    create_matching_order,
    pay_order,
    find_match,
    accept_match,
    reject_match,
    get_user_match_records,
    get_matching_questions
)

router = APIRouter(prefix="/api/v1/soul-matching", tags=["soul-matching"])


class PreferenceRequest(BaseModel):
    user_id: int
    gender_preference: Optional[str] = 'any'
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    exam_year: Optional[int] = None
    target_major: Optional[str] = None
    target_school_level: Optional[str] = None
    target_degree_type: Optional[str] = None
    study_style: Optional[str] = None
    personality_type: Optional[str] = None
    study_intensity: Optional[str] = None
    preferred_provinces: Optional[list] = None
    online_only: Optional[bool] = False


@router.get("/preferences")
def get_preferences(user_id: int = Query(...)):
    """获取用户匹配偏好"""
    pref = get_matching_preferences(user_id)
    return success(pref)


@router.post("/preferences")
def set_preferences(req: PreferenceRequest):
    """设置匹配偏好"""
    result = set_matching_preferences(
        user_id=req.user_id,
        gender_preference=req.gender_preference,
        age_min=req.age_min,
        age_max=req.age_max,
        exam_year=req.exam_year,
        target_major=req.target_major,
        target_school_level=req.target_school_level,
        target_degree_type=req.target_degree_type,
        study_style=req.study_style,
        personality_type=req.personality_type,
        study_intensity=req.study_intensity,
        preferred_provinces=req.preferred_provinces,
        online_only=req.online_only
    )
    return success(result)


@router.post("/orders")
def create_order(user_id: int = Query(...), price: float = Query(default=9.9)):
    """创建匹配订单"""
    order = create_matching_order(user_id, price)
    return success(order)


@router.post("/orders/{order_id}/pay")
def pay_matching_order(order_id: int, user_id: int = Query(...)):
    """支付订单"""
    try:
        order = pay_order(order_id, user_id)
        return success(order)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/match")
def execute_matching(order_id: int = Query(...), user_id: int = Query(...)):
    """执行匹配"""
    try:
        result = find_match(order_id, user_id)
        return success(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/records/{record_id}/accept")
def accept_matching_record(record_id: int, user_id: int = Query(...)):
    """接受匹配"""
    try:
        created_chat = accept_match(record_id, user_id)
        return success({'chat_created': created_chat})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/records/{record_id}/reject")
def reject_matching_record(record_id: int, user_id: int = Query(...)):
    """拒绝匹配"""
    try:
        reject_match(record_id, user_id)
        return success({'message': '已拒绝'})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/records")
def user_records(user_id: int = Query(...), page: int = Query(default=1, ge=1)):
    """获取用户匹配记录"""
    result = get_user_match_records(user_id, page)
    return success(result)


@router.get("/questions")
def get_questions(count: int = Query(default=8)):
    """获取匹配问题"""
    questions = get_matching_questions(count)
    return success(questions)
