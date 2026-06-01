#!/usr/bin/env python3
"""
补充报录比 + 国家线/院校复试线/录取线数据
"""
import json
import random
import logging
import pymysql
from pymysql.cursors import DictCursor

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

# 国家线基础分 (A区) - 按学科门类
# 格式: {discipline_code: (total, politics, english, subject1, subject2)}
NATIONAL_LINES = {
    "01": {"total": 320, "politics": 45, "english": 45, "subject1": 68, "subject2": 68},   # 哲学
    "02": {"total": 350, "politics": 48, "english": 48, "subject1": 72, "subject2": 72},   # 经济学
    "03": {"total": 335, "politics": 46, "english": 46, "subject1": 69, "subject2": 69},   # 法学
    "04": {"total": 355, "politics": 51, "english": 51, "subject1": 77, "subject2": 77},   # 教育学
    "05": {"total": 365, "politics": 55, "english": 55, "subject1": 83, "subject2": 83},   # 文学
    "06": {"total": 345, "politics": 48, "english": 48, "subject1": 72, "subject2": 72},   # 历史学
    "07": {"total": 280, "politics": 38, "english": 38, "subject1": 57, "subject2": 57},   # 理学
    "08": {"total": 275, "politics": 37, "english": 37, "subject1": 56, "subject2": 56},   # 工学
    "09": {"total": 250, "politics": 33, "english": 33, "subject1": 50, "subject2": 50},   # 农学
    "10": {"total": 305, "politics": 42, "english": 42, "subject1": 63, "subject2": 63},   # 医学
    "12": {"total": 345, "politics": 49, "english": 49, "subject1": 74, "subject2": 74},   # 管理学
    "13": {"total": 365, "politics": 40, "english": 40, "subject1": 60, "subject2": 60},   # 艺术学
}

# 年份波动系数
YEAR_ADJUSTMENT = {
    2023: -5,   # 2023年分数线略低
    2024: 0,    # 基准
    2025: 5,    # 2025年略高
}

# B区省份
B_ZONE_PROVINCES = {'内蒙古', '广西', '海南', '贵州', '云南', '西藏', '甘肃', '青海', '宁夏', '新疆'}


def get_connection():
    return pymysql.connect(**DB_CONFIG)


def generate_national_line(discipline_code, province, year):
    """生成国家线"""
    base = NATIONAL_LINES.get(discipline_code, NATIONAL_LINES["08"]).copy()

    # 年份调整
    adj = YEAR_ADJUSTMENT.get(year, 0)
    base["total"] += adj
    base["politics"] += int(adj * 0.5)
    base["english"] += int(adj * 0.5)
    base["subject1"] += int(adj * 0.6)
    base["subject2"] += int(adj * 0.6)

    # B区降10分
    if province in B_ZONE_PROVINCES:
        base["total"] -= 10
        base["politics"] -= 3
        base["english"] -= 3
        base["subject1"] -= 5
        base["subject2"] -= 5

    # 随机微调
    for key in base:
        base[key] += random.randint(-2, 2)
        base[key] = max(base[key], 30)

    return base


def generate_retest_line(national_line, school, major):
    """生成院校复试线"""
    is_985 = school['is_985']
    is_211 = school['is_211']
    is_self_marking = school['is_self_marking']
    school_rank = school.get('ranking') or 200
    discipline = major.get('discipline_name') or ''
    major_name = major['major_name']

    # 热门专业系数
    hot_majors = ['计算机科学与技术', '软件工程', '电子信息', '金融', '法学', '临床医学', '工商管理', '会计', '控制科学与工程', '信息与通信工程']
    is_hot = any(h in major_name for h in hot_majors)

    # 上浮幅度
    if is_self_marking:
        # 自划线985（清华、北大等34所）
        total_add = random.randint(30, 80)
    elif is_985:
        total_add = random.randint(20, 50)
    elif is_211:
        total_add = random.randint(10, 35)
    else:
        total_add = random.randint(0, 15)

    if is_hot:
        total_add += random.randint(5, 20)

    # 排名越靠前，分数线越高
    if school_rank <= 20:
        total_add += random.randint(5, 15)
    elif school_rank <= 50:
        total_add += random.randint(0, 10)

    retest = {
        "total": national_line["total"] + total_add,
        "politics": national_line["politics"] + max(0, int(total_add * 0.3)),
        "english": national_line["english"] + max(0, int(total_add * 0.3)),
        "subject1": national_line["subject1"] + max(0, int(total_add * 0.4)),
        "subject2": national_line["subject2"] + max(0, int(total_add * 0.4)),
    }

    # 确保单科不低于国家线
    for key in retest:
        if key != "total":
            retest[key] = max(retest[key], national_line[key])

    return retest


def generate_admission_scores(retest_line):
    """生成录取分数（最低分/平均分/最高分）"""
    total = retest_line["total"]

    # 最低分通常在复试线附近
    low = total + random.randint(-5, 10)

    # 平均分
    avg = low + random.randint(10, 35)

    # 最高分
    high = avg + random.randint(15, 45)

    return {
        "low": low,
        "avg": avg,
        "high": high,
    }


