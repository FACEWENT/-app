"""AI Agent 接口的请求/响应 Schema"""
from typing import Any, Literal

from pydantic import BaseModel, Field


class AgentChatRequest(BaseModel):
    """对话请求"""
    user_id: int | None = Field(default=None, description="用户ID，可选；登录后传")
    session_id: int | None = Field(default=None, description="会话ID；不传将自动创建")
    message: str = Field(min_length=1, max_length=2000, description="用户消息")
    scene_type: Literal[
        "qa", "school_selection", "school_compare",
        "score_analysis", "retest_consulting"
    ] = "school_selection"


class AgentChatResponse(BaseModel):
    session_id: int
    role: str = "assistant"
    content: str
    message_type: str = "text"
    structured_payload: dict[str, Any] | None = None
    tool_invocations: list[str] = []


class CreateSessionRequest(BaseModel):
    user_id: int
    scene_type: Literal[
        "qa", "school_selection", "school_compare",
        "score_analysis", "retest_consulting"
    ] = "school_selection"
    title: str | None = None
    input_snapshot: dict[str, Any] | None = None


class SessionTitleUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
