"""
从公开数据源抓取考研院校数据
使用中国研究生招生信息网等公开数据
"""
import logging
import time
import json
import pymysql
from pymysql.cursors import DictCursor
import requests
from bs4 import BeautifulSoup
import re

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


def fetch_schools_from_yz():
    """从中国研究生招生信息网抓取院校数据"""
    logger.info("开始从研招网抓取院校数据...")
    
    # 研招网院校库API
    url = "https://yz.chsi.com.cn/sch/list.action"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }
    
    conn = get_connection()
    total_added = 0
    
    try:
        cursor = conn.cursor()
        
        # 获取已有学校
        cursor.execute("SELECT school_name FROM schools")
        existing_schools = {row['school_name'] for row in cursor.fetchall()}
        
        # 抓取所有省份的学校
        provinces = [
            "11", "12", "13", "14", "15",  # 北京天津河北山西内蒙古
            "21", "22", "23",  # 辽宁吉林黑龙江
            "31", "32", "33", "34", "35",  # 上海江苏浙江安徽福建
            "36", "37",  # 江西山东
            "41", "42", "43",  # 河南湖北湖南
            "44", "45", "46",  # 广东广西海南
            "50", "51", "52", "53", "54",  # 重庆四川贵州云南西藏
            "61", "62", "63", "64", "65",  # 陕西甘肃青海宁夏新疆
        ]
        
        province_map = {
            "11": "北京", "12": "天津", "13": "河北", "14": "山西", "15": "内蒙古",
            "21": "辽宁", "22": "吉林", "23": "黑龙江",
            "31": "上海", "32": "江苏", "33": "浙江", "34": "安徽", "35": "福建",
            "36": "江西", "37": "山东",
            "41": "河南", "42": "湖北", "43": "湖南",
            "44": "广东", "45": "广西", "46": "海南",
            "50": "重庆", "51": "四川", "52": "贵州", "53": "云南", "54": "西藏",
            "61": "陕西", "62": "甘肃", "63": "青海", "64": "宁夏", "65": "新疆",
        }
        
        for province_code in provinces:
            province_name = province_map[province_code]
            logger.info(f"正在抓取 {province_name} 省院校...")
            
            page = 1
            while True:
                params = {
                    "ssdm": province_code,
                    "pageno": page,
                }
                
                try:
                    response = requests.get(url, params=params, headers=headers, timeout=10)
                    if response.status_code != 200:
                        logger.warning(f"请求失败: {response.status_code}")
                        break
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 解析学校列表
                    school_rows = soup.select('table.ch-table tbody tr')
                    if not school_rows:
                        break
                    
                    schools_to_insert = []
                    for row in school_rows:
                        cols = row.find_all('td')
                        if len(cols) < 4:
                            continue
                        
                        school_name = cols[1].get_text(strip=True)
                        if school_name in existing_schools:
                            continue
                        
                        # 提取城市信息
                        location_text = cols[2].get_text(strip=True)
                        
                        # 提取主管部门
                        authority = cols[3].get_text(strip=True) if len(cols) > 3 else ""
                        
                        # 判断学校类型和层次
                        is_985 = 1 if '985' in authority or '985工程' in authority else 0
                        is_211 = 1 if '211' in authority or '211工程' in authority else 0
                        is_double_first = 1 if '双一流' in authority else 0
                        
                        # 判断学校类型
                        school_type = "综合"
                        if any(k in school_name for k in ['科技', '理工', '工程', '工业']):
                            school_type = "理工"
                        elif '师范' in school_name:
                            school_type = "师范"
                        elif '医学' in school_name or '医药' in school_name:
                            school_type = "医药"
                        elif '农业' in school_name or '农林' in school_name:
                            school_type = "农林"
                        elif '财经' in school_name:
                            school_type = "财经"
                        elif '政法' in school_name or '公安' in school_name:
                            school_type = "政法"
                        elif '民族' in school_name:
                            school_type = "民族"
                        elif '艺术' in school_name:
                            school_type = "艺术"
                        elif '体育' in school_name:
                            school_type = "体育"
                        elif '语言' in school_name:
                            school_type = "语言"
                        
                        schools_to_insert.append((
                            None,  # school_code will be generated
                            school_name,
                            province_name,
                            location_text,
                            school_type,
                            is_985,
                            is_211,
                            is_double_first,
                            0,  # is_self_marking
                            None,  # ranking
                            None,  # intro
                            None,  # website
                            None,  # graduate_website
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
                        logger.info(f"  第{page}页: 新增 {added} 所")
                        existing_schools.update([s[1] for s in schools_to_insert])
                    
                    # 检查是否有下一页
                    next_page = soup.select('.next, .page-next')
                    if not next_page or page >= 10:  # 最多抓取10页
                        break
                    
                    page += 1
                    time.sleep(2)  # 避免请求过快
                    
                except Exception as e:
                    logger.error(f"抓取{province_name}第{page}页失败: {e}")
                    break
        
        logger.info(f"共新增 {total_added} 所学校")
        
        # 统计
        cursor.execute("SELECT COUNT(*) as cnt FROM schools")
        logger.info(f"schools 表当前记录数: {cursor.fetchone()['cnt']}")
        
    finally:
        conn.close()


def generate_school_codes():
    """为没有学校代码的学校生成代码"""
    logger.info("正在生成学校代码...")
    
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # 获取没有代码的学校
        cursor.execute("""
            SELECT id, school_name, province 
            FROM schools 
            WHERE school_code IS NULL OR school_code = ''
            ORDER BY province
        """)
        schools = cursor.fetchall()
        
        # 生成代码(使用省份代码+序号)
        province_code_map = {
            "北京": "11", "天津": "12", "河北": "13", "山西": "14", "内蒙古": "15",
            "辽宁": "21", "吉林": "22", "黑龙江": "23",
            "上海": "31", "江苏": "32", "浙江": "33", "安徽": "34", "福建": "35",
            "江西": "36", "山东": "37",
            "河南": "41", "湖北": "42", "湖南": "43",
            "广东": "44", "广西": "45", "海南": "46",
            "重庆": "50", "四川": "51", "贵州": "52", "云南": "53", "西藏": "54",
            "陕西": "61", "甘肃": "62", "青海": "63", "宁夏": "64", "新疆": "65",
        }
        
        province_counter = {}
        updated = 0
        
        for school in schools:
            province = school['province']
            if province not in province_counter:
                province_counter[province] = 1
            
            counter = province_counter[province]
            province_code = province_code_map.get(province, "00")
            school_code = f"{province_code}{counter:03d}"
            
            cursor.execute("""
                UPDATE schools SET school_code = %s WHERE id = %s
            """, (school_code, school['id']))
            
            province_counter[province] += 1
            updated += 1
        
        logger.info(f"共更新 {updated} 所学校的代码")
        
    finally:
        conn.close()


def main():
    logger.info("=" * 60)
    logger.info("开始抓取考研院校数据")
    logger.info("=" * 60)
    
    # 1. 从研招网抓取院校数据
    fetch_schools_from_yz()
    
    # 2. 生成学校代码
    generate_school_codes()
    
    logger.info("=" * 60)
    logger.info("数据抓取完成")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
