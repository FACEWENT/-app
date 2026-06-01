"""
从研招网抓取院校数据 - 简化版
"""
import requests
from bs4 import BeautifulSoup
import logging
import time
import pymysql
from pymysql.cursors import DictCursor
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

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

def get_connection():
    return pymysql.connect(**DB_CONFIG)


def scrape_yz_schools():
    """从研招网抓取院校"""
    logger.info("开始从研招网抓取院校数据...")
    
    conn = get_connection()
    total_added = 0
    
    try:
        cursor = conn.cursor()
        
        # 获取已有学校
        cursor.execute("SELECT school_name FROM schools")
        existing = {row['school_name'] for row in cursor.fetchall()}
        logger.info(f"已有学校: {len(existing)} 所")
        
        start = 0
        page_size = 20
        max_pages = 47  # 研招网共47页
        
        for page in range(1, max_pages + 1):
            start = (page - 1) * page_size
            url = f'https://yz.chsi.com.cn/sch/?start={start}'
            
            try:
                response = requests.get(url, headers=HEADERS, timeout=10)
                if response.status_code != 200:
                    logger.warning(f"第{page}页请求失败: {response.status_code}")
                    break
                
                soup = BeautifulSoup(response.text, 'html.parser')
                items = soup.find_all('div', class_='sch-item')
                
                if not items:
                    logger.info(f"第{page}页无数据,结束")
                    break
                
                logger.info(f"第{page}页: 找到 {len(items)} 所学校")
                
                schools_data = []
                for item in items:
                    # 学校名称
                    name_elem = item.find('a', class_='name')
                    if not name_elem:
                        continue
                    
                    school_name = name_elem.get_text(strip=True)
                    if school_name in existing:
                        continue
                    
                    # 获取完整文本信息
                    full_text = item.get_text()
                    full_text = re.sub(r'\s+', '', full_text)
                    
                    # 解析标签
                    is_985 = 1 if '985' in full_text else 0
                    is_211 = 1 if '211' in full_text else 0
                    is_double_first = 1 if '双一流' in full_text else 0
                    is_self_marking = 1 if '自划线' in full_text else 0
                    has_grad_school = 1 if '研究生院' in full_text else 0
                    
                    # 解析位置 - 在""和"主管部门"之间
                    location = ''
                    province = ''
                    city = ''
                    
                    # 查找图标字符后的位置信息
                    match = re.search(r'[]([^主管部门]+?)主管部门', full_text)
                    if match:
                        location = match.group(1).strip()
                        # 分离省市
                        parts = location.split()
                        if parts:
                            province = parts[0]
                            city = parts[1] if len(parts) > 1 else province
                    
                    # 判断学校类型
                    school_type = '综合'
                    if any(k in school_name for k in ['科技', '理工', '工程', '工业', '邮电', '电子']):
                        school_type = '理工'
                    elif '师范' in school_name:
                        school_type = '师范'
                    elif any(k in school_name for k in ['医学', '医药', '中医']):
                        school_type = '医药'
                    elif any(k in school_name for k in ['农业', '农林', '林业']):
                        school_type = '农林'
                    elif '财经' in school_name:
                        school_type = '财经'
                    elif any(k in school_name for k in ['政法', '公安', '警察']):
                        school_type = '政法'
                    elif '民族' in school_name:
                        school_type = '民族'
                    elif any(k in school_name for k in ['艺术', '美术', '音乐', '戏剧', '电影']):
                        school_type = '艺术'
                    elif '体育' in school_name:
                        school_type = '体育'
                    elif '语言' in school_name or '外国语' in school_name:
                        school_type = '语言'
                    
                    schools_data.append((
                        None, school_name, province, city, school_type,
                        is_985, is_211, is_double_first, is_self_marking,
                        None, None, None, None
                    ))
                    existing.add(school_name)
                
                if schools_data:
                    cursor.executemany("""
                        INSERT IGNORE INTO schools (
                            school_code, school_name, province, city, school_type,
                            is_985, is_211, is_double_first_class, is_self_marking,
                            ranking, intro, website, graduate_website
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, schools_data)
                    
                    added = cursor.rowcount
                    total_added += added
                    logger.info(f"  新增 {added} 所")
                
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"第{page}页处理失败: {e}")
                break
        
        logger.info(f"\n共新增 {total_added} 所学校")
        
        # 统计
        cursor.execute("SELECT COUNT(*) as cnt FROM schools")
        total = cursor.fetchone()['cnt']
        logger.info(f"schools 表当前记录数: {total}")
        
        # 省份分布
        cursor.execute("SELECT province, COUNT(*) as cnt FROM schools WHERE province != '' GROUP BY province ORDER BY cnt DESC")
        print("\n=== 各省份院校分布 ===")
        for row in cursor.fetchall():
            print(f"  {row['province']}: {row['cnt']} 所")
        
    finally:
        conn.close()


if __name__ == '__main__':
    scrape_yz_schools()
