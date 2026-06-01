"""
社交功能API路由
"""
from fastapi import APIRouter, HTTPException, Query

from app.core.response import success
from app.services.social import (
    get_random_matches,
    accept_match,
    reject_match,
    block_user,
    get_chat_list,
    get_chat_messages,
    send_message,
    get_user_public_profile
)

router = APIRouter(prefix="/api/v1/social", tags=["social"])


@router.get("/matches/random")
def random_matches(
    user_id: int = Query(..., description="当前用户ID"),
    count: int = Query(default=5, ge=1, le=20, description="返回数量")
):
    """获取随机匹配的网友"""
    matches = get_random_matches(user_id, count)
    return success(matches)


@router.post("/matches/{matched_user_id}/accept")
def accept(user_id: int = Query(...), matched_user_id: int = ...):
    """接受匹配，创建聊天"""
    result = accept_match(user_id, matched_user_id)
    return success(result)


@router.post("/matches/{matched_user_id}/reject")
def reject(user_id: int = Query(...), matched_user_id: int = ...):
    """拒绝匹配"""
    reject_match(user_id, matched_user_id)
    return success({'status': 'rejected'})


@router.post("/blocks")
def block(
    user_id: int = Query(...),
    blocked_user_id: int = Query(...),
    reason: str = Query(default="")
):
    """屏蔽用户"""
    block_user(user_id, blocked_user_id, reason)
    return success({'status': 'blocked'})


@router.get("/chats")
def chats(user_id: int = Query(...)):
    """获取聊天列表"""
    chat_list = get_chat_list(user_id)
    return success(chat_list)


@router.get("/chats/{chat_id}/messages")
def chat_messages(
    chat_id: int,
    user_id: int = Query(...),
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0)
):
    """获取聊天消息"""
    result = get_chat_messages(chat_id, user_id, limit, offset)
    if 'error' in result:
        raise HTTPException(status_code=404, detail=result['error'])
    return success(result)


@router.post("/chats/{chat_id}/messages")
def send_msg(
    chat_id: int,
    user_id: int = Query(...),
    content: str = Query(...),
    message_type: str = Query(default='text')
):
    """发送消息"""
    result = send_message(chat_id, user_id, content, message_type)
    if 'error' in result:
        raise HTTPException(status_code=404, detail=result['error'])
    return success(result)


@router.get("/users/{user_id}/profile")
def user_profile(user_id: int, viewer_id: int = Query(...)):
    """获取用户公开画像"""
    profile = get_user_public_profile(user_id, viewer_id)
    if not profile:
        raise HTTPException(status_code=404, detail="user profile not found or hidden")
    return success(profile)
