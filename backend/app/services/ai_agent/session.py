"""AI 会话持久化 - ai_sessions / ai_messages 表 CRUD"""
import json
from typing import Any

from app.core.db import execute, fetch_all, fetch_one


# ===================== Sessions =====================

def create_session(user_id: int, scene_type: str = "school_selection",
                    title: str | None = None,
                    input_snapshot: dict | None = None) -> int:
    """创建新会话，返回 session_id"""
    return execute(
        """INSERT INTO ai_sessions (user_id, session_title, scene_type, input_snapshot)
           VALUES (%s, %s, %s, %s)""",
        (
            user_id,
            title or _default_title(scene_type),
            scene_type,
            json.dumps(input_snapshot, ensure_ascii=False) if input_snapshot else None,
        ),
    )


def _default_title(scene_type: str) -> str:
    return {
        "qa": "考研问答",
        "school_selection": "智能择校",
        "school_compare": "院校对比",
        "score_analysis": "分数评估",
        "retest_consulting": "复试咨询",
    }.get(scene_type, "AI对话")


def get_session(session_id: int, user_id: int | None = None) -> dict | None:
    if user_id:
        return fetch_one(
            "SELECT * FROM ai_sessions WHERE id=%s AND user_id=%s",
            (session_id, user_id),
        )
    return fetch_one("SELECT * FROM ai_sessions WHERE id=%s", (session_id,))


def list_sessions(user_id: int, limit: int = 30) -> list[dict]:
    return fetch_all(
        """SELECT id, session_title, scene_type, summary, status,
                  created_at, updated_at
           FROM ai_sessions
           WHERE user_id=%s AND status='active'
           ORDER BY updated_at DESC
           LIMIT %s""",
        (user_id, limit),
    )


def update_session_title(session_id: int, title: str) -> None:
    execute(
        "UPDATE ai_sessions SET session_title=%s WHERE id=%s",
        (title, session_id),
    )


def archive_session(session_id: int, user_id: int) -> int:
    return execute(
        "UPDATE ai_sessions SET status='archived' WHERE id=%s AND user_id=%s",
        (session_id, user_id),
    )


def touch_session(session_id: int) -> None:
    execute(
        "UPDATE ai_sessions SET updated_at=CURRENT_TIMESTAMP WHERE id=%s",
        (session_id,),
    )


# ===================== Messages =====================

def add_message(session_id: int, role: str, content: str,
                message_type: str = "text",
                structured_payload: dict | list | None = None) -> int:
    """新增一条消息（user/assistant/system）"""
    return execute(
        """INSERT INTO ai_messages (session_id, role, message_type, content, structured_payload)
           VALUES (%s, %s, %s, %s, %s)""",
        (
            session_id,
            role,
            message_type,
            content or "",
            json.dumps(structured_payload, ensure_ascii=False) if structured_payload else None,
        ),
    )


def list_messages(session_id: int, limit: int = 50) -> list[dict]:
    rows = fetch_all(
        """SELECT id, role, message_type, content, structured_payload, created_at
           FROM ai_messages
           WHERE session_id=%s
           ORDER BY id ASC
           LIMIT %s""",
        (session_id, limit),
    )
    return rows


def get_history_for_llm(session_id: int, max_pairs: int = 10) -> list[dict]:
    """
    获取最近的对话历史，转换成 LLM messages 格式（仅 user/assistant 文本）
    用于多轮上下文。
    """
    rows = fetch_all(
        """SELECT role, content, message_type
           FROM ai_messages
           WHERE session_id=%s AND role IN ('user','assistant')
                 AND message_type IN ('text','plan','recommendation')
                 AND content IS NOT NULL AND content <> ''
           ORDER BY id DESC
           LIMIT %s""",
        (session_id, max_pairs * 2),
    )
    rows.reverse()
    return [{"role": r["role"], "content": r["content"]} for r in rows]


def update_session_summary(session_id: int, summary: str) -> None:
    execute(
        "UPDATE ai_sessions SET summary=%s WHERE id=%s",
        (summary, session_id),
    )
