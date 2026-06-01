import json
import os
from contextlib import contextmanager
from decimal import Decimal
from typing import Any

import pymysql
from pymysql.cursors import DictCursor
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


def _db_settings() -> dict[str, Any]:
    return {
        "host": os.getenv("DB_HOST", "127.0.0.1"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "kaoyan_system_v2"),
        "charset": "utf8mb4",
        "cursorclass": DictCursor,
        "autocommit": True,
    }


@contextmanager
def get_connection():
    connection = pymysql.connect(**_db_settings())
    try:
        yield connection
    finally:
        connection.close()


def _convert_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8")
    if isinstance(value, str):
        stripped = value.strip()
        if (stripped.startswith("{") and stripped.endswith("}")) or (
            stripped.startswith("[") and stripped.endswith("]")
        ):
            try:
                return json.loads(stripped)
            except json.JSONDecodeError:
                return value
    return value


def normalize_row(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {key: _convert_value(value) for key, value in row.items()}


def normalize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [normalize_row(row) for row in rows if row is not None]


def fetch_all(query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            return normalize_rows(cursor.fetchall())


def fetch_one(query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            return normalize_row(cursor.fetchone())


def execute(query: str, params: tuple[Any, ...] = ()) -> int:
    """执行INSERT/UPDATE/DELETE，返回lastrowid（INSERT时）或受影响行数"""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            affected = cursor.execute(query, params)
            return cursor.lastrowid or affected
