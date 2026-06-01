"""
问题咨询与教学信息服务
"""
import json
from typing import Optional

from app.core.db import fetch_all, fetch_one, execute


# ========================================
# 用户目标院校管理
# ========================================

def set_user_target_school(
    user_id: int,
    school_id: int,
    school_name: str,
    exam_year: int,
    major_id: Optional[int] = None,
    major_code: Optional[str] = None,
    major_name: Optional[str] = None
) -> dict:
    """设置用户目标院校"""
    # 使用 INSERT ... ON DUPLICATE KEY UPDATE
    execute(
        """
        INSERT INTO user_target_schools 
        (user_id, school_id, school_name, major_id, major_code, major_name, exam_year)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
          school_id = VALUES(school_id),
          school_name = VALUES(school_name),
          major_id = VALUES(major_id),
          major_code = VALUES(major_code),
          major_name = VALUES(major_name),
          exam_year = VALUES(exam_year)
        """,
        (user_id, school_id, school_name, major_id, major_code, major_name, exam_year)
    )
    
    return get_user_target_school(user_id)


def get_user_target_school(user_id: int) -> Optional[dict]:
    """获取用户目标院校"""
    return fetch_one(
        """
        SELECT * FROM user_target_schools WHERE user_id = %s
        """,
        (user_id,)
    )


# ========================================
# 教学信息帖子管理
# ========================================

def create_tutoring_post(
    user_id: int,
    school_id: int,
    major_id: int,
    subject_type: str,
    subject_name: str,
    title: str,
    content: str,
    price: float,
    current_school: Optional[str] = None,
    current_major: Optional[str] = None,
    exam_score: Optional[int] = None,
    subject_score: Optional[int] = None,
    bio: Optional[str] = None,
    teaching_mode: str = 'online',
    contact_info: Optional[str] = None,
    images: Optional[list] = None
) -> int:
    """创建教学信息帖子"""
    post_id = execute(
        """
        INSERT INTO tutoring_posts (
            user_id, school_id, major_id, subject_type, subject_name,
            title, content, price, current_school, current_major,
            exam_score, subject_score, bio, teaching_mode, contact_info
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (user_id, school_id, major_id, subject_type, subject_name,
         title, content, price, current_school, current_major,
         exam_score, subject_score, bio, teaching_mode, contact_info)
    )
    
    # 保存图片
    if images:
        for idx, img in enumerate(images):
            execute(
                """
                INSERT INTO tutoring_post_images (post_id, image_url, image_type, sort_order)
                VALUES (%s, %s, %s, %s)
                """,
                (post_id, img['url'], img.get('type', 'other'), idx)
            )
    
    return post_id


def get_tutoring_posts(
    school_id: int,
    major_id: int,
    subject_type: str = "",
    page: int = 1,
    page_size: int = 20
) -> dict:
    """获取教学信息列表"""
    conditions = ["tp.status = 'active'", "tp.school_id = %s"]
    params = [school_id]
    
    # major_id 为 0 表示不限专业
    if major_id and major_id > 0:
        conditions.append("tp.major_id = %s")
        params.append(major_id)
    
    if subject_type:
        conditions.append("tp.subject_type = %s")
        params.append(subject_type)
    
    # 查总数
    count_query = f"SELECT COUNT(*) as total FROM tutoring_posts tp WHERE {' AND '.join(conditions)}"
    total = fetch_one(count_query, tuple(params))['total']
    
    # 分页查询
    offset = (page - 1) * page_size
    query = f"""
        SELECT 
          tp.*,
          u.nickname,
          u.avatar_url,
          (SELECT image_url FROM tutoring_post_images 
           WHERE post_id = tp.id AND image_type = 'avatar' 
           ORDER BY sort_order LIMIT 1) as teacher_avatar,
          (SELECT GROUP_CONCAT(CONCAT(image_url, '|', image_type) ORDER BY sort_order) 
           FROM tutoring_post_images WHERE post_id = tp.id) as images_str
        FROM tutoring_posts tp
        JOIN users u ON tp.user_id = u.id
        WHERE {' AND '.join(conditions)}
        ORDER BY tp.order_count DESC, tp.like_count DESC, tp.created_at DESC
        LIMIT %s OFFSET %s
    """
    params.extend([page_size, offset])
    posts = fetch_all(query, tuple(params))
    
    # 处理图片
    for post in posts:
        images = []
        if post.get('images_str'):
            for img_str in post['images_str'].split(','):
                parts = img_str.split('|')
                images.append({
                    'url': parts[0],
                    'type': parts[1] if len(parts) > 1 else 'other'
                })
        post['images'] = images
        del post['images_str']
    
    return {
        'items': posts,
        'page': page,
        'page_size': page_size,
        'total': total
    }


def get_tutoring_post_detail(post_id: int, user_id: Optional[int] = None) -> Optional[dict]:
    """获取教学帖子详情"""
    # 增加浏览
    execute(
        "UPDATE tutoring_posts SET view_count = view_count + 1 WHERE id = %s",
        (post_id,)
    )
    
    post = fetch_one(
        """
        SELECT 
          tp.*,
          u.nickname,
          u.avatar_url
        FROM tutoring_posts tp
        JOIN users u ON tp.user_id = u.id
        WHERE tp.id = %s AND tp.status = 'active'
        """,
        (post_id,)
    )
    
    if not post:
        return None
    
    # 获取图片
    post['images'] = fetch_all(
        "SELECT image_url, image_type, sort_order FROM tutoring_post_images WHERE post_id = %s ORDER BY sort_order",
        (post_id,)
    )
    
    # 检查用户是否已点赞
    if user_id:
        like_record = fetch_one(
            "SELECT id FROM tutoring_post_likes WHERE post_id = %s AND user_id = %s",
            (post_id, user_id)
        )
        post['is_liked'] = like_record is not None
    else:
        post['is_liked'] = False
    
    return post


def toggle_tutoring_like(post_id: int, user_id: int) -> bool:
    """点赞教学帖子"""
    # 检查是否已点赞
    existing = fetch_one(
        "SELECT id FROM tutoring_post_likes WHERE post_id = %s AND user_id = %s",
        (post_id, user_id)
    )
    
    if existing:
        # 取消点赞
        execute(
            "DELETE FROM tutoring_post_likes WHERE post_id = %s AND user_id = %s",
            (post_id, user_id)
        )
        execute(
            "UPDATE tutoring_posts SET like_count = GREATEST(like_count - 1, 0) WHERE id = %s",
            (post_id,)
        )
        return False
    else:
        # 添加点赞
        execute(
            "INSERT INTO tutoring_post_likes (post_id, user_id) VALUES (%s, %s)",
            (post_id, user_id)
        )
        execute(
            "UPDATE tutoring_posts SET like_count = like_count + 1 WHERE id = %s",
            (post_id,)
        )
        return True
