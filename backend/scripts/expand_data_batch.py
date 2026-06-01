"""
批量爬取考研院校和专业数据
目标:
1. 扩充学校数据到800+所(覆盖全国所有具有研究生招生资格的高校)
2. 扩充专业数据到500+个
3. 扩充学校-专业关联
4. 扩充招生记录和分数线数据(2023-2025年)
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

# ==================== 配置 ====================
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
    """初始化千问 API"""
    if not HAS_DASHSCOPE:
        logger.error("请先安装 dashscope: pip install dashscope")
        return False
    
    dashscope.api_key = DASHSCOPE_API_KEY
    return True


def call_qwen(prompt: str, system_prompt: str = None, max_retries: int = 3) -> Optional[str]:
    """调用千问大模型"""
    if not HAS_DASHSCOPE:
        return None
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
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
                time.sleep(2 ** attempt)
                
        except Exception as e:
            logger.warning(f"API 调用异常 (attempt {attempt + 1}): {e}")
            time.sleep(2 ** attempt)
    
    return None


def parse_json_from_response(response: str) -> Optional[dict]:
    """从千问的回复中提取 JSON 数据"""
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass
    
    match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    
    match = re.search(r'```\s*(.*?)\s*```', response, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    
    start = response.find('{')
    end = response.rfind('}')
    if start != -1 and end != -1:
        try:
            return json.loads(response[start:end+1])
        except json.JSONDecodeError:
            pass
    
    logger.warning(f"无法从回复中解析 JSON: {response[:200]}...")
    return None


def parse_json_array(response: str) -> Optional[list]:
    """从回复中解析 JSON 数组"""
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass
    
    match = re.search(r'```json\s*(\[.*?\])\s*```', response, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    
    start = response.find('[')
    end = response.rfind(']')
    if start != -1 and end != -1:
        try:
            return json.loads(response[start:end+1])
        except json.JSONDecodeError:
            pass
    
    return None


def get_connection():
    return pymysql.connect(**DB_CONFIG)


# ==================== 1. 批量扩充学校数据 ====================
def expand_schools():
    """使用千问批量生成全国研究生招生院校数据"""
    logger.info("开始扩充学校数据...")
    
    if not init_dashscope():
        return
    
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # 获取已有的学校名称
        cursor.execute("SELECT school_name FROM schools")
        existing_schools = {row['school_name'] for row in cursor.fetchall()}
        logger.info(f"已有学校: {len(existing_schools)} 所")
        
        # 按省份分批生成学校
        provinces = [
            "北京", "天津", "上海", "重庆",  # 直辖市
            "河北", "河南", "山东", "山西",  # 华北
            "辽宁", "吉林", "黑龙江",  # 东北
            "江苏", "浙江", "安徽", "福建", "江西",  # 华东
            "湖北", "湖南", "广东", "海南",  # 华中华南
            "四川", "贵州", "云南", "广西",  # 西南
            "陕西", "甘肃", "青海", "宁夏", "新疆",  # 西北
            "内蒙古", "西藏",  # 自治区
        ]
        
        total_added = 0
        
        for province in provinces:
            # 检查该省份已有多少学校
            cursor.execute("SELECT COUNT(*) as cnt FROM schools WHERE province = %s", (province,))
            existing_count = cursor.fetchone()['cnt']
            
            # 如果该省份学校数量已经较多,跳过
            if existing_count > 50:
                logger.info(f"{province}: 已有{existing_count}所学校,跳过")
                continue
            
            logger.info(f"正在生成 {province} 省研究生招生院校...")
            
            prompt = f"""请列出{province}省所有具有硕士研究生招生资格的院校(包括985/211/双一流/普通院校)。

