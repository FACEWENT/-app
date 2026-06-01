"""
考研数据抓取和填充工具
用于填充 school_tags, school_majors, enrollment_records, score_lines 表
"""
import json
import time
import logging
import pymysql
from pymysql.cursors import DictCursor
from typing import Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== 数据库配置 ====================
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


# ==================== 1. 填充 school_tags ====================
def fill_school_tags():
    """基于 schools 表已有的 985/211/双一流 等字段自动生成标签"""
    logger.info("开始填充 school_tags 表...")
    
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # 获取所有学校
        cursor.execute("""
            SELECT id, school_name, is_985, is_211, is_double_first_class, 
                   is_self_marking, province, city
            FROM schools
        """)
        schools = cursor.fetchall()
        
        tags_to_insert = []
        
        for school in schools:
            school_id = school['id']
            
            # 基于字段生成系统标签
            if school['is_985']:
                tags_to_insert.append((school_id, '985工程', 'system'))
            if school['is_211']:
                tags_to_insert.append((school_id, '211工程', 'system'))
            if school['is_double_first_class']:
                tags_to_insert.append((school_id, '双一流', 'system'))
            if school['is_self_marking']:
                tags_to_insert.append((school_id, '自划线', 'system'))
            
            # 基于城市生成区位标签
            if school['city'] in ['北京市', '上海市']:
                tags_to_insert.append((school_id, '一线城市', 'system'))
            elif school['city'] in ['广州市', '深圳市', '杭州市', '南京市', 
                                    '成都市', '武汉市', '重庆市', '天津市']:
                tags_to_insert.append((school_id, '新一线城市', 'system'))
            
            # 基于学校类型生成标签（如果有学校类型字段）
            if school.get('school_type'):
                tags_to_insert.append((school_id, school['school_type'], 'system'))
        
        # 批量插入
        if tags_to_insert:
            cursor.executemany("""
                INSERT IGNORE INTO school_tags (school_id, tag_name, tag_type)
                VALUES (%s, %s, %s)
            """, tags_to_insert)
            
            logger.info(f"成功插入 {cursor.rowcount} 条标签记录")
        
        # 统计
        cursor.execute("SELECT COUNT(*) as cnt FROM school_tags")
        logger.info(f"school_tags 表当前记录数: {cursor.fetchone()['cnt']}")
        
    finally:
        conn.close()


# ==================== 2. 填充 school_majors ====================
def fill_school_majors():
    """建立学校与专业的关联关系"""
    logger.info("开始填充 school_majors 表...")
    
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # 获取所有学校和所有专业
        cursor.execute("SELECT id FROM schools")
        school_ids = [row['id'] for row in cursor.fetchall()]
        
        cursor.execute("SELECT id FROM majors")
        major_ids = [row['id'] for row in cursor.fetchall()]
        
        logger.info(f"共 {len(school_ids)} 所学校, {len(major_ids)} 个专业")
        
        # 这里使用规则匹配：前100名学校开设所有工科专业，其他学校开设部分专业
        # 实际应用中应该从网上抓取真实的学校-专业对应关系
        relations = []
        
        for school_id in school_ids:
            # 简单规则：根据学校排名决定开设专业的范围
            cursor.execute("SELECT ranking FROM schools WHERE id = %s", (school_id,))
            ranking = cursor.fetchone()['ranking']
            
            if ranking <= 100:
                # 前100名学校，开设大部分专业
                for major_id in major_ids:
                    relations.append((school_id, major_id, 1))
            else:
                # 其他学校，开设部分专业
                for major_id in major_ids[:50]:  # 只开设前50个专业
                    relations.append((school_id, major_id, 1))
        
        # 批量插入
        if relations:
            cursor.executemany("""
                INSERT IGNORE INTO school_majors (school_id, major_id, is_active)
                VALUES (%s, %s, %s)
            """, relations)
            
            logger.info(f"成功插入 {cursor.rowcount} 条学校-专业关系")
        
        # 统计
        cursor.execute("SELECT COUNT(*) as cnt FROM school_majors")
        logger.info(f"school_majors 表当前记录数: {cursor.fetchone()['cnt']}")
        
    finally:
        conn.close()


# ==================== 3. 填充 enrollment_records (核心数据) ====================

def generate_mock_enrollment_data(school_id: int, major_id: int, exam_year: int, 
                                   school_name: str, major_name: str) -> dict:
    """
    生成模拟的招生数据
    实际应用中应该从研招网或各院校官网抓取真实数据
    """
    import random
    
    # 根据学校排名和专业热门程度生成合理的数据范围
    base_data = {
        'school_id': school_id,
        'major_id': major_id,
        'exam_year': exam_year,
        'degree_type': 'academic' if int(major_id) <= 35 else 'professional',
        'study_mode': 'full_time',
        'department_name': f'{school_name}研究生院',
        'planned_enrollment': random.randint(5, 50),
        'actual_enrollment': random.randint(5, 55),
        'recommended_exemption_count': random.randint(0, 15),
        'application_count': random.randint(50, 500),
        'tuition_fee': round(random.uniform(8000, 30000), 2),
        'academic_system': random.choice(['2年', '2.5年', '3年']),
    }
    
    # 计算报录比
    if base_data['application_count'] and base_data['actual_enrollment']:
        base_data['application_admission_ratio'] = round(
            base_data['application_count'] / base_data['actual_enrollment'], 2
        )
    
    # 复试比
    base_data['retest_ratio'] = round(random.uniform(1.2, 1.5), 2)
    
    return base_data


