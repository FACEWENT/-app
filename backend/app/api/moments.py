"""
树洞瞬间API路由
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from app.core.response import success
from app.services.moments import (
    create_moment,
    get_moment_list,
    get_moment_detail,
    toggle_moment_like,
    add_moment_comment,
    get_moment_comments
)

router = APIRouter(prefix="/api/v1/moments", tags=["moments"])


class CreateMomentRequest(BaseModel):
    user_id: int
    content: str
    mood_tag: Optional[str] = None
    location_name: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    images: Optional[str] = None


class AddCommentRequest(BaseModel):
    user_id: int
    content: str


@router.post("")
def create_moment_api(req: CreateMomentRequest):
    """发布瞬间"""
    images_list = req.images.split(',') if req.images else None
    
    moment_id = create_moment(
        user_id=req.user_id,
        content=req.content,
        mood_tag=req.mood_tag,
        location_name=req.location_name,
        province=req.province,
        city=req.city,
        district=req.district,
        latitude=req.latitude,
        longitude=req.longitude,
        images=images_list
    )
    
    return success({'moment_id': moment_id})


@router.get("")
def list_moments(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    user_id: int = Query(default=None)
):
    """获取瞬间列表"""
    result = get_moment_list(
        page=page,
        page_size=page_size,
        user_id=user_id
    )
    return success(result)


@router.get("/{moment_id}")
def moment_detail(moment_id: int, user_id: int = Query(default=None)):
    """获取瞬间详情"""
    moment = get_moment_detail(moment_id, user_id)
    if not moment:
        raise HTTPException(status_code=404, detail="moment not found")
    return success(moment)


@router.post("/{moment_id}/like")
def like_moment(moment_id: int, user_id: int = Query(...)):
    """点赞/取消点赞瞬间"""
    is_liked = toggle_moment_like(moment_id, user_id)
    return success({'is_liked': is_liked})


@router.post("/{moment_id}/comments")
def add_comment(moment_id: int, req: AddCommentRequest):
    """添加评论"""
    comment_id = add_moment_comment(moment_id, req.user_id, req.content)
    return success({'comment_id': comment_id})


@router.get("/{moment_id}/comments")
def list_comments(
    moment_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50)
):
    """获取瞬间评论列表"""
    result = get_moment_comments(moment_id, page, page_size)
    return success(result)
