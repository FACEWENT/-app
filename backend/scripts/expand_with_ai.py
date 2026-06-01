"""
使用千问AI扩充考研数据
目标:
1. 扩充学校-专业关联数据
2. 扩充招生数据(2023-2025年)
3. 扩充分数线数据
"""
import json
import time
import logging
import re
from typing import Optional
import pymysql
from pymysql.cursors import DictCursor

try:
    import dashscope
    from dashscope import Generation
    HAS_DASHSCOPE = True
except ImportError:
    HAS_DASHSCOPE = False
    print("注意: 未安装 dashscope 库，请运行: pip install dashscope")

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

DASHSCOPE_API_KEY = "sk-4a5d8e6280a1441791ea4a723de0ffda"
MODEL_NAME = "qwen-plus"


def init_dashscope():
    if not HAS_DASHSCOPE:
        logger.error("请先安装 dashscope: pip install dashscope")
        return False
    dashscope.api_key = DASHSCOPE_API_KEY
    return True


def call_qwen(prompt: str, max_retries: int = 3) -> Optional[str]:
    if not HAS_DASHSCOPE:
        return None
    
    messages = [{"role": "user", "content": prompt}]
    
    for attempt in range(max_retries):
        try:
            response = Generation.call(
                model=MODEL_NAME,
                messages=messages,
                result_format='message',
                temperature=0.3,
            )
            
            if response.status_code == 200:
                return response.output.choices[0].message.content
            else:
                logger.warning(f"API 调用失败 (attempt {attempt + 1}): {response.code} - {response.message}")
                if 'Arrearage' in str(response.code):
                    return None
                time.sleep(2 ** attempt)
                
        except Exception as e:
            logger.warning(f"API 调用异常 (attempt {attempt + 1}): {e}")
            time.sleep(2 ** attempt)
    
    return None