请以 JSON 数组格式返回,每所学校包含以下字段:
- school_name: 学校名称
- school_code: 学校代码(5位数字)
- city: 所在城市
- is_985: 是否985(0或1)
- is_211: 是否211(0或1)
- is_double_first_class: 是否双一流(0或1)
- is_self_marking: 是否自划线(0或1)
- school_type: 学校类型(综合/理工/师范/农林/医药/财经/政法/艺术/体育/民族/军事等)
- ranking: 全国排名(如果有的话)
- intro: 学校简介(50字以内)
- website: 学校官网URL
- graduate_website: 研究生院官网URL

注意:
1. 只返回 JSON 数组,不要有其他内容
2. 排除以下已存在的学校: {', '.join(list(existing_schools)[:20])}
3. 学校代码必须是5位数字
4. 数据要准确"""
            
            response = call_qwen(prompt)
            if response:
                schools_data = parse_json_array(response)
                if schools_data:
                    schools_to_insert = []
                    for school in schools_data:
                        if school.get('school_name') and school['school_name'] not in existing_schools:
                            schools_to_insert.append((
                                school.get('school_code'),
                                school['school_name'],
                                province,
                                school.get('city', ''),
                                school.get('school_type'),
                                school.get('is_985', 0),
                                school.get('is_211', 0),
                                school.get('is_double_first_class', 0),
                                school.get('is_self_marking', 0),
                                school.get('ranking'),
                                school.get('intro'),
                                school.get('website'),
                                school.get('graduate_website'),
                            ))
                    
                    if schools_to_insert:
                        cursor.executemany("""
                            INSERT IGNORE INTO schools (
                                school_code, school_name, province, city, school_type,
                                is_985, is_211, is_double_first_class, is_self_marking,
                                ranking, intro, website, graduate_website
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, schools_to_insert)
                        
                        added = cursor.rowcount
                        total_added += added
                        logger.info(f"{province}: 新增 {added} 所学校")
                        existing_schools.update([s[1] for s in schools_to_insert])
            
            # 避免 API 调用频率限制
            time.sleep(2)
        
        logger.info(f"共新增 {total_added} 所学校")
        
        # 统计
        cursor.execute("SELECT COUNT(*) as cnt FROM schools")
        logger.info(f"schools 表当前记录数: {cursor.fetchone()['cnt']}")
        
    finally:
        conn.close()


# ==================== 2. 扩充专业数据 ====================
def expand_majors():
    """使用千问扩充硕士专业数据"""
    logger.info("开始扩充专业数据...")
    
    if not init_dashscope():
        return
    
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # 获取已有专业
        cursor.execute("SELECT major_code, major_name FROM majors")
        existing_majors = {row['major_name'] for row in cursor.fetchall()}
        logger.info(f"已有专业: {len(existing_majors)} 个")
        
        # 学科门类
        disciplines = [
            ("01", "哲学"),
            ("02", "经济学"),
            ("03", "法学"),
            ("04", "教育学"),
            ("05", "文学"),
            ("06", "历史学"),
            ("07", "理学"),
            ("08", "工学"),
            ("09", "农学"),
            ("10", "医学"),
            ("11", "军事学"),
            ("12", "管理学"),
            ("13", "艺术学"),
            ("14", "交叉学科"),
        ]
        
        total_added = 0
        
        for disc_code, disc_name in disciplines:
            logger.info(f"正在生成 {disc_name} 门类下的硕士专业...")
            
            prompt = f"""请列出中国硕士研究生招生中{disc_name}门类(代码{disc_code})下的所有一级学科和专业。

包括:
1. 学术型硕士专业(代码以{disc_code}开头)
2. 专业型硕士专业(如果有)

请以 JSON 数组格式返回,每个专业包含:
- major_code: 专业代码(6位数字)
- major_name: 专业名称
- degree_type: academic(学硕)或professional(专硕)
- major_category_name: 一级学科名称

注意:
1. 只返回 JSON 数组,不要有其他内容
2. 排除已存在的专业: {', '.join(list(existing_majors)[:30])}
3. 专业代码必须是6位数字
4. 学硕专业代码前4位是一级学科代码"""
            
            response = call_qwen(prompt)
            if response:
                majors_data = parse_json_array(response)
                if majors_data:
                    majors_to_insert = []
                    for major in majors_data:
                        if major.get('major_name') and major['major_name'] not in existing_majors:
                            majors_to_insert.append((
                                major.get('major_code'),
                                major['major_name'],
                                major.get('degree_type', 'academic'),
                                disc_code,
                                disc_name,
                                major.get('major_category_name'),
                            ))
                    
                    if majors_to_insert:
                        cursor.executemany("""
                            INSERT IGNORE INTO majors (
                                major_code, major_name, degree_type,
                                discipline_code, discipline_name, major_category_name
                            ) VALUES (%s, %s, %s, %s, %s, %s)
                        """, majors_to_insert)
                        
                        added = cursor.rowcount
                        total_added += added
                        logger.info(f"{disc_name}: 新增 {added} 个专业")
                        existing_majors.update([m[1] for m in majors_to_insert])
            
            time.sleep(2)
        
        logger.info(f"共新增 {total_added} 个专业")
        
        cursor.execute("SELECT COUNT(*) as cnt FROM majors")
        logger.info(f"majors 表当前记录数: {cursor.fetchone()['cnt']}")
        
    finally:
        conn.close()


