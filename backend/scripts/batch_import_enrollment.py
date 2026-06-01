"""
批量导入招生信息工具
支持从Excel/CSV文件批量导入近三年招生数据
"""
import pymysql
import csv
import json
from typing import List, Dict
from datetime import datetime


DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': 'lwt18251X',
    'database': 'kaoyan_system_v2',
}


def import_enrollment_from_csv(file_path: str):
    """
    从CSV文件导入招生数据
    
    CSV格式要求:
    school_code,school_name,major_code,major_name,exam_year,degree_type,
    study_mode,department_name,planned_enrollment,actual_enrollment,
    application_count,retest_ratio,tuition_fee,exam_subjects
    """
    conn = pymysql.connect(**DB_CONFIG, charset='utf8mb4')
    cursor = conn.cursor()
    
    imported = 0
    skipped = 0
    errors = 0
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            try:
                # 获取school_id
                cursor.execute("""
                    SELECT id FROM schools 
                    WHERE school_code = %s AND status = 'active'
                """, (row['school_code'],))
                
                school_result = cursor.fetchone()
                if not school_result:
                    print(f"  [WARN] 未找到院校: {row['school_name']} ({row['school_code']})")
                    skipped += 1
                    continue
                
                school_id = school_result[0]
                
                # 获取major_id
                cursor.execute("""
                    SELECT id FROM majors 
                    WHERE major_code = %s AND is_active = 1
                """, (row['major_code'],))
                
                major_result = cursor.fetchone()
                if not major_result:
                    # 如果专业不存在，尝试插入一条临时记录
                    major_name = row.get('major_name', '')
                    cursor.execute("""
                        INSERT INTO majors (major_code, major_name, is_active)
                        VALUES (%s, %s, 1)
                    """, (row['major_code'], major_name))
                    major_id = cursor.lastrowid
                    print(f"  [INFO] 自动创建专业: {major_name} ({row['major_code']})")
                else:
                    major_id = major_result[0]
                
                # 检查是否已存在
                cursor.execute("""
                    SELECT id FROM enrollment_records 
                    WHERE school_id = %s AND major_id = %s AND exam_year = %s
                    AND department_name = %s
                """, (school_id, major_id, row['exam_year'], row.get('department_name', '')))
                
                existing_id = cursor.fetchone()
                
                if existing_id:
                    # 更新现有记录
                    cursor.execute("""
                        UPDATE enrollment_records SET
                            planned_enrollment = %s,
                            actual_enrollment = %s,
                            application_count = %s,
                            retest_ratio = %s,
                            tuition_fee = %s,
                            exam_subjects = %s,
                            data_source = 'CSV导入',
                            source_updated_at = %s
                        WHERE id = %s
                    """, (
                        int(row['planned_enrollment']) if row.get('planned_enrollment') else None,
                        int(row['actual_enrollment']) if row.get('actual_enrollment') else None,
                        int(row['application_count']) if row.get('application_count') else None,
                        float(row['retest_ratio']) if row.get('retest_ratio') else None,
                        float(row['tuition_fee']) if row.get('tuition_fee') else None,
                        json.dumps(row.get('exam_subjects', ''), ensure_ascii=False),
                        datetime.now(),
                        existing_id[0]
                    ))
                    imported += 1
                else:
                    # 插入新记录
                    cursor.execute("""
                        INSERT INTO enrollment_records (
                            school_id, major_id, exam_year, degree_type, study_mode,
                            department_name, planned_enrollment, actual_enrollment,
                            application_count, retest_ratio, tuition_fee,
                            exam_subjects, data_source, source_updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        school_id,
                        major_id,
                        int(row['exam_year']),
                        row.get('degree_type', 'academic'),
                        row.get('study_mode', 'full_time'),
                        row.get('department_name', ''),
                        int(row['planned_enrollment']) if row.get('planned_enrollment') else None,
                        int(row['actual_enrollment']) if row.get('actual_enrollment') else None,
                        int(row['application_count']) if row.get('application_count') else None,
                        float(row['retest_ratio']) if row.get('retest_ratio') else None,
                        float(row['tuition_fee']) if row.get('tuition_fee') else None,
                        json.dumps(row.get('exam_subjects', ''), ensure_ascii=False),
                        'CSV导入',
                        datetime.now()
                    ))
                    imported += 1
                
            except Exception as e:
                print(f"  [ERROR] 导入失败: {e}")
                errors += 1
                continue
    
    conn.commit()
    
    print(f"\n导入完成:")
    print(f"  成功: {imported} 条")
    print(f"  跳过: {skipped} 条")
    print(f"  错误: {errors} 条")
    
    conn.close()


def generate_sample_csv(file_path: str):
    """生成示例CSV文件"""
    sample_data = [
        {
            'school_code': '10001',
            'school_name': '北京大学',
            'major_code': '010100',
            'major_name': '哲学',
            'exam_year': 2025,
            'degree_type': 'academic',
            'study_mode': 'full_time',
            'department_name': '哲学系',
            'planned_enrollment': 15,
            'actual_enrollment': 12,
            'application_count': 120,
            'retest_ratio': 1.2,
            'tuition_fee': 8000,
            'exam_subjects': '政治,英语一,哲学基础,西方哲学史'
        },
        {
            'school_code': '10003',
            'school_name': '清华大学',
            'major_code': '081200',
            'major_name': '计算机科学与技术',
            'exam_year': 2025,
            'degree_type': 'academic',
            'study_mode': 'full_time',
            'department_name': '计算机科学与技术系',
            'planned_enrollment': 30,
            'actual_enrollment': 28,
            'application_count': 450,
            'retest_ratio': 1.5,
            'tuition_fee': 8000,
            'exam_subjects': '政治,英语一,数学一,计算机专业基础'
        },
    ]
    
    with open(file_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=sample_data[0].keys())
        writer.writeheader()
        writer.writerows(sample_data)
    
    print(f"✓ 示例CSV文件已生成: {file_path}")


def main():
    """主函数"""
    import sys
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  python batch_import_enrollment.py <csv文件路径>")
        print("  python batch_import_enrollment --sample  # 生成示例CSV")
        return
    
    if sys.argv[1] == '--sample':
        generate_sample_csv('sample_enrollment_data.csv')
    else:
        csv_file = sys.argv[1]
        import_enrollment_from_csv(csv_file)


if __name__ == "__main__":
    main()
