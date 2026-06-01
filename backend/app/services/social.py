"""
社交功能服务：匹配网友和聊天
"""
import json
import random
from datetime import datetime
from typing import Optional

from app.core.db import fetch_all, fetch_one, execute


def calculate_match_score(my_profile: dict, other_profile: dict) -> tuple[float, dict]:
    """
    计算两个用户的匹配分数 (0-100)
    
    返回:
        (总分, 各维度分数详情)
    """
    scores = {}
    
    # 1. 考研年份匹配 (权重: 25%)
    if my_profile.get('exam_year') and other_profile.get('exam_year'):
        if my_profile['exam_year'] == other_profile['exam_year']:
            scores['exam_year'] = 100
        else:
            diff = abs(my_profile['exam_year'] - other_profile['exam_year'])
            scores['exam_year'] = max(0, 100 - diff * 50)
    else:
        scores['exam_year'] = 50  # 未知给中等分
    
    # 2. 专业匹配 (权重: 30%)
    my_major = my_profile.get('target_major_code', '')
    other_major = other_profile.get('target_major_code', '')
    if my_major and other_major:
        if my_major == other_major:
            scores['major'] = 100
        elif my_major[:4] == other_major[:4]:  # 同一学科
            scores['major'] = 60
        elif my_major[:2] == other_major[:2]:  # 同一门类
            scores['major'] = 40
        else:
            scores['major'] = 20
    else:
        scores['major'] = 50
    
    # 3. 成绩水平匹配 (权重: 20%)
    my_score = my_profile.get('score_total')
    other_score = other_profile.get('score_total')
    if my_score and other_score:
        diff = abs(my_score - other_score)
        scores['score'] = max(0, 100 - (diff / 2))  # 相差200分为0
    else:
        scores['score'] = 50
    
    # 4. 地域偏好匹配 (权重: 15%)
    my_pref_provinces = my_profile.get('preferred_provinces')
    other_pref_provinces = other_profile.get('preferred_provinces')
    if my_pref_provinces and other_pref_provinces:
        try:
            my_set = set(json.loads(my_pref_provinces)) if isinstance(my_pref_provinces, str) else set(my_pref_provinces)
            other_set = set(json.loads(other_pref_provinces)) if isinstance(other_pref_provinces, str) else set(other_pref_provinces)
            if my_set and other_set:
                overlap = my_set & other_set
                scores['location'] = (len(overlap) / max(len(my_set | other_set), 1)) * 100
            else:
                scores['location'] = 50
        except:
            scores['location'] = 50
    else:
        scores['location'] = 50
    
    # 5. 学位类型匹配 (权重: 10%)
    my_degree = my_profile.get('target_degree_type')
    other_degree = other_profile.get('target_degree_type')
    if my_degree and other_degree:
        if my_degree == other_degree:
            scores['degree'] = 100
        else:
            scores['degree'] = 30
    else:
        scores['degree'] = 50
    
    # 加权计算总分
    weights = {
        'exam_year': 0.25,
        'major': 0.30,
        'score': 0.20,
        'location': 0.15,
        'degree': 0.10
    }
    
    final_score = sum(scores[k] * weights[k] for k in scores)
    return round(final_score, 2), scores


