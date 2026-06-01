"""
问题咨询与教学信息API路由
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from app.core.response import success
from app.services.tutoring import (
    set_user_target_school,
    get_user_target_school,
    create_tutoring_post,
    get_tutoring_posts,
    get_tutoring_post_detail,
    toggle_tutoring_like
)
import json

router = APIRouter(prefix="/api/v1/tutoring", tags=["tutoring"])


class SetTargetSchoolRequest(BaseModel):
    user_id: int
    school_id: int
    school_name: str
    exam_year: int
    major_id: Optional[int] = None
    major_code: Optional[str] = None
    major_name: Optional[str] = None


class CreateTutoringPostRequest(BaseModel):
    user_id: int
    school_id: int
    major_id: int
    subject_type: str
    subject_name: str
    title: str
    content: str
    price: float
    current_school: Optional[str] = None
    current_major: Optional[str] = None
    exam_score: Optional[int] = None
    subject_score: Optional[int] = None
    bio: Optional[str] = None
    teaching_mode: Optional[str] = 'online'
    contact_info: Optional[str] = None
    images: Optional[str] = None


@router.get("/target-school")
def get_target(user_id: int = Query(...)):
    """获取用户目标院校"""
    target = get_user_target_school(user_id)
    return success(target)


@router.post("/target-school")
def set_target(req: SetTargetSchoolRequest):
    """设置用户目标院校"""
    result = set_user_target_school(
        user_id=req.user_id,
        school_id=req.school_id,
        school_name=req.school_name,
        exam_year=req.exam_year,
        major_id=req.major_id,
        major_code=req.major_code,
        major_name=req.major_name
    )
    return success(result)


@router.post("/posts")
def create_post(req: CreateTutoringPostRequest):
    """发布教学信息"""
    images_list = json.loads(req.images) if req.images else None
    
    post_id = create_tutoring_post(
        user_id=req.user_id,
        school_id=req.school_id,
        major_id=req.major_id,
        subject_type=req.subject_type,
        subject_name=req.subject_name,
        title=req.title,
        content=req.content,
        price=req.price,
        current_school=req.current_school,
        current_major=req.current_major,
        exam_score=req.exam_score,
        subject_score=req.subject_score,
        bio=req.bio,
        teaching_mode=req.teaching_mode,
        contact_info=req.contact_info,
        images=images_list
    )
    
    return success({'post_id': post_id})


@router.get("/posts")
def list_posts(
    school_id: int = Query(...),
    major_id: int = Query(...),
    subject_type: str = Query(default=""),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50)
):
    """获取教学信息列表"""
    result = get_tutoring_posts(
        school_id=school_id,
        major_id=major_id,
        subject_type=subject_type,
        page=page,
        page_size=page_size
    )
    return success(result)


class LikeRequest(BaseModel):
    user_id: int


@router.get("/posts/{post_id}")
def post_detail(post_id: int, user_id: int = Query(default=None)):
    """获取教学帖子详情"""
    post = get_tutoring_post_detail(post_id, user_id)
    if not post:
        raise HTTPException(status_code=404, detail="post not found")
    return success(post)


@router.post("/posts/{post_id}/like")
def like_post(post_id: int, req: LikeRequest):
    """点赞教学帖子"""
    is_liked = toggle_tutoring_like(post_id, req.user_id)
    return success({'is_liked': is_liked})
