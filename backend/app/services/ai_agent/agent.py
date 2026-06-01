"""KaoyanAgent - 考研AI Agent主逻辑（编排 LLM + 工具调用循环 + 会话持久化）"""
import json
import logging
from typing import Any

from app.services.ai_agent import session as session_store
from app.services.ai_agent.llm import LLMError, call_llm, parse_tool_arguments
from app.services.ai_agent.prompts import SYSTEM_PROMPT, build_user_profile_hint
from app.services.ai_agent.tools import TOOL_SCHEMAS, execute_tool, get_user_profile

logger = logging.getLogger(__name__)

MAX_TOOL_ITERATIONS = 5  # 防止死循环


class KaoyanAgent:
    """考研择校/调剂Agent"""

    def __init__(self, user_id: int | None = None, scene_type: str = "school_selection"):
        self.user_id = user_id
        self.scene_type = scene_type

    # ----------------- 主入口 -----------------

    def chat(self, session_id: int, user_message: str) -> dict:
        """处理一次用户消息，返回 assistant 回复。

        流程:
          1. 持久化用户消息
          2. 拼装 system + 用户画像 + 历史 + 当前消息
          3. 调用 LLM；若返回 tool_calls，执行工具并回送，循环直到出 content
          4. 持久化 assistant 回复，附结构化结果
        """
        session_store.add_message(session_id, "user", user_message, "text")

        messages = self._build_messages(session_id, user_message)

        structured_payloads: list[dict] = []
        message_type = "text"
        last_text = ""

        for iteration in range(MAX_TOOL_ITERATIONS):
            try:
                assistant_msg = call_llm(messages, tools=TOOL_SCHEMAS)
            except LLMError as exc:
                err = f"抱歉，AI服务暂时不可用：{exc}"
                session_store.add_message(session_id, "assistant", err, "text")
                return {"role": "assistant", "content": err, "error": True}

            tool_calls = assistant_msg.get("tool_calls") or []
            content = assistant_msg.get("content") or ""

            # 把当前 assistant turn 加入 messages（让模型理解工具调用历史）
            messages.append({
                "role": "assistant",
                "content": content,
                "tool_calls": tool_calls,
            })

            if not tool_calls:
                # 终态：模型给出最终回答
                last_text = content
                break

            # 执行所有工具调用
            for call in tool_calls:
                fn = (call.get("function") or {}) if isinstance(call, dict) else {}
                tool_name = fn.get("name", "")
                args = parse_tool_arguments(fn.get("arguments"))
                logger.info("Agent调用工具 %s(%s)", tool_name, args)

                result = execute_tool(
                    tool_name, args,
                    context={"user_id": self.user_id},
                )

                # 推荐/调剂结果作为结构化 payload
                if tool_name in ("recommend_schools", "analyze_transfer", "compare_schools"):
                    structured_payloads.append({"tool": tool_name, "data": result})
                    if tool_name == "recommend_schools":
                        message_type = "plan"
                    elif tool_name == "analyze_transfer":
                        message_type = "recommendation"

                # 将工具结果回送给模型
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.get("id"),
                    "name": tool_name,
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                })

        else:
            # 超过最大迭代次数仍未给出回答
            last_text = "抱歉，处理过程过长，请尝试更具体的问题。"

        if not last_text:
            last_text = "（无回复内容）"

        # 持久化 assistant 消息
        payload_to_save = structured_payloads[0] if structured_payloads else None
        session_store.add_message(
            session_id, "assistant", last_text,
            message_type=message_type,
            structured_payload=payload_to_save,
        )
        session_store.touch_session(session_id)

        return {
            "role": "assistant",
            "content": last_text,
            "message_type": message_type,
            "structured_payload": payload_to_save,
            "tool_invocations": [p["tool"] for p in structured_payloads],
        }

    # ----------------- 内部辅助 -----------------

    def _build_messages(self, session_id: int, user_message: str) -> list[dict]:
        """拼装发往 LLM 的 messages 列表"""
        system_content = SYSTEM_PROMPT
        if self.user_id:
            profile_resp = get_user_profile(self.user_id)
            profile = profile_resp.get("profile") if isinstance(profile_resp, dict) else None
            hint = build_user_profile_hint(profile or {})
            if hint:
                system_content = f"{SYSTEM_PROMPT}\n\n{hint}"

        msgs: list[dict] = [{"role": "system", "content": system_content}]

        # 取历史（不含本条 user_message —— 已在 add_message 之后）
        history = session_store.get_history_for_llm(session_id, max_pairs=8)
        # history 末尾应当是当前 user 消息，避免重复
        if history and history[-1].get("role") == "user" and history[-1].get("content") == user_message:
            msgs.extend(history)
        else:
            msgs.extend(history)
            msgs.append({"role": "user", "content": user_message})
        return msgs


# ===================== 函数式入口 =====================

def run_chat(user_id: int | None, session_id: int, user_message: str,
             scene_type: str = "school_selection") -> dict:
    agent = KaoyanAgent(user_id=user_id, scene_type=scene_type)
    return agent.chat(session_id, user_message)
