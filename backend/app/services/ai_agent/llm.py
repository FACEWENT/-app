"""DashScope (qwen) LLM 客户端 - 支持 Function Calling"""
import json
import logging
import os
from typing import Any

import dashscope
from dashscope import Generation
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_MODEL = os.getenv("DASHSCOPE_MODEL", "qwen-plus")

if DASHSCOPE_API_KEY:
    dashscope.api_key = DASHSCOPE_API_KEY


class LLMError(Exception):
    """LLM 调用异常"""


def call_llm(messages: list[dict], tools: list[dict] | None = None,
             temperature: float = 0.5, model: str | None = None) -> dict:
    """
    调用 qwen 模型，支持 tool_calls。

    返回 dashscope choice 中的 message dict，结构形如：
    {
        "role": "assistant",
        "content": "...",
        "tool_calls": [{"id": "...", "type": "function", "function": {"name": "...", "arguments": "{...}"}}]
    }
    """
    if not DASHSCOPE_API_KEY:
        raise LLMError("缺少 DASHSCOPE_API_KEY，请在 .env 中配置")

    params: dict[str, Any] = {
        "model": model or DASHSCOPE_MODEL,
        "messages": messages,
        "result_format": "message",
        "temperature": temperature,
    }
    if tools:
        params["tools"] = tools

    try:
        response = Generation.call(**params)
    except Exception as exc:  # noqa: BLE001
        logger.exception("DashScope 调用异常")
        raise LLMError(f"调用大模型异常: {exc}") from exc

    if getattr(response, "status_code", 200) != 200:
        msg = getattr(response, "message", "unknown error")
        raise LLMError(f"DashScope 返回错误: {msg}")

    output = getattr(response, "output", None) or {}
    choices = output.get("choices") if isinstance(output, dict) else None
    if not choices:
        raise LLMError("LLM 无返回内容")

    return choices[0].get("message") or {}


def parse_tool_arguments(raw: Any) -> dict:
    """工具调用 arguments 通常是 JSON 字符串"""
    if isinstance(raw, dict):
        return raw
    if not raw:
        return {}
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}
    return {}
