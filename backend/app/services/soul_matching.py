"""
灵魂匹配服务（类似Soul灵魂匹配）
"""
from typing import Optional
import json
import uuid
from datetime import datetime

from app.core.db import fetch_all, fetch_one, execute


# ========================================
# 偏好管理
# ========================================

def set_matching_preferences(
    user_id: int,
    gender_preference: str = 'any',
    age_min: Optional[int] = None,
    age_max: Optional[int] = None,
    exam_year: Optional[int] = None,
    target_major: Optional[str] = None,
    target_school_level: Optional[str] = None,
    target_degree_type: Optional[str] = None,
    study_style: Optional[str] = None,
    personality_type: Optional[str] = None,
    study_intensity: Optional[str] = None,
    preferred_provinces: Optional[list] = None,
    online_only: bool = False
) -> dict:
    """设置匹配偏好"""
    provinces_json = json.dumps(preferred_provinces) if preferred_provinces else None
    
    execute(
        """
        INSERT INTO soul_matching_preferences 
        (user_id, gender_preference, age_min, age_max, exam_year, target_major,
         target_school_level, target_degree_type, study_style, personality_type,
         study_intensity, preferred_provinces, online_only)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
          gender_preference = VALUES(gender_preference),
          age_min = VALUES(age_min),
          age_max = VALUES(age_max),
          exam_year = VALUES(exam_year),
          target_major = VALUES(target_major),
          target_school_level = VALUES(target_school_level),
          target_degree_type = VALUES(target_degree_type),
          study_style = VALUES(study_style),
          personality_type = VALUES(personality_type),
          study_intensity = VALUES(study_intensity),
          preferred_provinces = VALUES(preferred_provinces),
          online_only = VALUES(online_only)
        """,
        (user_id, gender_preference, age_min, age_max, exam_year, target_major,
         target_school_level, target_degree_type, study_style, personality_type,
         study_intensity, provinces_json, online_only)
    )
    
    return get_matching_preferences(user_id)


def get_matching_preferences(user_id: int) -> Optional[dict]:
    """获取用户匹配偏好"""
    pref = fetch_one(
        "SELECT * FROM soul_matching_preferences WHERE user_id = %s",
        (user_id,)
    )
    
    if pref and pref.get('preferred_provinces'):
        try:
            pref['preferred_provinces'] = json.loads(pref['preferred_provinces'])
        except:
            pref['preferred_provinces'] = []
    
    return pref


# ========================================
# 订单管理
# ========================================

def create_matching_order(user_id: int, price: float = 9.9) -> dict:
    """创建匹配订单"""
    order_no = f"SOUL{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"
    
    order_id = execute(
        """
        INSERT INTO soul_matching_orders (user_id, order_no, price, status)
        VALUES (%s, %s, %s, 'pending')
        """,
        (user_id, order_no, price)
    )
    
    return {
        'order_id': order_id,
        'order_no': order_no,
        'price': price,
        'status': 'pending'
    }


def pay_order(order_id: int, user_id: int) -> dict:
    """支付订单"""
    # 验证订单
    order = fetch_one(
        "SELECT * FROM soul_matching_orders WHERE id = %s AND user_id = %s AND status = 'pending'",
        (order_id, user_id)
    )
    
    if not order:
        raise ValueError("订单不存在或已支付")
    
    # 更新订单状态
    execute(
        """
        UPDATE soul_matching_orders 
        SET status = 'paid', pay_time = NOW()
        WHERE id = %s
        """,
        (order_id,)
    )
    
    return fetch_one(
        "SELECT * FROM soul_matching_orders WHERE id = %s",
        (order_id,)
    )


# ========================================
# 匹配算法
# ========================================

