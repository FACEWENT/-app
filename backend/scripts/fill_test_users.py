"""
生成 users 和 user_profiles 测试数据
"""
import json
import random
import pymysql
from pymysql.cursors import DictCursor
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "lwt18251X",
    "database": "kaoyan_system_v2",
    "charset": "utf8mb4",
    "cursorclass": DictCursor,
    "autocommit": True,
}

def get_connection():
    return pymysql.connect(**DB_CONFIG)

# 测试数据池
NICKNAMES = [
    "考研小能手", "上岸锦鲤", "研途有你", "追梦人", "学霸本霸",
    "好好学习", "天天向上", "考研冲刺", "研究生预备役", "未来研究生",
    "985冲刺", "双一流目标", "考研人", "研途漫漫", "奋斗青年",
    "学霸养成中", "考研倒计时", "梦想启航", "研途风景", "考研日记"
]

PROVINCES = ["北京市", "上海市", "广东省", "江苏省", "浙江省", "湖北省", 
             "四川省", "山东省", "河南省", "河北省", "湖南省", "福建省"]

CITIES = ["北京市", "上海市", "广州市", "深圳市", "南京市", "杭州市", 
          "武汉市", "成都市", "济南市", "郑州市", "长沙市", "福州市"]

SCHOOL_LEVELS = ["985工程", "211工程", "双一流", "普通本科"]

UNDERGRAD_SCHOOLS = [
    "武汉大学", "华中科技大学", "郑州大学", "河南大学", "山东大学",
    "苏州大学", "上海大学", "南京师范大学", "杭州电子科技大学",
    "武汉理工大学", "西南大学", "西北大学", "南昌大学", "云南大学"
]

def generate_test_users(count: int = 20):
    """生成测试用户"""
    logger.info(f"开始生成 {count} 个测试用户...")
    
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        users = []
        for i in range(count):
            openid = f"test_openid_{i+1:04d}"
            unionid = f"test_unionid_{i+1:04d}"
            nickname = random.choice(NICKNAMES) + f"_{i+1}"
            mobile = f"1{random.choice(['38', '39', '50', '51', '52', '53', '55', '56', '57', '58', '59', '80', '81', '82', '83', '84', '85', '86', '87', '88', '89'])}{random.randint(10000000, 99999999)}"
            
            users.append((openid, unionid, nickname, mobile, 'active'))
        
        cursor.executemany("""
            INSERT IGNORE INTO users (openid, unionid, nickname, mobile, status)
            VALUES (%s, %s, %s, %s, %s)
        """, users)
        
        logger.info(f"成功插入 {cursor.rowcount} 个用户")
        
        # 统计
        cursor.execute("SELECT COUNT(*) as cnt FROM users")
        logger.info(f"users 表当前记录数: {cursor.fetchone()['cnt']}")
        
    finally:
        conn.close()


def generate_test_user_profiles(count: int = 20):
    """生成测试用户画像"""
    logger.info(f"开始生成 {count} 个测试用户画像...")
    
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # 获取所有用户
        cursor.execute("SELECT id FROM users ORDER BY id DESC LIMIT %s", (count,))
        user_ids = [row['id'] for row in cursor.fetchall()]
        
        # 获取部分专业作为目标专业
        cursor.execute("SELECT major_code, major_name FROM majors LIMIT 30")
        majors = cursor.fetchall()
        
        risk_prefs = ['conservative', 'balanced', 'aggressive']
        degree_types = ['academic', 'professional']
        study_modes = ['full_time', 'part_time']
        
        profiles = []
        for user_id in user_ids:
            target_major = random.choice(majors)
            exam_year = random.choice([2025, 2026, 2027])
            
            profile = (
                user_id,
                exam_year,
                random.choice(degree_types),
                random.choice(study_modes),
                target_major['major_code'],
                target_major['major_name'],
                random.randint(280, 400),  # 总分
                random.randint(40, 75),    # 政治
                random.randint(40, 80),    # 英语
                random.randint(80, 140),   # 科目一
                random.randint(80, 140),   # 科目二
                random.choice(UNDERGRAD_SCHOOLS),
                random.choice(NICKNAMES) + "专业",
                json.dumps(random.sample(PROVINCES, random.randint(1, 3)), ensure_ascii=False),
                json.dumps(random.sample(CITIES, random.randint(1, 2)), ensure_ascii=False),
                json.dumps(random.sample(SCHOOL_LEVELS, random.randint(1, 3)), ensure_ascii=False),
                random.choice(risk_prefs),
                f"目标{exam_year}年考研，希望上岸{random.choice(['985', '211', '双一流'])}院校"
            )
            profiles.append(profile)
        
        cursor.executemany("""
            INSERT INTO user_profiles (
                user_id, exam_year, target_degree_type, target_study_mode,
                target_major_code, target_major_name, score_total,
                politics_score, english_score, subject_one_score, subject_two_score,
                undergraduate_school, undergraduate_major, preferred_provinces,
                preferred_cities, preferred_school_levels, risk_preference, notes
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, profiles)
        
        logger.info(f"成功插入 {cursor.rowcount} 个用户画像")
        
        # 统计
        cursor.execute("SELECT COUNT(*) as cnt FROM user_profiles")
        logger.info(f"user_profiles 表当前记录数: {cursor.fetchone()['cnt']}")
        
    finally:
        conn.close()


def main():
    logger.info("=" * 50)
    logger.info("开始生成测试用户数据")
    logger.info("=" * 50)
    
    generate_test_users(20)
    generate_test_user_profiles(20)
    
    logger.info("=" * 50)
    logger.info("测试用户数据生成完成")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
