"""
经验分享服务（小红书笔记模式）
"""
from typing import Optional
import json

from app.core.db import fetch_all, fetch_one, execute


# ========================================
# 笔记管理
# ========================================

def create_note(
    user_id: int,
    title: str,
    content: str,
    category: Optional[str] = None,
    tags: Optional[list] = None,
    images: Optional[list] = None
) -> int:
    """创建经验笔记"""
    tags_json = json.dumps(tags) if tags else None
    
    note_id = execute(
        """
        INSERT INTO experience_notes (user_id, title, content, category, tags)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (user_id, title, content, category, tags_json)
    )
    
    # 保存图片
    if images:
        for idx, img in enumerate(images):
            is_cover = 1 if idx == 0 else 0
            execute(
                """
                INSERT INTO note_images (note_id, image_url, is_cover, sort_order)
                VALUES (%s, %s, %s, %s)
                """,
                (note_id, img['url'], is_cover, idx)
            )
    
    return note_id


def get_note_list(
    page: int = 1,
    page_size: int = 20,
    category: Optional[str] = None,
    sort_by: str = 'newest',
    user_id: Optional[int] = None
) -> dict:
    """获取笔记列表"""
    conditions = ["en.status = 'active'"]
    params = []
    
    if category:
        conditions.append("en.category = %s")
        params.append(category)
    
    # 排序
    if sort_by == 'hot':
        order_by = "en.like_count DESC, en.collect_count DESC, en.created_at DESC"
    elif sort_by == 'newest':
        order_by = "en.created_at DESC"
    else:
        order_by = "en.created_at DESC"
    
    offset = (page - 1) * page_size
    
    # 查总数
    count_query = f"SELECT COUNT(*) as total FROM experience_notes en WHERE {' AND '.join(conditions)}"
    total = fetch_one(count_query, tuple(params))['total']
    
    # 分页查询
    query = f"""
        SELECT 
          en.*,
          u.nickname,
          u.avatar_url,
          (SELECT GROUP_CONCAT(image_url ORDER BY sort_order) 
           FROM note_images WHERE note_id = en.id) as images_str
        FROM experience_notes en
        JOIN users u ON en.user_id = u.id
        WHERE {' AND '.join(conditions)}
        ORDER BY {order_by}
        LIMIT %s OFFSET %s
    """
    params.extend([page_size, offset])
    notes = fetch_all(query, tuple(params))
    
    # 处理图片和用户状态
    for note in notes:
        # 处理图片
        if note.get('images_str'):
            note['images'] = note['images_str'].split(',')
        else:
            note['images'] = []
        del note['images_str']
        
        # 解析标签
        if note.get('tags'):
            try:
                note['tags_list'] = json.loads(note['tags'])
            except:
                note['tags_list'] = []
        else:
            note['tags_list'] = []
        
        # 检查用户是否已点赞/收藏
        if user_id:
            like_record = fetch_one(
                "SELECT id FROM note_likes WHERE note_id = %s AND user_id = %s",
                (note['id'], user_id)
            )
            note['is_liked'] = like_record is not None
            
            collect_record = fetch_one(
                "SELECT id FROM note_collections WHERE note_id = %s AND user_id = %s",
                (note['id'], user_id)
            )
            note['is_collected'] = collect_record is not None
        else:
            note['is_liked'] = False
            note['is_collected'] = False
        
        # 格式化时间
        note['created_at_str'] = format_time(note['created_at'])
    
    return {
        'items': notes,
        'page': page,
        'page_size': page_size,
        'total': total
    }


def get_note_detail(note_id: int, user_id: Optional[int] = None) -> Optional[dict]:
    """获取笔记详情"""
    # 增加浏览
    execute(
        "UPDATE experience_notes SET view_count = view_count + 1 WHERE id = %s",
        (note_id,)
    )
    
    note = fetch_one(
        """
        SELECT 
          en.*,
          u.nickname,
          u.avatar_url
        FROM experience_notes en
        JOIN users u ON en.user_id = u.id
        WHERE en.id = %s AND en.status = 'active'
        """,
        (note_id,)
    )
    
    if not note:
        return None
    
    # 获取图片
    images = fetch_all(
        "SELECT image_url, is_cover FROM note_images WHERE note_id = %s ORDER BY sort_order",
        (note_id,)
    )
    note['images'] = [img['image_url'] for img in images]
    
    # 解析标签
    if note.get('tags'):
        try:
            note['tags_list'] = json.loads(note['tags'])
        except:
            note['tags_list'] = []
    else:
        note['tags_list'] = []
    
    # 检查点赞/收藏状态
    if user_id:
        like_record = fetch_one(
            "SELECT id FROM note_likes WHERE note_id = %s AND user_id = %s",
            (note_id, user_id)
        )
        note['is_liked'] = like_record is not None
        
        collect_record = fetch_one(
            "SELECT id FROM note_collections WHERE note_id = %s AND user_id = %s",
            (note_id, user_id)
        )
        note['is_collected'] = collect_record is not None
    else:
        note['is_liked'] = False
        note['is_collected'] = False
    
    # 获取评论
    note['comments'] = fetch_all(
        """
        SELECT nc.*, u.nickname, u.avatar_url
        FROM note_comments nc
        JOIN users u ON nc.user_id = u.id
        WHERE nc.note_id = %s AND nc.parent_id IS NULL
        ORDER BY nc.created_at ASC
        LIMIT 50
        """,
        (note_id,)
    )
    
    return note


def toggle_note_like(note_id: int, user_id: int) -> bool:
    """点赞/取消点赞笔记"""
    existing = fetch_one(
        "SELECT id FROM note_likes WHERE note_id = %s AND user_id = %s",
        (note_id, user_id)
    )
    
    if existing:
        execute(
            "DELETE FROM note_likes WHERE note_id = %s AND user_id = %s",
            (note_id, user_id)
        )
        execute(
            "UPDATE experience_notes SET like_count = GREATEST(like_count - 1, 0) WHERE id = %s",
            (note_id,)
        )
        return False
    else:
        execute(
            "INSERT INTO note_likes (note_id, user_id) VALUES (%s, %s)",
            (note_id, user_id)
        )
        execute(
            "UPDATE experience_notes SET like_count = like_count + 1 WHERE id = %s",
            (note_id,)
        )
        return True


def toggle_note_collect(note_id: int, user_id: int) -> bool:
    """收藏/取消收藏笔记"""
    existing = fetch_one(
        "SELECT id FROM note_collections WHERE note_id = %s AND user_id = %s",
        (note_id, user_id)
    )
    
    if existing:
        execute(
            "DELETE FROM note_collections WHERE note_id = %s AND user_id = %s",
            (note_id, user_id)
        )
        execute(
            "UPDATE experience_notes SET collect_count = GREATEST(collect_count - 1, 0) WHERE id = %s",
            (note_id,)
        )
        return False
    else:
        execute(
            "INSERT INTO note_collections (note_id, user_id) VALUES (%s, %s)",
            (note_id, user_id)
        )
        execute(
            "UPDATE experience_notes SET collect_count = collect_count + 1 WHERE id = %s",
            (note_id,)
        )
        return True


def add_note_comment(
    note_id: int,
    user_id: int,
    content: str,
    parent_id: Optional[int] = None
) -> int:
    """添加评论"""
    comment_id = execute(
        "INSERT INTO note_comments (note_id, user_id, content, parent_id) VALUES (%s, %s, %s, %s)",
        (note_id, user_id, content, parent_id)
    )
    
    # 更新评论数
    execute(
        "UPDATE experience_notes SET comment_count = comment_count + 1 WHERE id = %s",
        (note_id,)
    )
    
    return comment_id


def get_note_comments(
    note_id: int,
    page: int = 1,
    page_size: int = 20
) -> dict:
    """获取笔记评论列表"""
    offset = (page - 1) * page_size
    
    total = fetch_one(
        "SELECT COUNT(*) as total FROM note_comments WHERE note_id = %s AND parent_id IS NULL",
        (note_id,)
    )['total']
    
    comments = fetch_all(
        """
        SELECT nc.*, u.nickname, u.avatar_url
        FROM note_comments nc
        JOIN users u ON nc.user_id = u.id
        WHERE nc.note_id = %s AND nc.parent_id IS NULL
        ORDER BY nc.created_at ASC
        LIMIT %s OFFSET %s
        """,
        (note_id, page_size, offset)
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
