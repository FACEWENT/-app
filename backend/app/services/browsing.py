"""
浏览历史相关服务
"""
from app.core.db import fetch_all, fetch_one, get_connection


def add_browsing_history(
    user_id: str,
    target_type: str,
    target_id: str,
    source_page: str = "",
    duration_seconds: int = 0,
) -> bool:
    """添加浏览历史"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO user_browsing_history (user_id, target_type, target_id, source_page, duration_seconds)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user_id, target_type, target_id, source_page, duration_seconds)
            )
            return True
    except Exception:
        return False


def get_browsing_history(user_id: str, page: int = 1, page_size: int = 20) -> dict:
    """获取用户浏览历史"""
    offset = (page - 1) * page_size

    # 总数
    count_result = fetch_one(
        "SELECT COUNT(*) as total FROM user_browsing_history WHERE user_id = %s",
        (user_id,)
    )
    total = count_result["total"] if count_result else 0

    items = fetch_all(
        """
        SELECT id, target_type, target_id, source_page, duration_seconds, created_at
        FROM user_browsing_history
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """,
        (user_id, page_size, offset)
    )

    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
    }