def get_random_matches(user_id: int, count: int = 5) -> list[dict]:
    """
    获取随机匹配的网友列表
    
    参数:
        user_id: 当前用户ID
        count: 返回数量
    
    返回:
        匹配用户列表，按匹配分数排序
    """
    # 1. 获取当前用户画像
    my_profile = fetch_one(
        """
        SELECT * FROM vw_user_match_pool WHERE user_id = %s
        """,
        (user_id,)
    )
    
    if not my_profile:
        return []
    
    # 2. 获取可匹配用户池（排除自己、已屏蔽、已拒绝的）
    candidates = fetch_all(
        """
        SELECT * FROM vw_user_match_pool 
        WHERE user_id != %s
          AND user_id NOT IN (
              SELECT blocked_id FROM user_blocks WHERE blocker_id = %s
          )
          AND user_id NOT IN (
              SELECT matched_user_id FROM user_matches 
              WHERE user_id = %s AND status IN ('rejected', 'blocked')
          )
        ORDER BY RAND()
        LIMIT 50
        """,
        (user_id, user_id, user_id)
    )
    
    if not candidates:
        return []
    
    # 3. 计算匹配分数
    scored_matches = []
    for candidate in candidates:
        score, dimensions = calculate_match_score(my_profile, candidate)
        
        # 解析地域偏好用于展示
        preferred_provinces = candidate.get('preferred_provinces', '')
        if isinstance(preferred_provinces, str):
            try:
                preferred_provinces = json.loads(preferred_provinces)
            except:
                preferred_provinces = []
        
        scored_matches.append({
            'user_id': candidate['user_id'],
            'nickname': candidate['nickname'],
            'avatar_url': candidate['avatar_url'],
            'bio': candidate.get('bio', ''),
            'exam_year': candidate['exam_year'],
            'target_major_name': candidate.get('target_major_name', ''),
            'target_degree_type': candidate.get('target_degree_type', ''),
            'undergraduate_school': candidate.get('undergraduate_school', ''),
            'preferred_provinces': preferred_provinces,
            'last_active_at': candidate.get('last_active_at'),
            'match_score': score,
            'match_dimensions': dimensions
        })
    
    # 4. 按分数排序，返回前N个
    scored_matches.sort(key=lambda x: x['match_score'], reverse=True)
    return scored_matches[:count]


def accept_match(user_id: int, matched_user_id: int) -> dict:
    """
    接受匹配，创建聊天会话
    
    返回:
        聊天会话信息
    """
    # 更新匹配状态
    execute(
        """
        UPDATE user_matches 
        SET status = 'accepted'
        WHERE user_id = %s AND matched_user_id = %s AND status = 'pending'
        """,
        (user_id, matched_user_id)
    )
    
    # 检查是否已存在聊天会话
    user_a = min(user_id, matched_user_id)
    user_b = max(user_id, matched_user_id)
    
    existing = fetch_one(
        """
        SELECT id FROM user_chats 
        WHERE user_a_id = %s AND user_b_id = %s
        """,
        (user_a, user_b)
    )
    
    if existing:
        return {'chat_id': existing['id'], 'status': 'exists'}
    
    # 创建新聊天会话
    chat_id = execute(
        """
        INSERT INTO user_chats (user_a_id, user_b_id, status)
        VALUES (%s, %s, 'active')
        """,
        (user_a, user_b)
    )
    
    return {'chat_id': chat_id, 'status': 'created'}


def reject_match(user_id: int, matched_user_id: int) -> bool:
    """拒绝匹配"""
    execute(
        """
        UPDATE user_matches 
        SET status = 'rejected'
        WHERE user_id = %s AND matched_user_id = %s AND status = 'pending'
        """,
        (user_id, matched_user_id)
    )
    return True


def block_user(user_id: int, blocked_user_id: int, reason: str = "") -> bool:
    """屏蔽用户"""
    # 添加屏蔽记录
    execute(
        """
        INSERT IGNORE INTO user_blocks (blocker_id, blocked_id, reason)
        VALUES (%s, %s, %s)
        """,
        (user_id, blocked_user_id, reason)
    )
    
    # 更新匹配状态
    execute(
        """
        UPDATE user_matches 
        SET status = 'blocked'
        WHERE (user_id = %s AND matched_user_id = %s)
           OR (user_id = %s AND matched_user_id = %s)
        """,
        (user_id, blocked_user_id, blocked_user_id, user_id)
    )
    
    return True


def get_chat_list(user_id: int) -> list[dict]:
    """获取用户的聊天列表"""
    chats = fetch_all(
        """
        SELECT 
          c.id AS chat_id,
          CASE WHEN c.user_a_id = %s THEN c.user_b_id ELSE c.user_a_id END AS other_user_id,
          c.last_message,
          c.last_message_at,
          CASE WHEN c.user_a_id = %s THEN c.unread_count_a ELSE c.unread_count_b END AS unread_count,
          u.nickname,
          u.avatar_url
        FROM user_chats c
        JOIN users u ON u.id = CASE WHEN c.user_a_id = %s THEN c.user_b_id ELSE c.user_a_id END
        WHERE (c.user_a_id = %s OR c.user_b_id = %s)
          AND c.status = 'active'
        ORDER BY c.last_message_at DESC
        """,
        (user_id, user_id, user_id, user_id, user_id)
    )
    
    return chats


