"""
使用通义千问大模型抓取考研数据
支持抓取：学校标签、学校-专业关联、招生数据、分数线
"""
import json
import time
import logging
import re
import pymysql
from pymysql.cursors import DictCursor
from typing import Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

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

# 千问 API 配置 - 请替换为你的 API Key
DASHSCOPE_API_KEY = "sk-4a5d8e6280a1441791ea4a723de0ffda"

# 使用的模型
MODEL_NAME = "qwen-plus"  # 可选: qwen-turbo, qwen-plus, qwen-max


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
                temperature=0.3,  # 降低随机性，保证数据准确性
            )
            
            if response.status_code == 200:
                return response.output.choices[0].message.content
            else:
                logger.warning(f"API 调用失败 (attempt {attempt + 1}): {response.code} - {response.message}")
                time.sleep(2 ** attempt)  # 指数退避
                
        except Exception as e:
            logger.warning(f"API 调用异常 (attempt {attempt + 1}): {e}")
            time.sleep(2 ** attempt)
    
    return None


def parse_json_from_response(response: str) -> Optional[dict]:
    """从千问的回复中提取 JSON 数据"""
    # 尝试直接解析
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass
    
    # 尝试从 ```json ... ``` 中提取
    match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    
    # 尝试从 ``` ... ``` 中提取
    match = re.search(r'```\s*(.*?)\s*```', response, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    
    # 尝试找到第一个 { 和最后一个 }
    start = response.find('{')
    end = response.rfind('}')
    if start != -1 and end != -1:
        try:
            return json.loads(response[start:end+1])
        except json.JSONDecodeError:
            pass
    
    logger.warning(f"无法从回复中解析 JSON: {response[:200]}...")
    return None


# ==================== 数据库连接 ====================
def get_connection():
    return pymysql.connect(**DB_CONFIG)


# ==================== 1. 使用千问生成学校标签 ====================
def fill_school_tags_with_qwen(batch_size: int = 50):
    """使用千问为学校生成更丰富的标签"""
    logger.info("开始使用千问生成学校标签...")
    
    if not init_dashscope():
        return
    
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # 获取所有学校
        cursor.execute("""
            SELECT id, school_name, province, city, is_985, is_211, 
                   is_double_first_class, school_type, ranking
            FROM schools
            ORDER BY ranking
        """)
        schools = cursor.fetchall()
        
        # 分批处理
        for i in range(0, len(schools), batch_size):
            batch = schools[i:i + batch_size]
            
            # 构建 Prompt
            school_info = "\n".join([
                f"- {s['school_name']}（{s['province']} {s['city']}，"
                f"{'985' if s['is_985'] else ''}{'211' if s['is_211'] else ''}"
                f"{'双一流' if s['is_double_first_class'] else ''}，"
                f"排名{s['ranking']}）"
                for s in batch
            ])
            
            prompt = f"""请为以下学校生成3-5个标签，标签应反映学校的特色和优势。
可选标签类型包括：地理位置优势、学科特色、就业优势、科研实力、国际交流等。

学校列表：
{school_info}

请以 JSON 格式返回，格式如下：
{{
  "学校名称": ["标签1", "标签2", "标签3"],
  ...
}}

注意：
1. 只返回 JSON，不要有其他内容
2. 每个学校3-5个标签
3. 标签要简洁明了，2-6个字"""
            
            response = call_qwen(prompt)
            if response:
                tags_data = parse_json_from_response(response)
                if tags_data:
                    tags_to_insert = []
                    for school in batch:
                        school_name = school['school_name']
                        if school_name in tags_data:
                            for tag in tags_data[school_name]:
                                tags_to_insert.append((school['id'], tag, 'ai_generated'))
                    
                    if tags_to_insert:
                        cursor.executemany("""
                            INSERT IGNORE INTO school_tags (school_id, tag_name, tag_type)
                            VALUES (%s, %s, %s)
                        """, tags_to_insert)
                        logger.info(f"批次 {i//batch_size + 1}: 插入 {len(tags_to_insert)} 条标签")
            
            # 避免 API 调用频率限制
            time.sleep(1)
        
        # 统计
        cursor.execute("SELECT COUNT(*) as cnt FROM school_tags")
        logger.info(f"school_tags 表当前记录数: {cursor.fetchone()['cnt']}")
        
    finally:
        conn.close()


# ==================== 2. 使用千问抓取学校-专业关联 ====================
def fill_school_majors_with_qwen(school_limit: int = 30):
    """使用千问获取学校开设的专业"""
    logger.info(f"开始使用千问抓取学校-专业关联（前{school_limit}所学校）...")
    
    if not init_dashscope():
        return
    
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # 获取前 N 所学校
        cursor.execute("""
            SELECT id, school_name FROM schools 
            ORDER BY ranking LIMIT %s
        """, (school_limit,))
        schools = cursor.fetchall()
        
        # 获取所有专业
        cursor.execute("SELECT id, major_code, major_name FROM majors")
        majors = cursor.fetchall()
        major_map = {m['major_name']: m['id'] for m in majors}
        
        relations_inserted = 0
        
        for school in schools:
            school_name = school['school_name']
            school_id = school['id']
            
            # 构建 Prompt
            major_names = ", ".join([m['major_name'] for m in majors])
            
            prompt = f"""请列出{school_name}研究生院招生的所有硕士专业（只列专业名称）。
从以下专业列表中选择该校实际招生的专业：

{major_names}

请以 JSON 数组格式返回，例如：
["专业名称1", "专业名称2", ...]

注意：
1. 只返回 JSON 数组，不要有其他内容
2. 只选择该校实际招生的专业
3. 专业名称必须与上述列表完全匹配"""
            
            response = call_qwen(prompt)
            if response:
                major_list = parse_json_from_response(response)
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
                        relations_inserted += len(relations)
                        logger.info(f"{school_name}: 匹配 {len(relations)} 个专业")
            
            # 避免 API 调用频率限制
            time.sleep(1.5)
        
        logger.info(f"共插入 {relations_inserted} 条学校-专业关系")
        
        # 统计
        cursor.execute("SELECT COUNT(*) as cnt FROM school_majors")
        logger.info(f"school_majors 表当前记录数: {cursor.fetchone()['cnt']}")
        
    finally:
        conn.close()


# ==================== 3. 使用千问抓取招生数据 ====================
def fill_enrollment_records_with_qwen(years: list = None, school_limit: int = 20):
    """使用千问抓取招生数据"""
    if years is None:
        years = [2025]
    
    logger.info(f"开始使用千问抓取招生数据（前{school_limit}所学校，年份{years}）...")
    
    if not init_dashscope():
        return
    
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # 获取前 N 所学校
        cursor.execute("""
            SELECT id, school_name FROM schools 
            ORDER BY ranking LIMIT %s
        """, (school_limit,))
        schools = cursor.fetchall()
        
        # 获取这些学校已关联的专业
        cursor.execute("""
            SELECT sm.school_id, sm.major_id, m.major_name, m.degree_type
            FROM school_majors sm
            JOIN majors m ON sm.major_id = m.id
            WHERE sm.school_id IN ({})
        """.format(','.join([str(s['id']) for s in schools])))
        school_major_relations = cursor.fetchall()
        
        # 按学校分组
        school_majors_map = {}
        for rel in school_major_relations:
            if rel['school_id'] not in school_majors_map:
                school_majors_map[rel['school_id']] = []
            school_majors_map[rel['school_id']].append(rel)
        
        records_inserted = 0
        
        for year in years:
            for school in schools:
                school_id = school['id']
                school_name = school['school_name']
                
                if school_id not in school_majors_map:
                    continue
                
                majors = school_majors_map[school_id]
                
                # 只处理前10个专业（避免单次请求太长）
                for major_batch in [majors[i:i+10] for i in range(0, len(majors), 10)]:
                    major_info = "\n".join([
                        f"- {m['major_name']}（{m['degree_type']}）"
                        for m in major_batch
                    ])
                    
                    prompt = f"""请提供{school_name}{year}年硕士研究生的以下专业招生数据：

{major_info}

请提供以下信息（如果不确定，请给出合理估计值）：
1. 招生院系
2. 计划招生人数
3. 实际录取人数
4. 推免人数
5. 报名人数（估计）
6. 学费（元/年）
7. 学制

请以 JSON 格式返回，格式如下：
{{
  "专业名称": {{
    "department_name": "招生院系",
    "planned_enrollment": 数字,
    "actual_enrollment": 数字,
    "recommended_exemption_count": 数字,
    "application_count": 数字,
    "tuition_fee": 数字,
    "academic_system": "学制"
  }},
  ...
}}

注意：
1. 只返回 JSON，不要有其他内容
2. 数据尽量准确，可参考往年数据
3. 学费单位为元/年"""
                    
                    response = call_qwen(prompt)
                    if response:
                        enrollment_data = parse_json_from_response(response)
                        if enrollment_data:
                            for major in major_batch:
                                major_name = major['major_name']
                                if major_name in enrollment_data:
                                    data = enrollment_data[major_name]
                                    
                                    # 计算报录比
                                    app_count = data.get('application_count')
                                    act_count = data.get('actual_enrollment')
                                    ratio = None
                                    if app_count and act_count and act_count > 0:
                                        ratio = round(app_count / act_count, 2)
                                    
                                    try:
                                        cursor.execute("""
                                            INSERT IGNORE INTO enrollment_records (
                                                school_id, major_id, exam_year, degree_type, study_mode,
                                                department_name, planned_enrollment, actual_enrollment,
                                                recommended_exemption_count, application_count,
                                                application_admission_ratio, tuition_fee, academic_system
                                            ) VALUES (
                                                %s, %s, %s, %s, 'full_time', %s, %s, %s, %s, %s, %s, %s, %s
                                            )
                                        """, (
                                            school_id, major['major_id'], year, major['degree_type'],
                                            data.get('department_name'),
                                            data.get('planned_enrollment'),
                                            data.get('actual_enrollment'),
                                            data.get('recommended_exemption_count'),
                                            app_count,
                                            ratio,
                                            data.get('tuition_fee'),
                                            data.get('academic_system')
                                        ))
                                        records_inserted += 1
                                    except Exception as e:
                                        logger.warning(f"插入失败: {school_name}-{major_name}, {e}")
                    
                    # 避免 API 调用频率限制
                    time.sleep(2)
                
                # 每个学校处理完后暂停
                time.sleep(1)
        
        logger.info(f"共插入 {records_inserted} 条招生记录")
        
        # 统计
        cursor.execute("SELECT COUNT(*) as cnt FROM enrollment_records")
        logger.info(f"enrollment_records 表当前记录数: {cursor.fetchone()['cnt']}")
        
    finally:
        conn.close()


# ==================== 4. 使用千问抓取分数线 ====================
def fill_score_lines_with_qwen(years: list = None):
    """使用千问抓取分数线数据"""
    if years is None:
        years = [2025]
    
    logger.info(f"开始使用千问抓取分数线数据（年份{years}）...")
    
    if not init_dashscope():
        return
    
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # 获取招生记录
        year_condition = f"AND exam_year IN ({','.join(map(str, years))})" if years else ""
        cursor.execute(f"""
            SELECT er.id, er.exam_year, er.degree_type, er.study_mode,
                   s.school_name, m.major_name
            FROM enrollment_records er
            JOIN schools s ON er.school_id = s.id
            JOIN majors m ON er.major_id = m.id
            {year_condition}
            LIMIT 200
        """)  # 限制数量，避免过多 API 调用
        records = cursor.fetchall()
        
        # 按学校-年份分组
        grouped = {}
        for record in records:
            key = (record['school_name'], record['exam_year'])
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(record)
        
        lines_inserted = 0
        
        for (school_name, year), er_records in grouped.items():
            major_list = "\n".join([
                f"- {r['id']}: {r['major_name']}（{r['degree_type']}）"
                for r in er_records[:10]  # 每次最多10个
            ])
            
            prompt = f"""请提供{school_name}{year}年硕士研究生以下专业的分数线数据：

{major_list}

请提供以下分数线：
1. 国家线（总分、政治、英语、业务课一、业务课二）
2. 学校复试线（总分、政治、英语、业务课一、业务课二）
3. 录取分数（最低分、平均分、最高分）

请以 JSON 格式返回，格式如下：
{{
  "专业ID": {{
    "national": {{"total": 数字, "politics": 数字, "english": 数字, "subject1": 数字, "subject2": 数字}},
    "school_retest": {{"total": 数字, "politics": 数字, "english": 数字, "subject1": 数字, "subject2": 数字}},
    "admission": {{"low": 数字, "avg": 数字, "high": 数字}}
  }},
  ...
}}

注意：
1. 只返回 JSON，不要有其他内容
2. 分数要合理，符合国家线和学校实际情况
3. 如果某个专业没有数据，可以省略"""
            
            response = call_qwen(prompt)
            if response:
                score_data = parse_json_from_response(response)
                if score_data:
                    for er_id_str, scores in score_data.items():
                        try:
                            er_id = int(er_id_str)
                            
                            # 插入国家线
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
                                lines_inserted += 1
                            
                            # 插入学校复试线
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
                                lines_inserted += 1
                            
                            # 插入录取分数
                            if 'admission' in scores:
                                a = scores['admission']
                                cursor.execute("""
                                    INSERT IGNORE INTO score_lines (
                                        enrollment_record_id, score_line_type,
                                        admit_low_score, admit_avg_score, admit_high_score
                                    ) VALUES (%s, 'school_admission', %s, %s, %s)
                                """, (er_id, a.get('low'), a.get('avg'), a.get('high')))
                                lines_inserted += 1
                                
                        except (ValueError, Exception) as e:
                            logger.warning(f"处理失败 er_id={er_id_str}: {e}")
            
            # 避免 API 调用频率限制
            time.sleep(2)
        
        logger.info(f"共插入 {lines_inserted} 条分数线记录")
        
        # 统计
        cursor.execute("SELECT COUNT(*) as cnt FROM score_lines")
        logger.info(f"score_lines 表当前记录数: {cursor.fetchone()['cnt']}")
        
    finally:
        conn.close()


# ==================== 并发版本：快速填充招生数据 ====================
# 线程锁，保护数据库写入
_db_lock = threading.Lock()
_insert_count = 0

def process_school_enrollment(school: dict, year: int, major_batch_size: int = 10) -> int:
    """处理单个学校的招生数据（线程安全）"""
    global _insert_count
    school_id = school['id']
    school_name = school['school_name']
    
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # 获取该校已关联的专业
        cursor.execute("""
            SELECT sm.school_id, sm.major_id, m.major_name, m.degree_type
            FROM school_majors sm
            JOIN majors m ON sm.major_id = m.id
            WHERE sm.school_id = %s
        """, (school_id,))
        majors = cursor.fetchall()
        
        if not majors:
            return 0
        
        local_count = 0
        
        # 分批处理专业
        for major_batch in [majors[i:i+major_batch_size] for i in range(0, len(majors), major_batch_size)]:
            major_info = "\n".join([
                f"- {m['major_name']}（{m['degree_type']}）"
                for m in major_batch
            ])
            
            prompt = f"""请提供{school_name}{year}年硕士研究生的以下专业招生数据：

{major_info}

请提供以下信息（如果不确定，请给出合理估计值）：
1. 招生院系
2. 计划招生人数
3. 实际录取人数
4. 推免人数
5. 报名人数（估计）
6. 学费（元/年）
7. 学制

请以 JSON 格式返回，格式如下：
{{
  "专业名称": {{
    "department_name": "招生院系",
    "planned_enrollment": 数字,
    "actual_enrollment": 数字,
    "recommended_exemption_count": 数字,
    "application_count": 数字,
    "tuition_fee": 数字,
    "academic_system": "学制"
  }},
  ...
}}

注意：
1. 只返回 JSON，不要有其他内容
2. 数据尽量准确，可参考往年数据
3. 学费单位为元/年"""
            
            response = call_qwen(prompt)
            if response:
                enrollment_data = parse_json_from_response(response)
                if enrollment_data:
                    records_to_insert = []
                    for major in major_batch:
                        major_name = major['major_name']
                        if major_name in enrollment_data:
                            data = enrollment_data[major_name]
                            app_count = data.get('application_count')
                            act_count = data.get('actual_enrollment')
                            ratio = None
                            if app_count and act_count and act_count > 0:
                                ratio = round(app_count / act_count, 2)
                            
                            records_to_insert.append((
                                school_id, major['major_id'], year, major['degree_type'],
                                data.get('department_name'),
                                data.get('planned_enrollment'),
                                data.get('actual_enrollment'),
                                data.get('recommended_exemption_count'),
                                app_count,
                                ratio,
                                data.get('tuition_fee'),
                                data.get('academic_system')
                            ))
                    
                    # 线程安全地写入数据库
                    if records_to_insert:
                        with _db_lock:
                            cursor.executemany("""
                                INSERT IGNORE INTO enrollment_records (
                                    school_id, major_id, exam_year, degree_type, study_mode,
                                    department_name, planned_enrollment, actual_enrollment,
                                    recommended_exemption_count, application_count,
                                    application_admission_ratio, tuition_fee, academic_system
                                ) VALUES (
                                    %s, %s, %s, %s, 'full_time', %s, %s, %s, %s, %s, %s, %s, %s
                                )
                            """, records_to_insert)
                            local_count += cursor.rowcount
            
            # API 调用间隔
            time.sleep(1)
        
        if local_count > 0:
            logger.info(f"{school_name}: 插入 {local_count} 条招生记录")
        
        return local_count
        
    finally:
        conn.close()


def fill_enrollment_records_concurrent(years: list = None, school_limit: int = 50, max_workers: int = 5):
    """并发填充招生数据"""
    if years is None:
        years = [2025]
    
    logger.info(f"开始并发抓取招生数据（前{school_limit}所学校，{max_workers}并发，年份{years}）...")
    
    if not init_dashscope():
        return
    
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # 获取前 N 所学校
        cursor.execute("""
            SELECT id, school_name FROM schools 
            ORDER BY ranking LIMIT %s
        """, (school_limit,))
        schools = cursor.fetchall()
        
        logger.info(f"共 {len(schools)} 所学校待处理")
        
        global _insert_count
        _insert_count = 0
        
        # 并发处理
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for year in years:
                for school in schools:
                    future = executor.submit(process_school_enrollment, school, year)
                    futures[future] = school['school_name']
            
            # 等待所有任务完成
            for future in as_completed(futures):
                school_name = futures[future]
                try:
                    count = future.result()
                    _insert_count += count
                except Exception as e:
                    logger.error(f"{school_name} 处理失败: {e}")
        
        logger.info(f"共插入 {_insert_count} 条招生记录")
        
        # 统计
        cursor.execute("SELECT COUNT(*) as cnt FROM enrollment_records")
        logger.info(f"enrollment_records 表当前记录数: {cursor.fetchone()['cnt']}")
        
    finally:
        conn.close()


# ==================== 主函数 ====================
def main():
    """按顺序执行所有数据抓取任务"""
    logger.info("=" * 60)
    logger.info("开始使用千问大模型抓取考研数据")
    logger.info("=" * 60)
    
    # 配置 API Key
    global DASHSCOPE_API_KEY
    if DASHSCOPE_API_KEY == "YOUR_API_KEY_HERE":
        logger.warning("请先配置 DASHSCOPE_API_KEY")
        return
    
    # 1. 填充 school_tags
    fill_school_tags_with_qwen(batch_size=30)
    
    # 2. 填充 school_majors
    fill_school_majors_with_qwen(school_limit=20)
    
    # 3. 填充 enrollment_records (并发版本)
    fill_enrollment_records_concurrent(years=[2025], school_limit=30, max_workers=5)
    
    # 4. 填充 score_lines
    fill_score_lines_with_qwen(years=[2025])
    
    logger.info("=" * 60)
    logger.info("数据抓取任务完成")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
