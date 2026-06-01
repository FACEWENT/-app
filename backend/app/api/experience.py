"""
经验分享API路由
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from app.core.response import success
from app.services.experience import (
    create_note,
    get_note_list,
    get_note_detail,
    toggle_note_like,
    toggle_note_collect,
    add_note_comment,
    get_note_comments
)

router = APIRouter(prefix="/api/v1/experience", tags=["experience"])


class CreateNoteRequest(BaseModel):
    user_id: int
    title: str
    content: str
    category: Optional[str] = None
    tags: Optional[list] = None
    images: Optional[list] = None


class AddCommentRequest(BaseModel):
    user_id: int
    content: str
    parent_id: Optional[int] = None


class LikeRequest(BaseModel):
    user_id: int


@router.post("/notes")
def create_note_api(req: CreateNoteRequest):
    """发布经验笔记"""
    note_id = create_note(
        user_id=req.user_id,
        title=req.title,
        content=req.content,
        category=req.category,
        tags=req.tags,
        images=req.images
    )
    return success({'note_id': note_id})


@router.get("/notes")
def list_notes(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    category: str = Query(default=None),
    sort_by: str = Query(default='newest'),
    user_id: int = Query(default=None)
):
    """获取笔记列表"""
    result = get_note_list(
        page=page,
        page_size=page_size,
        category=category,
        sort_by=sort_by,
        user_id=user_id
    )
    return success(result)


@router.get("/notes/{note_id}")
def note_detail(note_id: int, user_id: int = Query(default=None)):
    """获取笔记详情"""
    note = get_note_detail(note_id, user_id)
    if not note:
        raise HTTPException(status_code=404, detail="note not found")
    return success(note)


@router.post("/notes/{note_id}/like")
def like_note(note_id: int, req: LikeRequest):
    """点赞/取消点赞笔记"""
    is_liked = toggle_note_like(note_id, req.user_id)
    return success({'is_liked': is_liked})


@router.post("/notes/{note_id}/collect")
def collect_note(note_id: int, req: LikeRequest):
    """收藏/取消收藏笔记"""
    is_collected = toggle_note_collect(note_id, req.user_id)
    return success({'is_collected': is_collected})


@router.post("/notes/{note_id}/comments")
def add_comment(note_id: int, req: AddCommentRequest):
    """添加评论"""
    comment_id = add_note_comment(note_id, req.user_id, req.content, req.parent_id)
    return success({'comment_id': comment_id})


@router.get("/notes/{note_id}/comments")
def list_comments(
    note_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50)
):
    """获取笔记评论列表"""
    result = get_note_comments(note_id, page, page_size)
    return success(result)
