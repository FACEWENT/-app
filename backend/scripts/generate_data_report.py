#!/usr/bin/env python3
"""
生成考研系统数据质量报告
"""
import pymysql
import json
from datetime import datetime

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': 'lwt18251X',
    'database': 'kaoyan_system_v2',
}

def generate_report():
    """生成数据质量报告"""
    conn = pymysql.connect(**DB_CONFIG, charset='utf8mb4')
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    print("=" * 70)
    print("考研择校调剂系统 - 数据质量报告")
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # 1. 院校总体统计
    print("\n【一、院校数据】")
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(is_985) as count_985,
            SUM(is_211) as count_211,
            SUM(is_double_first_class) as count_double,
            COUNT(DISTINCT province) as province_count
        FROM schools WHERE status = 'active'
    """)
    stats = cursor.fetchone()
    print(f"  院校总数: {stats['total']} 所")
    print(f"  985院校: {stats['count_985']} 所")
    print(f"  211院校: {stats['count_211']} 所")
    print(f"  双一流: {stats['count_double']} 所")
    print(f"  覆盖省份: {stats['province_count']} 个")
    
    # 2. 省份分布 TOP 10
    print("\n  省份分布 TOP 10:")
    cursor.execute("""
        SELECT province, COUNT(*) as count 
        FROM schools WHERE status = 'active'
        GROUP BY province ORDER BY count DESC LIMIT 10
    """)
    for row in cursor.fetchall():
        bar = '█' * (row['count'] // 2)
        print(f"    {row['province']:8s} {row['count']:4d} 所 {bar}")
    
    # 3. 专业数据
    print("\n【二、专业数据】")
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(DISTINCT discipline_code) as discipline_count,
            COUNT(DISTINCT degree_type) as degree_types
        FROM majors WHERE is_active = 1
    """)
    stats = cursor.fetchone()
    print(f"  专业总数: {stats['total']} 个")
    print(f"  学科门类: {stats['discipline_count']} 个")
    print(f"  学位类型: {stats['degree_types']} 种")
    
    # 学科门类分布
    print("\n  学科门类分布:")
    cursor.execute("""
        SELECT discipline_code, discipline_name, COUNT(*) as count
        FROM majors WHERE is_active = 1 AND discipline_code IS NOT NULL
        GROUP BY discipline_code, discipline_name
        ORDER BY discipline_code
    """)
    for row in cursor.fetchall():
        bar = '█' * (row['count'] // 5)
        print(f"    {row['discipline_code']} {row['discipline_name']:8s} {row['count']:4d} 个专业 {bar}")
    
    # 4. 招生记录
    print("\n【三、招生数据】")
    cursor.execute("SELECT COUNT(*) as total FROM enrollment_records")
    stats = cursor.fetchone()
    print(f"  招生记录: {stats['total']} 条")
    
    cursor.execute("""
        SELECT exam_year, COUNT(*) as count
        FROM enrollment_records
        GROUP BY exam_year
        ORDER BY exam_year DESC
    """)
    for row in cursor.fetchall():
        print(f"    {row['exam_year']}年: {row['count']} 条")
    
    # 5. 分数线数据
    print("\n【四、分数线数据】")
    cursor.execute("SELECT COUNT(*) as total FROM score_lines")
    stats = cursor.fetchone()
    print(f"  分数线记录: {stats['total']} 条")
    
    cursor.execute("""
        SELECT score_line_type, COUNT(*) as count
        FROM score_lines
        GROUP BY score_line_type
    """)
    for row in cursor.fetchall():
        type_name = {
            'national_line': '国家线',
            'school_retest': '院校复试线',
            'school_admission': '院校录取线'
        }.get(row['score_line_type'], row['score_line_type'])
        print(f"    {type_name}: {row['count']} 条")
    
    # 6. 数据完整性检查
    print("\n【五、数据完整性检查】")
    
    # 检查缺失省份的院校
    cursor.execute("""
        SELECT COUNT(*) as count FROM schools 
        WHERE status = 'active' AND (province IS NULL OR province = '')
    """)
    missing_province = cursor.fetchone()['count']
    print(f"  缺失省份信息: {missing_province} 所 {'✓' if missing_province == 0 else '✗ 需要补充'}")
    
    # 检查缺失discipline_code的专业
    cursor.execute("""
        SELECT COUNT(*) as count FROM majors 
        WHERE is_active = 1 AND discipline_code IS NULL
    """)
    missing_discipline = cursor.fetchone()['count']
    print(f"  缺失学科门类: {missing_discipline} 个 {'✓' if missing_discipline == 0 else '✗ 需要补充'}")
    
    # 7. 数据来源说明
    print("\n【六、数据来源】")
    print("  - 院校列表: 研招网 (yz.chsi.com.cn)")
    print("  - 985/211标识: 官方公布名单")
    print("  - 专业目录: 研招网硕士招生专业目录")
    print("  - 分数线: 各院校研究生招生官网")
    print("  - 简介信息: 千问AI辅助生成")
    
    # 8. 建议
    print("\n【七、优化建议】")
    print("  1. 继续爬取各专业详细招生信息（考试科目、招生人数等）")
    print("  2. 补充近三年分数线数据")
    print("  3. 增加院校简介、专业介绍等文本内容")
    print("  4. 定期更新数据，保持时效性")
    
    print("\n" + "=" * 70)
    
    conn.close()

if __name__ == "__main__":
    generate_report()
