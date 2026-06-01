"""
学习资料互助服务
"""
import json
from typing import Optional

from app.core.db import fetch_all, fetch_one, execute


def create_post(
    user_id: int,
    title: str,
    content: str,
    post_type: str,
    price: Optional[float] = None,
    original_price: Optional[float] = None,
    condition_level: Optional[str] = None,
    province: Optional[str] = None,
    city: Optional[str] = None,
    detail_address: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    tags: Optional[list] = None,
    category: Optional[str] = None,
    trade_method: str = 'both',
    contact_info: Optional[str] = None,
    images: Optional[list] = None
) -> int:
    """创建学习资料帖子"""
    tags_json = json.dumps(tags, ensure_ascii=False) if tags else None
    
    post_id = execute(
        """
        INSERT INTO study_posts (
            user_id, title, content, post_type, price, original_price,
            condition_level, province, city, detail_address, latitude, longitude,
            tags, category, trade_method, contact_info
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (user_id, title, content, post_type, price, original_price,
         condition_level, province, city, detail_address, latitude, longitude,
         tags_json, category, trade_method, contact_info)
    )
    
    # 保存图片
    if images:
        for idx, img_url in enumerate(images):
            execute(
                """
                INSERT INTO study_post_images (post_id, image_url, sort_order)
                VALUES (%s, %s, %s)
                """,
                (post_id, img_url, idx)
            )
    
    return post_id


def get_post_list(
    keyword: str = "",
    post_type: str = "",
    category: str = "",
    province: str = "",
    city: str = "",
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    page: int = 1,
    page_size: int = 20
) -> dict:
    """获取帖子列表（支持搜索和筛选）"""
    conditions = ["sp.status = 'active'"]
    params = []
    
    if keyword:
        conditions.append("(sp.title LIKE %s OR sp.content LIKE %s OR sp.tags LIKE %s)")
        wildcard = f"%{keyword}%"
        params.extend([wildcard, wildcard, wildcard])
    
    if post_type:
        conditions.append("sp.post_type = %s")
        params.append(post_type)
    
    if category:
        conditions.append("sp.category = %s")
        params.append(category)
    
    if province:
        conditions.append("sp.province = %s")
        params.append(province)
    
    if city:
        conditions.append("sp.city = %s")
        params.append(city)
    
    if min_price is not None:
        conditions.append("sp.price >= %s")
        params.append(min_price)
    
    if max_price is not None:
        conditions.append("sp.price <= %s")
        params.append(max_price)
    
    # 查总数
    count_conditions = [c.replace('sp.', '') for c in conditions]
    count_query = f"SELECT COUNT(*) as total FROM study_posts WHERE {' AND '.join(count_conditions)}"
    total = fetch_one(count_query, tuple(params))['total']
    
    # 分页查询
    offset = (page - 1) * page_size
    query = f"""
        SELECT 
          sp.id,
          sp.user_id,
          sp.title,
          sp.content,
          sp.post_type,
          sp.price,
          sp.original_price,
          sp.condition_level,
          sp.province,
          sp.city,
          sp.category,
          sp.trade_method,
          sp.view_count,
          sp.like_count,
          sp.comment_count,
          sp.created_at,
          u.nickname,
          u.avatar_url,
          (SELECT image_url 
           FROM study_post_images WHERE post_id = sp.id ORDER BY sort_order LIMIT 1) as cover_image
        FROM study_posts sp
        JOIN users u ON sp.user_id = u.id
        WHERE {' AND '.join(conditions)}
        ORDER BY sp.created_at DESC
        LIMIT %s OFFSET %s
    """
    params.extend([page_size, offset])
    posts = fetch_all(query, tuple(params))
    
    # 处理tags
    for post in posts:
        if post.get('tags'):
            try:
                post['tags'] = json.loads(post['tags']) if isinstance(post['tags'], str) else post['tags']
            except:
                post['tags'] = []
    
    return {
        'items': posts,
        'page': page,
        'page_size': page_size,
        'total': total
    }


def get_post_detail(post_id: int, user_id: Optional[int] = None) -> Optional[dict]:
    """获取帖子详情"""
    # 增加浏览次数
    execute(
        "UPDATE study_posts SET view_count = view_count + 1 WHERE id = %s",
        (post_id,)
    )
    
    post = fetch_one(
        """
        SELECT 
          sp.*,
          u.nickname,
          u.avatar_url
        FROM study_posts sp
        JOIN users u ON sp.user_id = u.id
        WHERE sp.id = %s AND sp.status = 'active'
        """,
        (post_id,)
    )
    
    if not post:
        return None
    
    # 解析tags
    if post.get('tags'):
        try:
            post['tags'] = json.loads(post['tags']) if isinstance(post['tags'], str) else post['tags']
        except:
            post['tags'] = []
    
    # 获取图片列表
    post['images'] = fetch_all(
        "SELECT image_url, sort_order FROM study_post_images WHERE post_id = %s ORDER BY sort_order",
        (post_id,)
    )
    
    # 检查是否已点赞
    if user_id:
        post['is_liked'] = fetch_one(
            "SELECT 1 FROM study_post_likes WHERE post_id = %s AND user_id = %s",
            (post_id, user_id)
        ) is not None
    else:
        post['is_liked'] = False
    
    return post


def toggle_like(post_id: int, user_id: int) -> bool:
    """切换点赞状态"""
    existing = fetch_one(
        "SELECT id FROM study_post_likes WHERE post_id = %s AND user_id = %s",
        (post_id, user_id)
    )
    
    if existing:
        # 取消点赞
        execute(
            "DELETE FROM study_post_likes WHERE post_id = %s AND user_id = %s",
            (post_id, user_id)
        )
        execute(
            "UPDATE study_posts SET like_count = GREATEST(like_count - 1, 0) WHERE id = %s",
            (post_id,)
        )
        return False
    else:
        # 添加点赞
        execute(
            "INSERT IGNORE INTO study_post_likes (post_id, user_id) VALUES (%s, %s)",
            (post_id, user_id)
        )
        execute(
            "UPDATE study_posts SET like_count = like_count + 1 WHERE id = %s",
            (post_id,)
        )
        return True


def search_suggestions(keyword: str, limit: int = 10) -> list:
    """搜索建议"""
    posts = fetch_all(
        """
        SELECT id, title, post_type, category, price
        FROM study_posts
        WHERE status = 'active' AND title LIKE %s
        ORDER BY view_count DESC
        LIMIT %s
        """,
        (f"%{keyword}%", limit)
    )
    return posts