# ==================== 3. 扩充学校-专业关联 ====================
def expand_school_majors(batch_size: int = 50):
    """使用千问扩充学校-专业关联数据"""
    logger.info("开始扩充学校-专业关联...")
    
    if not init_dashscope():
        return
    
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # 获取没有关联专业或关联较少的学校
        cursor.execute("""
            SELECT s.id, s.school_name
            FROM schools s
            LEFT JOIN school_majors sm ON s.id = sm.school_id
            GROUP BY s.id, s.school_name
            HAVING COUNT(sm.major_id) < 10
            ORDER BY s.ranking
            LIMIT 200
        """)
        schools = cursor.fetchall()
        
        # 获取所有专业
        cursor.execute("SELECT id, major_code, major_name, degree_type FROM majors")
        majors = cursor.fetchall()
        major_map = {m['major_name']: m['id'] for m in majors}
        major_names = [m['major_name'] for m in majors]
        
        logger.info(f"待处理学校: {len(schools)} 所, 专业总数: {len(majors)} 个")
        
        total_added = 0
        
        for school in schools:
            school_name = school['school_name']
            school_id = school['id']
            
            # 只选取相关专业类别
            prompt = f"""请列出{school_name}硕士研究生招生的主要专业(30-50个)。

从以下专业中选择该校实际招生的专业:
{', '.join(major_names[:200])}

请以 JSON 数组格式返回专业名称列表,例如:
["专业名称1", "专业名称2", ...]

注意:
1. 只返回 JSON 数组
2. 专业名称必须与上述列表完全匹配
3. 选择该校的优势专业和主要招生专业"""
            
            response = call_qwen(prompt)
            if response:
                major_list = parse_json_array(response)
                if major_list and isinstance(major_list, list):
                    relations = []
                    for major_name in major_list:
                        if major_name in major_map:
                            relations.append((school_id, major_map[major_name], 1))
                    
                    if relations:
                        cursor.executemany("""
                            INSERT IGNORE INTO school_majors (school_id, major_id, is_active)
                            VALUES (%s, %s, %s)
                        """, relations)
                        total_added += len(relations)
                        logger.info(f"{school_name}: 关联 {len(relations)} 个专业")
            
            time.sleep(1.5)
        
        logger.info(f"共新增 {total_added} 条学校-专业关联")
        
        cursor.execute("SELECT COUNT(*) as cnt FROM school_majors")
        logger.info(f"school_majors 表当前记录数: {cursor.fetchone()['cnt']}")
        
    finally:
        conn.close()


