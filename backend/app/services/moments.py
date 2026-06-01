"""
树洞瞬间服务（类似Soul瞬间）
"""
from typing import Optional

from app.core.db import fetch_all, fetch_one, execute


# ========================================
# 瞬间管理
# ========================================

def create_moment(
    user_id: int,
    content: str,
    mood_tag: Optional[str] = None,
    location_name: Optional[str] = None,
    province: Optional[str] = None,
    city: Optional[str] = None,
    district: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    images: Optional[list] = None
) -> int:
    """创建瞬间"""
    moment_id = execute(
        """
        INSERT INTO user_moments (
            user_id, content, mood_tag, location_name, province, city, district,
            latitude, longitude
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (user_id, content, mood_tag, location_name, province, city, district,
         latitude, longitude)
    )
    
    # 保存图片
    if images:
        for idx, img_url in enumerate(images):
            execute(
                """
                INSERT INTO moment_images (moment_id, image_url, sort_order)
                VALUES (%s, %s, %s)
                """,
                (moment_id, img_url, idx)
            )
    
    return moment_id


def get_moment_list(
    page: int = 1,
    page_size: int = 20,
    user_id: Optional[int] = None
) -> dict:
    """获取瞬间列表（按时间倒序）"""
    offset = (page - 1) * page_size
    
    # 查总数
    total = fetch_one(
        "SELECT COUNT(*) as total FROM user_moments WHERE status = 'active'"
    )['total']
    
    # 分页查询
    query = """
        SELECT 
          um.*,
          u.nickname,
          u.avatar_url,
          (SELECT GROUP_CONCAT(image_url ORDER BY sort_order) 
           FROM moment_images WHERE moment_id = um.id) as images_str
        FROM user_moments um
        JOIN users u ON um.user_id = u.id
        WHERE um.status = 'active'
        ORDER BY um.created_at DESC
        LIMIT %s OFFSET %s
    """
    moments = fetch_all(query, (page_size, offset))
    
    # 处理图片和点赞状态
    for moment in moments:
        # 处理图片
        if moment.get('images_str'):
            moment['images'] = moment['images_str'].split(',')
        else:
            moment['images'] = []
        del moment['images_str']
        
        # 检查用户是否已点赞
        if user_id:
            like_record = fetch_one(
                "SELECT id FROM moment_likes WHERE moment_id = %s AND user_id = %s",
                (moment['id'], user_id)
            )
            moment['is_liked'] = like_record is not None
        else:
            moment['is_liked'] = False
        
        # 格式化时间
        moment['created_at_str'] = format_time(moment['created_at'])
    
    return {
        'items': moments,
        'page': page,
        'page_size': page_size,
        'total': total
    }


def get_moment_detail(moment_id: int, user_id: Optional[int] = None) -> Optional[dict]:
    """获取瞬间详情"""
    # 增加浏览
    execute(
        "UPDATE user_moments SET view_count = view_count + 1 WHERE id = %s",
        (moment_id,)
    )
    
    moment = fetch_one(
        """
        SELECT 
          um.*,
          u.nickname,
          u.avatar_url
        FROM user_moments um
        JOIN users u ON um.user_id = u.id
        WHERE um.id = %s AND um.status = 'active'
        """,
        (moment_id,)
    )
    
    if not moment:
        return None
    
    # 获取图片
    images = fetch_all(
        "SELECT image_url FROM moment_images WHERE moment_id = %s ORDER BY sort_order",
        (moment_id,)
    )
    moment['images'] = [img['image_url'] for img in images]
    
    # 检查点赞状态
    if user_id:
        like_record = fetch_one(
            "SELECT id FROM moment_likes WHERE moment_id = %s AND user_id = %s",
            (moment_id, user_id)
        )
        moment['is_liked'] = like_record is not None
    else:
        moment['is_liked'] = False
    
    # 获取评论
    moment['comments'] = fetch_all(
        """
        SELECT mc.*, u.nickname, u.avatar_url
        FROM moment_comments mc
        JOIN users u ON mc.user_id = u.id
        WHERE mc.moment_id = %s
        ORDER BY mc.created_at ASC
        LIMIT 50
        """,
        (moment_id,)
    )
    
    return moment


def toggle_moment_like(moment_id: int, user_id: int) -> bool:
    """点赞/取消点赞瞬间"""
    existing = fetch_one(
        "SELECT id FROM moment_likes WHERE moment_id = %s AND user_id = %s",
        (moment_id, user_id)
    )
    
    if existing:
        # 取消点赞
        execute(
            "DELETE FROM moment_likes WHERE moment_id = %s AND user_id = %s",
            (moment_id, user_id)
        )
        execute(
            "UPDATE user_moments SET like_count = GREATEST(like_count - 1, 0) WHERE id = %s",
            (moment_id,)
        )
        return False
    else:
        # 添加点赞
        execute(
            "INSERT INTO moment_likes (moment_id, user_id) VALUES (%s, %s)",
            (moment_id, user_id)
        )
        execute(
            "UPDATE user_moments SET like_count = like_count + 1 WHERE id = %s",
            (moment_id,)
        )
        return True


def add_moment_comment(
    moment_id: int,
    user_id: int,
    content: str
) -> int:
    """添加评论"""
    comment_id = execute(
        "INSERT INTO moment_comments (moment_id, user_id, content) VALUES (%s, %s, %s)",
        (moment_id, user_id, content)
    )
    
    # 更新评论数
    execute(
        "UPDATE user_moments SET comment_count = comment_count + 1 WHERE id = %s",
        (moment_id,)
    )
    
    return comment_id


def get_moment_comments(
    moment_id: int,
    page: int = 1,
    page_size: int = 20
) -> dict:
    """获取瞬间评论列表"""
    offset = (page - 1) * page_size
    
    total = fetch_one(
        "SELECT COUNT(*) as total FROM moment_comments WHERE moment_id = %s",
        (moment_id,)
    )['total']
    
    comments = fetch_all(
        """
        SELECT mc.*, u.nickname, u.avatar_url
        FROM moment_comments mc
        JOIN users u ON mc.user_id = u.id
        WHERE mc.moment_id = %s
        ORDER BY mc.created_at ASC
        LIMIT %s OFFSET %s
        """,
        (moment_id, page_size, offset)
    )
    
    return {
        'items': comments,
        'page': page,
        'page_size': page_size,
        'total': total
    }


def format_time(dt) -> str:
    """格式化时间显示"""
    if not dt:
        return ''
    
    from datetime import datetime
    
    now = datetime.now()
    diff = (now - dt).total_seconds()
    
    if diff < 60:
        return '刚刚'
    elif diff < 3600:
        return f'{int(diff / 60)}分钟前'
    elif diff < 86400:
        return f'{int(diff / 3600)}小时前'
    elif diff < 604800:
        return f'{int(diff / 86400)}天前'
    else:
        return dt.strftime('%m-%d %H:%M')