def find_match(order_id: int, user_id: int) -> Optional[dict]:
    """执行匹配算法"""
    # 获取用户偏好
    user_pref = get_matching_preferences(user_id)
    if not user_pref:
        raise ValueError("请先设置匹配偏好")
    
    # 更新订单状态为匹配中
    execute(
        "UPDATE soul_matching_orders SET status = 'matching', match_time = NOW() WHERE id = %s",
        (order_id,)
    )
    
    # 查询所有可见且未屏蔽的用户
    candidates = fetch_all(
        """
        SELECT 
          u.id, u.nickname, u.avatar_url,
          up.exam_year, up.target_major_name, up.target_degree_type,
          up.target_study_mode, up.preferred_provinces,
          up.undergraduate_school, up.bio
        FROM users u
        JOIN user_profiles up ON u.id = up.user_id
        WHERE u.id != %s
          AND u.status = 'active'
          AND up.is_visible_to_others = 1
          AND u.id NOT IN (
            SELECT blocked_id FROM user_blocks WHERE blocker_id = %s
            UNION
            SELECT blocker_id FROM user_blocks WHERE blocked_id = %s
          )
        """,
        (user_id, user_id, user_id)
    )
    
    if not candidates:
        return None
    
    # 计算匹配分数
    scored_candidates = []
    for candidate in candidates:
        score, dimensions = calculate_match_score(user_pref, candidate)
        scored_candidates.append({
            **candidate,
            'match_score': score,
            'match_dimensions': dimensions
        })
    
    # 按匹配分数排序，取最高分
    scored_candidates.sort(key=lambda x: x['match_score'], reverse=True)
    best_match = scored_candidates[0]
    
    # 保存匹配记录
    record_id = execute(
        """
        INSERT INTO soul_matching_records 
        (order_id, user_a_id, user_b_id, match_score, match_dimensions, status)
        VALUES (%s, %s, %s, %s, %s, 'pending')
        """,
        (order_id, user_id, best_match['id'], 
         best_match['match_score'], 
         json.dumps(best_match['match_dimensions']))
    )
    
    # 更新订单状态
    execute(
        "UPDATE soul_matching_orders SET status = 'completed', completed_time = NOW() WHERE id = %s",
        (order_id,)
    )
    
    return {
        'record_id': record_id,
        'matched_user': best_match
    }


def calculate_match_score(user_pref: dict, candidate: dict) -> tuple:
    """
    计算匹配分数（5维度加权）
    返回: (总分, 维度详情)
    """
    dimensions = {}
    total_score = 0
    weights = {
        'exam_year': 0.30,      # 考研年份 30%
        'major': 0.25,          # 专业 25%
        'degree_type': 0.15,    # 学位类型 15%
        'study_style': 0.15,    # 学习风格 15%
        'personality': 0.15     # 性格 15%
    }
    
    # 1. 考研年份匹配 (30%)
    if user_pref.get('exam_year') and candidate.get('exam_year'):
        if user_pref['exam_year'] == candidate['exam_year']:
            dimensions['exam_year'] = 100
        else:
            # 差一年扣30分
            diff = abs(user_pref['exam_year'] - candidate['exam_year'])
            dimensions['exam_year'] = max(0, 100 - diff * 30)
    else:
        dimensions['exam_year'] = 50  # 未设置给中间分
    
    # 2. 专业匹配 (25%)
    if user_pref.get('target_major') and candidate.get('target_major_name'):
        if user_pref['target_major'].lower() in candidate['target_major_name'].lower():
            dimensions['major'] = 100
        else:
            dimensions['major'] = 30
    else:
        dimensions['major'] = 50
    
    # 3. 学位类型匹配 (15%)
    if user_pref.get('target_degree_type') and candidate.get('target_degree_type'):
        if user_pref['target_degree_type'] == candidate['target_degree_type']:
            dimensions['degree_type'] = 100
        else:
            dimensions['degree_type'] = 0
    else:
        dimensions['degree_type'] = 50
    
    # 4. 学习风格匹配 (15%)
    if user_pref.get('study_style'):
        style_map = {
            '早起型': ['早起型'],
            '夜猫子': ['夜猫子'],
            '均衡型': ['均衡型']
        }
        candidate_style = candidate.get('target_study_mode', '')
        if user_pref['study_style'] == candidate_style:
            dimensions['study_style'] = 100
        else:
            dimensions['study_style'] = 40
    else:
        dimensions['study_style'] = 50
    
    # 5. 性格匹配 (15%)
    if user_pref.get('personality_type'):
        if user_pref['personality_type'] == candidate.get('bio', '')[:10]:
            dimensions['personality'] = 100
        else:
            dimensions['personality'] = 50
    else:
        dimensions['personality'] = 50
    
    # 计算加权总分
    for dim, weight in weights.items():
        total_score += dimensions.get(dim, 50) * weight
    
    return round(total_score, 2), dimensions


