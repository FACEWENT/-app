"""
收藏相关 API
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.core.response import success
from app.services.favorite import add_favorite, remove_favorite, get_user_favorites, is_favorited

router = APIRouter(prefix="/api/v1/favorites", tags=["favorites"])


class FavoriteRequest(BaseModel):
    user_id: str
    favorite_type: str  # school, major, enrollment_record, plan
    target_id: str


@router.post("")
def add(payload: FavoriteRequest):
    """添加收藏"""
    if add_favorite(payload.user_id, payload.favorite_type, payload.target_id):
        return success({"favorited": True})
    raise HTTPException(status_code=500, detail="Failed to add favorite")


@router.delete("")
def remove(user_id: str, favorite_type: str, target_id: str):
    """取消收藏"""
    if remove_favorite(user_id, favorite_type, target_id):
        return success({"favorited": False})
    raise HTTPException(status_code=500, detail="Failed to remove favorite")


@router.get("")
def list_favorites(user_id: str, favorite_type: str = ""):
    """获取用户收藏列表"""
    items = get_user_favorites(user_id, favorite_type)
    return success(items)


@router.get("/check")
def check_favorited(user_id: str, favorite_type: str, target_id: str):
    """检查是否已收藏"""
    return success({"favorited": is_favorited(user_id, favorite_type, target_id)})