def get_chat_messages(chat_id: int, user_id: int, limit: int = 20, offset: int = 0) -> dict:
    """
    获取聊天消息
    
    返回:
        { messages, other_user, has_more }
    """
    # 获取聊天信息和对方用户
    chat = fetch_one(
        """
        SELECT 
          c.*,
          CASE WHEN c.user_a_id = %s THEN c.user_b_id ELSE c.user_a_id END AS other_user_id
        FROM user_chats c
        WHERE c.id = %s AND (c.user_a_id = %s OR c.user_b_id = %s)
        """,
        (user_id, chat_id, user_id, user_id)
    )
    
    if not chat:
        return {'error': 'chat not found'}
    
    # 获取消息列表
    messages = fetch_all(
        """
        SELECT id, sender_id, content, message_type, is_read, created_at
        FROM user_messages
        WHERE chat_id = %s
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """,
        (chat_id, limit, offset)
    )
    
    # 反转消息顺序（最新的在最后）
    messages.reverse()
    
    # 标记已读
    execute(
        """
        UPDATE user_messages 
        SET is_read = 1
        WHERE chat_id = %s AND receiver_id = %s AND is_read = 0
        """,
        (chat_id, user_id)
    )
    
    # 清零未读计数
    if user_id == chat['user_a_id']:
        execute("UPDATE user_chats SET unread_count_a = 0 WHERE id = %s", (chat_id,))
    else:
        execute("UPDATE user_chats SET unread_count_b = 0 WHERE id = %s", (chat_id,))
    
    # 获取对方信息
    other_user = fetch_one(
        "SELECT id, nickname, avatar_url FROM users WHERE id = %s",
        (chat['other_user_id'],)
    )
    
    return {
        'messages': messages,
        'other_user': other_user,
        'has_more': len(messages) == limit
    }


def send_message(chat_id: int, sender_id: int, content: str, message_type: str = 'text') -> dict:
    """
    发送消息
    
    返回:
        消息信息
    """
    # 获取聊天会话确定接收者
    chat = fetch_one(
        "SELECT user_a_id, user_b_id FROM user_chats WHERE id = %s",
        (chat_id,)
    )
    
    if not chat:
        return {'error': 'chat not found'}
    
    receiver_id = chat['user_b_id'] if sender_id == chat['user_a_id'] else chat['user_a_id']
    
    # 插入消息
    message_id = execute(
        """
        INSERT INTO user_messages (chat_id, sender_id, receiver_id, content, message_type)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (chat_id, sender_id, receiver_id, content, message_type)
    )
    
    # 更新聊天会话
    execute(
        """
        UPDATE user_chats 
        SET last_message = %s,
            last_message_at = NOW(),
            unread_count_a = CASE WHEN %s = user_a_id THEN unread_count_a ELSE unread_count_a + 1 END,
            unread_count_b = CASE WHEN %s = user_b_id THEN unread_count_b ELSE unread_count_b + 1 END
        WHERE id = %s
        """,
        (content[:100], sender_id, sender_id, chat_id)
    )
    
    return {
        'message_id': message_id,
        'created_at': datetime.now().isoformat()
    }


def get_user_public_profile(user_id: int, viewer_id: int) -> Optional[dict]:
    """获取用户的公开画像（用于匹配展示）"""
    # 检查是否被屏蔽
    blocked = fetch_one(
        "SELECT 1 FROM user_blocks WHERE blocker_id = %s AND blocked_id = %s",
        (viewer_id, user_id)
    )
    
    if blocked:
        return None
    
    profile = fetch_one(
        """
        SELECT 
          u.nickname,
          u.avatar_url,
          up.exam_year,
          up.target_major_name,
          up.target_degree_type,
          up.undergraduate_school,
          up.preferred_provinces,
          up.bio,
          up.last_active_at
        FROM users u
        JOIN user_profiles up ON u.id = up.user_id
        WHERE u.id = %s AND up.is_visible_to_others = 1
        """,
        (user_id,)
    )
    
    if profile and profile.get('preferred_provinces'):
        try:
            profile['preferred_provinces'] = json.loads(profile['preferred_provinces'])
        except:
            profile['preferred_provinces'] = []
    
    return profile