# ==================== 4. 批量生成招生数据 ====================
def expand_enrollment_data(years: list = None, batch_size: int = 20):
    """批量生成招生数据"""
    if years is None:
        years = [2023, 2024, 2025]
    
    logger.info(f"开始批量生成招生数据(年份: {years})...")
    
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
            LIMIT 1000
        """)
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
        
        for school_id, school_data in list(school_groups.items())[:100]:  # 处理前100所学校
            school_name = school_data['school_name']
            majors = school_data['majors']
            
            # 每次处理15个专业
            for major_batch in [majors[i:i+15] for i in range(0, len(majors), 15)]:
                major_info = "\n".join([
                    f"- {m['major_name']}({m['degree_type']})" for m in major_batch
                ])
                
                for year in years:
                    # 检查是否已存在
                    existing_ids = []
                    for m in major_batch:
                        cursor.execute("""
                            SELECT id FROM enrollment_records
                            WHERE school_id = %s AND major_id = %s AND exam_year = %s
                        """, (school_id, m['major_id'], year))
                        if cursor.fetchone():
                            existing_ids.append(m['major_id'])
                    
                    if len(existing_ids) == len(major_batch):
                        continue
                    
                    prompt = f"""请提供{school_name}{year}年硕士研究生以下专业的招生数据:

{major_info}

请提供以下信息:
1. department_name: 招生院系
2. planned_enrollment: 计划招生人数
3. actual_enrollment: 实际录取人数
4. recommended_exemption_count: 推免人数
5. application_count: 报名人数(估计)
6. tuition_fee: 学费(元/年)
7. academic_system: 学制(如"3年"、"2年")

请以 JSON 格式返回:
{{
  "专业名称": {{
    "department_name": "院系名称",
    "planned_enrollment": 数字,
    "actual_enrollment": 数字,
    "recommended_exemption_count": 数字,
    "application_count": 数字,
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
                        enrollment_data = parse_json_from_response(response)
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
                    
                    time.sleep(1)
            
            time.sleep(1)
        
        logger.info(f"共新增 {total_added} 条招生记录")
        
        cursor.execute("SELECT COUNT(*) as cnt FROM enrollment_records")
        logger.info(f"enrollment_records 表当前记录数: {cursor.fetchone()['cnt']}")
        
    finally:
        conn.close()


# ==================== 5. 批量生成分数线数据 ====================
def expand_score_lines(years: list = None):
    """批量生成分数线数据"""
    if years is None:
        years = [2023, 2024, 2025]
    
    logger.info(f"开始批量生成分数线数据(年份: {years})...")
    
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
            LIMIT 500
        """.format(','.join(map(str, years))))
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
2. 分数要合理"""
                
                response = call_qwen(prompt)
                if response:
                    score_data = parse_json_from_response(response)
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
                
                time.sleep(2)
        
        logger.info(f"共新增 {total_added} 条分数线记录")
        
        cursor.execute("SELECT COUNT(*) as cnt FROM score_lines")
        logger.info(f"score_lines 表当前记录数: {cursor.fetchone()['cnt']}")
        
    finally:
        conn.close()


# ==================== 主函数 ====================
def main():
    """按顺序执行所有数据扩充任务"""
    logger.info("=" * 60)
    logger.info("开始批量扩充考研数据")
    logger.info("=" * 60)
    
    if DASHSCOPE_API_KEY == "YOUR_API_KEY_HERE":
        logger.warning("请先配置 DASHSCOPE_API_KEY")
        return
    
    # 1. 扩充学校数据
    expand_schools()
    
    # 2. 扩充专业数据
    expand_majors()
    
    # 3. 扩充学校-专业关联
    expand_school_majors()
    
    # 4. 扩充招生数据
    expand_enrollment_data(years=[2023, 2024, 2025])
    
    # 5. 扩充分数线数据
    expand_score_lines(years=[2023, 2024, 2025])
    
    logger.info("=" * 60)
    logger.info("数据扩充任务完成")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
