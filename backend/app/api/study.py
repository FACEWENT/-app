"""
学习资料互助API路由
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from app.core.response import success
from app.services.study import (
    create_post,
    get_post_list,
    get_post_detail,
    toggle_like,
    search_suggestions
)

router = APIRouter(prefix="/api/v1/study", tags=["study"])


class CreateStudyPostRequest(BaseModel):
    user_id: int
    title: str
    content: str
    post_type: str
    price: Optional[float] = None
    original_price: Optional[float] = None
    condition_level: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    detail_address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    tags: Optional[str] = None
    category: Optional[str] = None
    trade_method: Optional[str] = 'both'
    contact_info: Optional[str] = None
    images: Optional[str] = None


@router.post("/posts")
def create_study_post(req: CreateStudyPostRequest):
    """发布学习资料帖子"""
    import json
    tags_list = json.loads(req.tags) if req.tags else None
    images_list = json.loads(req.images) if req.images else None
    
    post_id = create_post(
        user_id=req.user_id,
        title=req.title,
        content=req.content,
        post_type=req.post_type,
        price=req.price,
        original_price=req.original_price,
        condition_level=req.condition_level,
        province=req.province,
        city=req.city,
        detail_address=req.detail_address,
        latitude=req.latitude,
        longitude=req.longitude,
        tags=tags_list,
        category=req.category,
        trade_method=req.trade_method,
        contact_info=req.contact_info,
        images=images_list
    )
    
    return success({'post_id': post_id})


@router.get("/posts")
def list_posts(
    keyword: str = Query(default=""),
    post_type: str = Query(default=""),
    category: str = Query(default=""),
    province: str = Query(default=""),
    city: str = Query(default=""),
    min_price: float = Query(default=None),
    max_price: float = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50)
):
    """获取帖子列表"""
    result = get_post_list(
        keyword=keyword,
        post_type=post_type,
        category=category,
        province=province,
        city=city,
        min_price=min_price,
        max_price=max_price,
        page=page,
        page_size=page_size
    )
    return success(result)


class LikeRequest(BaseModel):
    user_id: int


@router.get("/posts/{post_id}")
def post_detail(post_id: int, user_id: int = Query(default=None)):
    """获取帖子详情"""
    post = get_post_detail(post_id, user_id)
    if not post:
        raise HTTPException(status_code=404, detail="post not found")
    return success(post)


@router.post("/posts/{post_id}/like")
def like_post(post_id: int, req: LikeRequest):
    """点赞/取消点赞"""
    is_liked = toggle_like(post_id, req.user_id)
    return success({'is_liked': is_liked})


@router.get("/search/suggestions")
def search(keyword: str = Query(...), limit: int = Query(default=10)):
    """搜索建议"""
    suggestions = search_suggestions(keyword, limit)
    return success(suggestions)
