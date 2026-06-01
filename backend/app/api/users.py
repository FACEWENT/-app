"""
用户相关 API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.core.response import success
from app.services.user import login_or_register, get_user_profile, update_user_profile

router = APIRouter(prefix="/api/v1/users", tags=["users"])


class LoginRequest(BaseModel):
    openid: str
    unionid: str = ""
    nickname: str = ""
    avatar_url: str = ""


class ProfileUpdateRequest(BaseModel):
    exam_year: Optional[int] = None
    target_degree_type: Optional[str] = None
    target_study_mode: Optional[str] = None
    target_major_code: Optional[str] = None
    target_major_name: Optional[str] = None
    score_total: Optional[int] = None
    politics_score: Optional[int] = None
    english_score: Optional[int] = None
    subject_one_score: Optional[int] = None
    subject_two_score: Optional[int] = None
    undergraduate_school: Optional[str] = None
    undergraduate_major: Optional[str] = None
    preferred_provinces: Optional[list[str]] = None
    preferred_cities: Optional[list[str]] = None
    preferred_school_levels: Optional[list[str]] = None
    risk_preference: Optional[str] = None
    notes: Optional[str] = None


@router.post("/login")
def login(payload: LoginRequest):
    """微信登录，不存在则自动注册"""
    user = login_or_register(
        openid=payload.openid,
        unionid=payload.unionid,
        nickname=payload.nickname,
        avatar_url=payload.avatar_url,
    )
    return success(user)


@router.get("/{user_id}/profile")
def get_profile(user_id: str):
    """获取用户画像"""
    profile = get_user_profile(user_id)
    if not profile:
        return success({"user_id": user_id, "message": "profile not set"})
    return success(profile)


@router.put("/{user_id}/profile")
def update_profile(user_id: str, payload: ProfileUpdateRequest):
    """更新用户画像"""
    profile = update_user_profile(user_id, payload.model_dump(exclude_none=True))
    return success(profile)