def parse_json(response: str):
    try:
        return json.loads(response)
    except:
        pass
    
    import re
    match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except:
            pass
    
    match = re.search(r'```\s*(\[.*?\])\s*```', response, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except:
            pass
    
    start = response.find('{')
    end = response.rfind('}')
    if start != -1 and end != -1:
        try:
            return json.loads(response[start:end+1])
        except:
            pass
    
    start = response.find('[')
    end = response.rfind(']')
    if start != -1 and end != -1:
        try:
            return json.loads(response[start:end+1])
        except:
            pass
    
    return None


def get_connection():
    return pymysql.connect(**DB_CONFIG)


def expand_school_majors_with_ai(limit: int = 100):
    """使用AI扩充学校-专业关联"""
    logger.info(f"开始使用AI扩充学校-专业关联(处理前{limit}所学校)...")
    
    if not init_dashscope():
        return
    
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # 获取专业关联较少的学校
        cursor.execute("""
            SELECT s.id, s.school_name, s.province, s.school_type
            FROM schools s
            LEFT JOIN school_majors sm ON s.id = sm.school_id
            GROUP BY s.id, s.school_name, s.province, s.school_type
            HAVING COUNT(sm.major_id) < 15
            ORDER BY s.ranking
            LIMIT %s
        """, (limit,))
        schools = cursor.fetchall()
        
        # 获取所有专业
        cursor.execute("SELECT id, major_code, major_name, degree_type, discipline_name FROM majors")
        majors = cursor.fetchall()
        major_map = {m['major_name']: m for m in majors}
        
        logger.info(f"待处理学校: {len(schools)} 所, 专业总数: {len(majors)} 个")
        
        total_added = 0
        
        for school in schools:
            school_name = school['school_name']
            school_id = school['id']
            province = school['province']
            school_type = school['school_type']
            
            # 根据学校类型筛选相关专业
            related_majors = []
            for m in majors:
                disc = m['discipline_name'] or ''
                # 理工类学校主要招理工专业
                if school_type == '理工' and disc in ['工学', '理学']:
                    related_majors.append(m)
                # 师范类学校主要招师范相关专业
                elif school_type == '师范' and disc in ['教育学', '文学', '理学']:
                    related_majors.append(m)
                # 医药类学校主要招医学专业
                elif school_type == '医药' and disc in ['医学']:
                    related_majors.append(m)
                # 农林类学校主要招农林专业
                elif school_type == '农林' and disc in ['农学']:
                    related_majors.append(m)
                # 财经类学校主要招经济管理专业
                elif school_type == '财经' and disc in ['经济学', '管理学']:
                    related_majors.append(m)
                # 综合类学校专业较多
                elif school_type == '综合':
                    related_majors.append(m)
                # 其他类型也添加一些常见专业
                else:
                    if disc in ['工学', '管理学', '文学', '教育学']:
                        related_majors.append(m)
            
            # 如果筛选后的专业太多,取前150个
            if len(related_majors) > 150:
                related_majors = related_majors[:150]
            
            major_names = [m['major_name'] for m in related_majors]
            major_names_str = '、'.join(major_names[:100])  # 只取前100个名称
            
            prompt = f"""请列出{school_name}({province},{school_type})硕士研究生招生的主要专业(30-50个)。

从以下专业中选择该校实际招生的专业(返回专业名称即可):
{major_names_str}

请以 JSON 数组格式返回专业名称列表,例如:
["专业名称1", "专业名称2", "专业名称3"]

注意:
1. 只返回 JSON 数组,不要有其他内容
2. 选择30-50个该校的主要招生专业
3. 专业名称必须与上述列表中的名称完全匹配"""
            
            response = call_qwen(prompt)
            if response:
                major_list = parse_json(response)
                if major_list and isinstance(major_list, list):
                    relations = []
                    for major_name in major_list:
                        if major_name in major_map:
                            relations.append((school_id, major_map[major_name]['id'], 1))
                    
                    if relations:
                        cursor.executemany("""
                            INSERT IGNORE INTO school_majors (school_id, major_id, is_active)
                            VALUES (%s, %s, %s)
                        """, relations)
                        total_added += len(relations)
                        logger.info(f"{school_name}: 关联 {len(relations)} 个专业")
            
            time.sleep(1)  # 避免API调用频率限制
        
        logger.info(f"共新增 {total_added} 条学校-专业关联")
        
        cursor.execute("SELECT COUNT(*) as cnt FROM school_majors")
        logger.info(f"school_majors 表当前记录数: {cursor.fetchone()['cnt']}")
        
    finally:
        conn.close()


def expand_enrollment_with_ai(years: list = None, limit: int = 200):
    """使用AI扩充招生数据"""
    if years is None:
        years = [2024, 2025]
    
    logger.info(f"开始使用AI扩充招生数据(年份: {years}, 处理{limit}条关联)...")
    
    if not init_dashscope():
        return
    
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # 获取需要生成招生数据的学校-专业关联
        cursor.execute("""
            SELECT sm.school_id, sm.major_id, s.school_name, m.major_name, m.degree_type
            FROM school_majors sm
            JOIN schools s ON sm.school_id = s.id
            JOIN majors m ON sm.major_id = m.id
            WHERE sm.is_active = 1
            ORDER BY s.ranking
            LIMIT %s
        """, (limit,))
        relations = cursor.fetchall()
        
        logger.info(f"待处理学校-专业关联: {len(relations)} 条")
        
        # 按学校分组
        school_groups = {}
        for rel in relations:
            if rel['school_id'] not in school_groups:
                school_groups[rel['school_id']] = {
                    'school_name': rel['school_name'],
                    'majors': []
                }
            school_groups[rel['school_id']]['majors'].append(rel)
        
        total_added = 0
        
        for school_id, school_data in school_groups.items():
            school_name = school_data['school_name']
            majors = school_data['majors']
            
            # 每次处理10个专业
            for major_batch in [majors[i:i+10] for i in range(0, len(majors), 10)]:
                major_info = "\n".join([
                    f"- {m['major_name']}({m['degree_type']})" for m in major_batch
                ])
                
                for year in years:
                    prompt = f"""请提供{school_name}{year}年硕士研究生以下专业的招生数据:

{major_info}

请提供以下信息:
1. department_name: 招生院系
2. planned_enrollment: 计划招生人数
3. actual_enrollment: 实际录取人数  
4. recommended_exemption_count: 推免人数
5. tuition_fee: 学费(元/年)
6. academic_system: 学制(如"3年"、"2年")

请以 JSON 格式返回:
{{
  "专业名称": {{
    "department_name": "院系名称",
    "planned_enrollment": 数字,
    "actual_enrollment": 数字,
    "recommended_exemption_count": 数字,
    "tuition_fee": 数字,
    "academic_system": "学制"
  }}
}}

注意:
1. 只返回 JSON
2. 数据要合理,符合实际情况
3. 学费单位为元/年"""
                    
                    response = call_qwen(prompt)
                    if response:
                        enrollment_data = parse_json(response)
                        if enrollment_data:
                            records_to_insert = []
                            for major in major_batch:
                                if major['major_name'] in enrollment_data:
                                    data = enrollment_data[major['major_name']]
                                    app_count = data.get('application_count')
                                    act_count = data.get('actual_enrollment')
                                    ratio = round(app_count / act_count, 2) if app_count and act_count and act_count > 0 else None
                                    
                                    records_to_insert.append((
                                        school_id, major['major_id'], year, major['degree_type'],
                                        data.get('department_name'),
                                        data.get('planned_enrollment'),
                                        data.get('actual_enrollment'),
                                        data.get('recommended_exemption_count'),
                                        app_count,
                                        ratio,
                                        data.get('tuition_fee'),
                                        data.get('academic_system'),
                                    ))
                            
                            if records_to_insert:
                                cursor.executemany("""
                                    INSERT IGNORE INTO enrollment_records (
                                        school_id, major_id, exam_year, degree_type, study_mode,
                                        department_name, planned_enrollment, actual_enrollment,
                                        recommended_exemption_count, application_count,
                                        application_admission_ratio, tuition_fee, academic_system
                                    ) VALUES (%s, %s, %s, %s, 'full_time', %s, %s, %s, %s, %s, %s, %s, %s)
                                """, records_to_insert)
                                total_added += len(records_to_insert)
                                logger.info(f"{school_name}-{year}: 新增 {len(records_to_insert)} 条")
                    
                    time.sleep(1)
            
            time.sleep(0.5)
        
        logger.info(f"共新增 {total_added} 条招生记录")
        
        cursor.execute("SELECT COUNT(*) as cnt FROM enrollment_records")
        logger.info(f"enrollment_records 表当前记录数: {cursor.fetchone()['cnt']}")
        
    finally:
        conn.close()


def expand_score_lines_with_ai(years: list = None, limit: int = 300):
    """使用AI扩充分数线数据"""
    if years is None:
        years = [2024, 2025]
    
    logger.info(f"开始使用AI扩充分数线数据(年份: {years}, 处理{limit}条)...")
    
    if not init_dashscope():
        return
    
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # 获取没有分数线的招生记录
        cursor.execute("""
            SELECT er.id, er.exam_year, er.degree_type,
                   s.school_name, m.major_name
            FROM enrollment_records er
            JOIN schools s ON er.school_id = s.id
            JOIN majors m ON er.major_id = m.id
            WHERE er.exam_year IN ({})
            AND NOT EXISTS (
                SELECT 1 FROM score_lines sl WHERE sl.enrollment_record_id = er.id
            )
            LIMIT %s
        """.format(','.join(map(str, years))), (limit,))
        records = cursor.fetchall()
        
        logger.info(f"待生成分数线记录: {len(records)} 条")
        
        # 按学校-年份分组
        grouped = {}
        for record in records:
            key = (record['school_name'], record['exam_year'])
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(record)
        
        total_added = 0
        
        for (school_name, year), er_records in grouped.items():
            # 每次处理8个专业
            for batch in [er_records[i:i+8] for i in range(0, len(er_records), 8)]:
                major_list = "\n".join([
                    f"- ID {r['id']}: {r['major_name']}({r['degree_type']})" for r in batch
                ])
                
                prompt = f"""请提供{school_name}{year}年硕士研究生以下专业的分数线数据:

{major_list}

请提供:
1. national: 国家线(总分、政治、英语、业务课一、业务课二)
2. school_retest: 学校复试线(总分、政治、英语、业务课一、业务课二)  
3. admission: 录取分数(最低分、平均分、最高分)

JSON格式:
{{
  "记录ID": {{
    "national": {{"total": 数字, "politics": 数字, "english": 数字, "subject1": 数字, "subject2": 数字}},
    "school_retest": {{"total": 数字, "politics": 数字, "english": 数字, "subject1": 数字, "subject2": 数字}},
    "admission": {{"low": 数字, "avg": 数字, "high": 数字}}
  }}
}}

注意:
1. 只返回 JSON
2. 分数要合理,符合国家线和学校实际情况"""
                
                response = call_qwen(prompt)
                if response:
                    score_data = parse_json(response)
                    if score_data:
                        for er_id_str, scores in score_data.items():
                            try:
                                er_id = int(er_id_str)
                                
                                if 'national' in scores:
                                    n = scores['national']
                                    cursor.execute("""
                                        INSERT IGNORE INTO score_lines (
                                            enrollment_record_id, score_line_type,
                                            total_score, politics_score, english_score,
                                            subject_one_score, subject_two_score
                                        ) VALUES (%s, 'national', %s, %s, %s, %s, %s)
                                    """, (er_id, n.get('total'), n.get('politics'),
                                          n.get('english'), n.get('subject1'), n.get('subject2')))
                                    total_added += 1
                                
                                if 'school_retest' in scores:
                                    sr = scores['school_retest']
                                    cursor.execute("""
                                        INSERT IGNORE INTO score_lines (
                                            enrollment_record_id, score_line_type,
                                            total_score, politics_score, english_score,
                                            subject_one_score, subject_two_score
                                        ) VALUES (%s, 'school_retest', %s, %s, %s, %s, %s)
                                    """, (er_id, sr.get('total'), sr.get('politics'),
                                          sr.get('english'), sr.get('subject1'), sr.get('subject2')))
                                    total_added += 1
                                
                                if 'admission' in scores:
                                    a = scores['admission']
                                    cursor.execute("""
                                        INSERT IGNORE INTO score_lines (
                                            enrollment_record_id, score_line_type,
                                            admit_low_score, admit_avg_score, admit_high_score
                                        ) VALUES (%s, 'school_admission', %s, %s, %s)
                                    """, (er_id, a.get('low'), a.get('avg'), a.get('high')))
                                    total_added += 1
                                    
                            except (ValueError, Exception) as e:
                                logger.warning(f"处理失败 er_id={er_id_str}: {e}")
                
                time.sleep(1.5)
        
        logger.info(f"共新增 {total_added} 条分数线记录")
        
        cursor.execute("SELECT COUNT(*) as cnt FROM score_lines")
        logger.info(f"score_lines 表当前记录数: {cursor.fetchone()['cnt']}")
        
    finally:
        conn.close()


def main():
    logger.info("=" * 60)
    logger.info("开始使用千问AI扩充考研数据")
    logger.info("=" * 60)
    
    # 1. 扩充学校-专业关联
    expand_school_majors_with_ai(limit=80)
    
    # 2. 扩充招生数据
    expand_enrollment_with_ai(years=[2024, 2025], limit=300)
    
    # 3. 扩充分数线数据
    expand_score_lines_with_ai(years=[2024, 2025], limit=500)
    
    logger.info("=" * 60)
    logger.info("数据扩充任务完成")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