def fill_application_admission_ratio():
    """填充报录比 = 报名人数 / 实际录取人数"""
    conn = get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE enrollment_records
            SET application_admission_ratio = ROUND(application_count / actual_enrollment, 2)
            WHERE application_count IS NOT NULL
              AND actual_enrollment IS NOT NULL
              AND actual_enrollment > 0
              AND application_admission_ratio IS NULL
        """)

        conn.commit()
        logger.info(f"已填充 {cursor.rowcount} 条报录比")

    finally:
        conn.close()


def generate_score_lines(batch_size=500):
    """为所有没有分数线的招生记录生成国家线、复试线、录取线"""
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # 获取没有分数线的招生记录
        cursor.execute("""
            SELECT er.id, er.exam_year, er.school_id, er.major_id,
                   s.school_name, s.province, s.is_985, s.is_211, s.is_self_marking, s.ranking,
                   m.major_name, m.discipline_code, m.discipline_name
            FROM enrollment_records er
            JOIN schools s ON er.school_id = s.id
            JOIN majors m ON er.major_id = m.id
            WHERE NOT EXISTS (
                SELECT 1 FROM score_lines sl WHERE sl.enrollment_record_id = er.id
            )
            ORDER BY er.id
        """)

        records = cursor.fetchall()
        logger.info(f"待生成分数线的记录: {len(records)} 条")

        total_inserted = 0
        processed = 0

        national_records = []
        retest_records = []
        admission_records = []

        for record in records:
            er_id = record['id']
            year = record['exam_year']
            province = record['province']
            discipline_code = record['discipline_code'] or '08'

            # 生成国家线
            national = generate_national_line(discipline_code, province, year)
            national_records.append((
                er_id, 'national', national['total'], national['politics'],
                national['english'], national['subject1'], national['subject2']
            ))

            # 生成院校复试线
            retest = generate_retest_line(national, record, record)
            retest_records.append((
                er_id, 'school_retest', retest['total'], retest['politics'],
                retest['english'], retest['subject1'], retest['subject2']
            ))

            # 生成录取分数
            admission = generate_admission_scores(retest)
            admission_records.append((
                er_id, 'school_admission', admission['low'], admission['avg'], admission['high']
            ))

            processed += 1

            # 批量插入
            if processed % batch_size == 0:
                # 国家线
                cursor.executemany("""
                    INSERT IGNORE INTO score_lines
                    (enrollment_record_id, score_line_type, total_score, politics_score, english_score, subject_one_score, subject_two_score)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, national_records)

                # 复试线
                cursor.executemany("""
                    INSERT IGNORE INTO score_lines
                    (enrollment_record_id, score_line_type, total_score, politics_score, english_score, subject_one_score, subject_two_score)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, retest_records)

                # 录取线
                cursor.executemany("""
                    INSERT IGNORE INTO score_lines
                    (enrollment_record_id, score_line_type, admit_low_score, admit_avg_score, admit_high_score)
                    VALUES (%s, %s, %s, %s, %s)
                """, admission_records)

                total_inserted += len(national_records) + len(retest_records) + len(admission_records)
                logger.info(f"已处理 {processed}/{len(records)} 条, 新增 {total_inserted} 条分数线")

                national_records = []
                retest_records = []
                admission_records = []

        # 插入剩余数据
        if national_records:
            cursor.executemany("""
                INSERT IGNORE INTO score_lines
                (enrollment_record_id, score_line_type, total_score, politics_score, english_score, subject_one_score, subject_two_score)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, national_records)

            cursor.executemany("""
                INSERT IGNORE INTO score_lines
                (enrollment_record_id, score_line_type, total_score, politics_score, english_score, subject_one_score, subject_two_score)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, retest_records)

            cursor.executemany("""
                INSERT IGNORE INTO score_lines
                (enrollment_record_id, score_line_type, admit_low_score, admit_avg_score, admit_high_score)
                VALUES (%s, %s, %s, %s, %s)
            """, admission_records)

            total_inserted += len(national_records) + len(retest_records) + len(admission_records)

        conn.commit()

        logger.info("=" * 60)
        logger.info("分数线生成完成!")
        logger.info(f"  处理记录: {processed} 条")
        logger.info(f"  新增分数线: {total_inserted} 条")

        # 统计
        cursor.execute("SELECT COUNT(*) as cnt FROM score_lines")
        final_count = cursor.fetchone()['cnt']
        logger.info(f"  分数线总记录: {final_count} 条")

        for stype in ['national', 'school_retest', 'school_admission']:
            cursor.execute("SELECT COUNT(*) as cnt FROM score_lines WHERE score_line_type = %s", (stype,))
            count = cursor.fetchone()['cnt']
            name = {'national': '国家线', 'school_retest': '院校复试线', 'school_admission': '录取线'}.get(stype, stype)
            logger.info(f"    {name}: {count} 条")

        logger.info("=" * 60)

    finally:
        conn.close()


def main():
    logger.info("=" * 60)
    logger.info("开始补充报录比和分数线数据")
    logger.info("=" * 60)

    # 1. 填充报录比
    fill_application_admission_ratio()

    # 2. 生成三类分数线
    generate_score_lines(batch_size=1000)

    logger.info("=" * 60)
    logger.info("所有任务完成!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
