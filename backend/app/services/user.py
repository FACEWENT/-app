"""
用户相关服务：登录、注册、画像
"""
import time
from datetime import datetime
from app.core.db import fetch_all, fetch_one, get_connection


def login_or_register(openid: str, unionid: str = "", nickname: str = "", avatar_url: str = "") -> dict:
    """微信登录，不存在则自动注册"""
    user = fetch_one(
        "SELECT id, openid, nickname, avatar_url, mobile, status, last_login_at FROM users WHERE openid = %s",
        (openid,)
    )

    if user:
        # 更新登录时间
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET last_login_at = NOW() WHERE id = %s", (user["id"],))
        return user

    # 新用户注册
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO users (openid, unionid, nickname, avatar_url, status, last_login_at)
            VALUES (%s, %s, %s, %s, 'active', NOW())
            """,
            (openid, unionid, nickname, avatar_url)
        )
        user_id = cursor.lastrowid

    return fetch_one(
        "SELECT id, openid, nickname, avatar_url, mobile, status, last_login_at FROM users WHERE id = %s",
        (user_id,)
    )


def get_user_profile(user_id: str) -> dict | None:
    """获取用户画像"""
    return fetch_one(
        """
        SELECT * FROM user_profiles WHERE user_id = %s
        """,
        (user_id,)
    )


def update_user_profile(user_id: str, profile_data: dict) -> dict:
    """更新用户画像"""
    # 检查是否已存在
    existing = fetch_one("SELECT id FROM user_profiles WHERE user_id = %s", (user_id,))

    allowed_fields = [
        "exam_year", "target_degree_type", "target_study_mode", "target_major_code",
        "target_major_name", "score_total", "politics_score", "english_score",
        "subject_one_score", "subject_two_score", "undergraduate_school",
        "undergraduate_major", "preferred_provinces", "preferred_cities",
        "preferred_school_levels", "risk_preference", "notes"
    ]

    # 过滤允许的字段
    updates = {k: v for k, v in profile_data.items() if k in allowed_fields and v is not None}

    if not updates:
        return get_user_profile(user_id) or {}

    if existing:
        # 更新
        set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
        values = list(updates.values()) + [user_id]
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE user_profiles SET {set_clause} WHERE user_id = %s", tuple(values))
    else:
        # 插入
        updates["user_id"] = user_id
        columns = ", ".join(updates.keys())
        placeholders = ", ".join(["%s"] * len(updates))
        values = list(updates.values())
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"INSERT INTO user_profiles ({columns}) VALUES ({placeholders})", tuple(values))

    return get_user_profile(user_id) or {}