# ========================================
# 匹配记录管理
# ========================================

def accept_match(record_id: int, user_id: int) -> bool:
    """接受匹配"""
    record = fetch_one(
        "SELECT * FROM soul_matching_records WHERE id = %s",
        (record_id,)
    )
    
    if not record:
        raise ValueError("匹配记录不存在")
    
    # 确定当前用户是A还是B
    is_user_a = record['user_a_id'] == user_id
    action_field = 'user_a_action' if is_user_a else 'user_b_action'
    
    execute(
        f"UPDATE soul_matching_records SET {action_field} = 'accept' WHERE id = %s",
        (record_id,)
    )
    
    # 检查双方是否都接受
    updated_record = fetch_one("SELECT * FROM soul_matching_records WHERE id = %s", (record_id,))
    
    if updated_record['user_a_action'] == 'accept' and updated_record['user_b_action'] == 'accept':
        # 创建聊天会话
        from app.services.social import create_chat
        chat_id = create_chat(record['user_a_id'], record['user_b_id'])
        
        execute(
            "UPDATE soul_matching_records SET status = 'chatting', chat_id = %s WHERE id = %s",
            (chat_id, record_id)
        )
        
        return True
    
    return False


def reject_match(record_id: int, user_id: int):
    """拒绝匹配"""
    record = fetch_one(
        "SELECT * FROM soul_matching_records WHERE id = %s",
        (record_id,)
    )
    
    if not record:
        raise ValueError("匹配记录不存在")
    
    is_user_a = record['user_a_id'] == user_id
    action_field = 'user_a_action' if is_user_a else 'user_b_action'
    
    execute(
        f"UPDATE soul_matching_records SET {action_field} = 'reject' WHERE id = %s",
        (record_id,)
    )


def get_user_match_records(user_id: int, page: int = 1, page_size: int = 10) -> dict:
    """获取用户匹配记录"""
    offset = (page - 1) * page_size
    
    total = fetch_one(
        "SELECT COUNT(*) as total FROM soul_matching_records WHERE user_a_id = %s OR user_b_id = %s",
        (user_id, user_id)
    )['total']
    
    records = fetch_all(
        """
        SELECT 
          smr.*,
          u.nickname, u.avatar_url,
          CASE 
            WHEN smr.user_a_id = %s THEN smr.user_b_id
            ELSE smr.user_a_id
          END as matched_user_id
        FROM soul_matching_records smr
        JOIN users u ON (
          CASE 
            WHEN smr.user_a_id = %s THEN smr.user_b_id
            ELSE smr.user_a_id
          END = u.id
        )
        WHERE smr.user_a_id = %s OR smr.user_b_id = %s
        ORDER BY smr.created_at DESC
        LIMIT %s OFFSET %s
        """,
        (user_id, user_id, user_id, user_id, page_size, offset)
    )
    
    for record in records:
        if record.get('match_dimensions'):
            try:
                record['match_dimensions'] = json.loads(record['match_dimensions'])
            except:
                record['match_dimensions'] = {}
    
    return {
        'items': records,
        'page': page,
        'page_size': page_size,
        'total': total
    }


# ========================================
# 问答题库
# ========================================

def get_matching_questions(count: int = 8) -> list:
    """获取匹配问题"""
    questions = fetch_all(
        "SELECT * FROM soul_matching_questions WHERE is_active = 1 ORDER BY sort_order LIMIT %s",
        (count,)
    )
    return questions
