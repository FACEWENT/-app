"""考研AI Agent路由 - 智能择校 / 调剂 / 院校对比 / 数据问答"""
from fastapi import APIRouter, HTTPException, Query

from app.core.response import success
from app.schemas.ai_agent import (
    AgentChatRequest,
    AgentChatResponse,
    CreateSessionRequest,
    SessionTitleUpdate,
)
from app.schemas.common import AIInterpretRequest
from app.services.ai_agent import session as session_store
from app.services.ai_agent.agent import KaoyanAgent
from app.services.ai_agent.prompts import WELCOME_MESSAGE
from app.services.recommendation import interpret_question

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])


# ---------------------- 兼容老接口：本地正则解析 ----------------------

@router.post("/interpret")
def ai_interpret(payload: AIInterpretRequest):
    """轻量本地解析（不调用大模型），保留向后兼容。"""
    result = interpret_question(
        question=payload.question,
        score_total=payload.score_total,
        program_code=payload.program_code,
        preferred_provinces=payload.preferred_provinces,
    )
    return success(result)


# ---------------------- Agent 主入口 ----------------------

@router.get("/welcome")
def ai_welcome():
    """获取AI欢迎语"""
    return success({"message": WELCOME_MESSAGE})


@router.post("/agent/chat", response_model=None)
def agent_chat(payload: AgentChatRequest):
    """与考研AI Agent对话。会自动管理会话与持久化历史。"""
    session_id = payload.session_id

    # 自动创建会话
    if not session_id:
        if not payload.user_id:
            raise HTTPException(status_code=400, detail="未登录用户必须传入 session_id 或先创建会话")
        session_id = session_store.create_session(
            user_id=payload.user_id,
            scene_type=payload.scene_type,
        )

    # 校验会话归属
    sess = session_store.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="会话不存在")
    if payload.user_id and sess.get("user_id") and sess["user_id"] != payload.user_id:
        raise HTTPException(status_code=403, detail="无权访问该会话")

    agent = KaoyanAgent(user_id=payload.user_id, scene_type=payload.scene_type)
    reply = agent.chat(session_id, payload.message)

    return success({
        "session_id": session_id,
        **reply,
    })


# ---------------------- 会话管理 ----------------------

@router.post("/sessions")
def create_session(payload: CreateSessionRequest):
    sid = session_store.create_session(
        user_id=payload.user_id,
        scene_type=payload.scene_type,
        title=payload.title,
        input_snapshot=payload.input_snapshot,
    )
    sess = session_store.get_session(sid)
    return success(sess)


@router.get("/sessions")
def list_sessions(user_id: int = Query(...), limit: int = Query(30, le=100)):
    rows = session_store.list_sessions(user_id, limit=limit)
    return success({"count": len(rows), "sessions": rows})


@router.get("/sessions/{session_id}")
def session_detail(session_id: int, user_id: int | None = Query(default=None)):
    sess = session_store.get_session(session_id, user_id=user_id)
    if not sess:
        raise HTTPException(status_code=404, detail="会话不存在")
    messages = session_store.list_messages(session_id, limit=200)
    return success({"session": sess, "messages": messages})


@router.get("/sessions/{session_id}/messages")
def session_messages(session_id: int, limit: int = Query(50, le=200)):
    rows = session_store.list_messages(session_id, limit=limit)
    return success({"count": len(rows), "messages": rows})


@router.put("/sessions/{session_id}/title")
def update_title(session_id: int, payload: SessionTitleUpdate):
    session_store.update_session_title(session_id, payload.title)
    return success({"session_id": session_id, "title": payload.title})


@router.delete("/sessions/{session_id}")
def archive_session(session_id: int, user_id: int = Query(...)):
    affected = session_store.archive_session(session_id, user_id)
    if not affected:
        raise HTTPException(status_code=404, detail="会话不存在或无权操作")
    return success({"session_id": session_id, "status": "archived"})
