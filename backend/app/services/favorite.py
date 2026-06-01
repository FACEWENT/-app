"""
收藏相关服务
"""
from app.core.db import fetch_all, fetch_one, get_connection


def add_favorite(user_id: str, favorite_type: str, target_id: str) -> bool:
    """添加收藏"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT IGNORE INTO user_favorites (user_id, favorite_type, target_id)
                VALUES (%s, %s, %s)
                """,
                (user_id, favorite_type, target_id)
            )
            return True
    except Exception:
        return False


def remove_favorite(user_id: str, favorite_type: str, target_id: str) -> bool:
    """取消收藏"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM user_favorites WHERE user_id = %s AND favorite_type = %s AND target_id = %s",
                (user_id, favorite_type, target_id)
            )
            return True
    except Exception:
        return False


def get_user_favorites(user_id: str, favorite_type: str = "") -> list[dict]:
    """获取用户收藏列表"""
    conditions = ["user_id = %s"]
    params: list = [user_id]

    if favorite_type:
        conditions.append("favorite_type = %s")
        params.append(favorite_type)

    query = f"""
        SELECT id, favorite_type, target_id, created_at
        FROM user_favorites
        WHERE {' AND '.join(conditions)}
        ORDER BY created_at DESC
    """
    return fetch_all(query, tuple(params))


def is_favorited(user_id: str, favorite_type: str, target_id: str) -> bool:
    """检查是否已收藏"""
    result = fetch_one(
        """
        SELECT id FROM user_favorites
        WHERE user_id = %s AND favorite_type = %s AND target_id = %s
        """,
        (user_id, favorite_type, target_id)
    )
    return result is not None