def fill_enrollment_records(years: list = None):
    """填充招生记录数据"""
    if years is None:
        years = [2024, 2025]  # 默认抓取最近两年数据
    
    logger.info(f"开始填充 enrollment_records 表，年份: {years}")
    
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # 获取所有学校
        cursor.execute("SELECT id, school_name, ranking FROM schools ORDER BY ranking")
        schools = cursor.fetchall()
        
        # 获取所有专业
        cursor.execute("SELECT id, major_name FROM majors")
        majors = cursor.fetchall()
        
        total_inserted = 0
        
        for year in years:
            for school in schools:
                # 只处理前50名学校的部分专业（避免数据量过大）
                if school['ranking'] > 50:
                    continue
                    
                for major in majors[:20]:  # 每个学校只处理前20个专业
                    record = generate_mock_enrollment_data(
                        school['id'], major['id'], year,
                        school['school_name'], major['major_name']
                    )
                    
                    try:
                        cursor.execute("""
                            INSERT IGNORE INTO enrollment_records (
                                school_id, major_id, exam_year, degree_type, study_mode,
                                department_name, planned_enrollment, actual_enrollment,
                                recommended_exemption_count, application_count,
                                application_admission_ratio, retest_ratio,
                                tuition_fee, academic_system
                            ) VALUES (
                                %(school_id)s, %(major_id)s, %(exam_year)s, 
                                %(degree_type)s, %(study_mode)s, %(department_name)s,
                                %(planned_enrollment)s, %(actual_enrollment)s,
                                %(recommended_exemption_count)s, %(application_count)s,
                                %(application_admission_ratio)s, %(retest_ratio)s,
                                %(tuition_fee)s, %(academic_system)s
                            )
                        """, record)
                        total_inserted += 1
                    except Exception as e:
                        logger.warning(f"插入失败: {school['school_name']} - {major['major_name']}, {e}")
                
                # 每处理10所学校暂停一下
                if school['id'] % 10 == 0:
                    time.sleep(0.1)
        
        logger.info(f"成功插入 {total_inserted} 条招生记录")
        
        # 统计
        cursor.execute("SELECT COUNT(*) as cnt FROM enrollment_records")
        logger.info(f"enrollment_records 表当前记录数: {cursor.fetchone()['cnt']}")
        
    finally:
        conn.close()


# ==================== 4. 填充 score_lines ====================
def fill_score_lines():
    """填充分数线数据"""
    logger.info("开始填充 score_lines 表...")
    
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        import random
        
        # 获取所有招生记录
        cursor.execute("""
            SELECT id, exam_year, degree_type 
            FROM enrollment_records
        """)
        records = cursor.fetchall()
        
        score_lines_data = []
        
        for record in records:
            er_id = record['id']
            exam_year = record['exam_year']
            
            # 国家线基础数据（不同年份和专业有所不同）
            if exam_year == 2025:
                # 2025年工学国家线（A区）
                national_total = 273
                national_single = 37
            else:
                # 2024年工学国家线（A区）
                national_total = 273
                national_single = 37
            
            # 1. 国家线
            score_lines_data.append((
                er_id, 'national',
                national_total, national_single, national_single,
                national_single, national_single, None
            ))
            
            # 2. 院校复试线（通常高于国家线）
            school_retest_total = national_total + random.randint(10, 80)
            score_lines_data.append((
                er_id, 'school_retest',
                school_retest_total,
                national_single + random.randint(0, 10),
                national_single + random.randint(0, 10),
                national_single + random.randint(0, 10),
                national_single + random.randint(0, 10), None
            ))
            
            # 3. 录取分数（通常高于复试线）
            admit_low = school_retest_total + random.randint(5, 30)
            score_lines_data.append((
                er_id, 'school_admission',
                None, None, None, None, None,
                admit_low,
                admit_low + random.randint(10, 40),
                admit_low + random.randint(50, 100)
            ))
        
        # 批量插入
        if score_lines_data:
            cursor.executemany("""
                INSERT INTO score_lines (
                    enrollment_record_id, score_line_type,
                    total_score, politics_score, english_score,
                    subject_one_score, subject_two_score,
                    admit_low_score, admit_avg_score, admit_high_score
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, score_lines_data)
            
            logger.info(f"成功插入 {cursor.rowcount} 条分数线记录")
        
        # 统计
        cursor.execute("SELECT COUNT(*) as cnt FROM score_lines")
        logger.info(f"score_lines 表当前记录数: {cursor.fetchone()['cnt']}")
        
    finally:
        conn.close()


# ==================== 主函数 ====================
def main():
    """按顺序执行所有数据填充任务"""
    logger.info("=" * 50)
    logger.info("开始数据填充任务")
    logger.info("=" * 50)
    
    # 1. 填充 school_tags
    fill_school_tags()
    
    # 2. 填充 school_majors
    fill_school_majors()
    
    # 3. 填充 enrollment_records
    fill_enrollment_records()
    
    # 4. 填充 score_lines
    fill_score_lines()
    
    logger.info("=" * 50)
    logger.info("数据填充任务完成")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
