"""
从研招网(yz.chsi.com.cn)抓取完整院校数据
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
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

def get_connection():
    return pymysql.connect(**DB_CONFIG)


def parse_school_info(item):
    """解析单个院校信息"""
    try:
        # 学校名称
        name_elem = item.find('a', class_='name')
        school_name = name_elem.get_text(strip=True) if name_elem else ''
        
        # 获取链接中的学校ID
        href = name_elem.get('href', '') if name_elem else ''
        school_id_match = re.search(r'sch/viewSchDetail\?schid=(\d+)', href)
        schid = school_id_match.group(1) if school_id_match else None
        
        # 标签信息
        tags = []
        tag_elems = item.find_all('span', class_='tag')
        for tag in tag_elems:
            tags.append(tag.get_text(strip=True))
        
        # 判断985/211/双一流
        is_985 = 1 if '985' in ' '.join(tags) else 0
        is_211 = 1 if '211' in ' '.join(tags) else 0
        is_double_first = 1 if '双一流' in ' '.join(tags) else 0
        
        # 自划线
        is_self_marking = 1 if '自划线' in ' '.join(tags) else 0
        
        # 位置信息
        location_elem = item.find('span', class_='place')
        location = location_elem.get_text(strip=True) if location_elem else ''
        # 解析省份和城市
        parts = location.split(' ') if location else ['', '']
        province = parts[0] if len(parts) > 0 else ''
        city = parts[1] if len(parts) > 1 else ''
        
        # 主管部门
        authority_elem = item.find('span', class_='belong')
        authority = authority_elem.get_text(strip=True).replace('主管部门：', '') if authority_elem else ''
        
        # 研究生院
        has_graduate_school = 1 if '研究生院' in ' '.join(tags) else 0
        
        return {
            'schid': schid,
            'school_name': school_name,
            'province': province,
            'city': city,
            'is_985': is_985,
            'is_211': is_211,
            'is_double_first_class': is_double_first,
            'is_self_marking': is_self_marking,
            'has_graduate_school': has_graduate_school,
            'authority': authority,
            'tags': tags,
            'href': href,
        }
    except Exception as e:
        logger.error(f'解析学校信息失败: {e}')
        return None


def scrape_schools():
    """抓取所有院校数据"""
    logger.info("开始从研招网抓取院校数据...")
    
    conn = get_connection()
    total_added = 0
    total_pages = 0
    
    try:
        cursor = conn.cursor()
        
        # 获取已有学校
        cursor.execute("SELECT school_name FROM schools")
        existing_schools = {row['school_name'] for row in cursor.fetchall()}
        logger.info(f"已有学校: {len(existing_schools)} 所")
        
        start = 0
        max_start = 1000  # 最多抓取1000所学校
        page_size = 20
        
        while start < max_start:
            url = f'https://yz.chsi.com.cn/sch/?start={start}'
            page = (start // page_size) + 1
            
            try:
                response = requests.get(url, headers=HEADERS, timeout=10)
                if response.status_code != 200:
                    logger.warning(f"第{page}页请求失败: {response.status_code}")
                    break
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 查找所有院校项
                items = soup.find_all('div', class_='sch-item')
                if not items:
                    logger.info(f"第{page}页无数据,抓取结束")
                    break
                
                logger.info(f"正在处理第{page}页,找到 {len(items)} 所学校")
                
                schools_to_insert = []
                for item in items:
                    info = parse_school_info(item)
                    if info and info['school_name'] and info['school_name'] not in existing_schools:
                        # 判断学校类型
                        school_type = '综合'
                        name = info['school_name']
                        if any(k in name for k in ['科技', '理工', '工程', '工业', '邮电', '电子']):
                            school_type = '理工'
                        elif '师范' in name:
                            school_type = '师范'
                        elif any(k in name for k in ['医学', '医药', '中医']):
                            school_type = '医药'
                        elif any(k in name for k in ['农业', '农林', '林业']):
                            school_type = '农林'
                        elif '财经' in name:
                            school_type = '财经'
                        elif any(k in name for k in ['政法', '公安', '警察']):
                            school_type = '政法'
                        elif '民族' in name:
                            school_type = '民族'
                        elif any(k in name for k in ['艺术', '美术', '音乐', '戏剧', '电影']):
                            school_type = '艺术'
                        elif '体育' in name:
                            school_type = '体育'
                        elif '语言' in name or '外国语' in name:
                            school_type = '语言'
                        elif '交通' in name:
                            school_type = '理工'
                        elif '建筑' in name:
                            school_type = '理工'
                        
                        schools_to_insert.append((
                            None,  # school_code - 后面生成
                            info['school_name'],
                            info['province'],
                            info['city'],
                            school_type,
                            info['is_985'],
                            info['is_211'],
                            info['is_double_first_class'],
                            info['is_self_marking'],
                            None,  # ranking
                            None,  # intro
                            None,  # website
                            None,  # graduate_website
                        ))
                        existing_schools.add(info['school_name'])
                
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
                
                total_pages = page
                page += 1
                time.sleep(1)  # 避免请求过快
                
            except Exception as e:
                logger.error(f"第{page}页处理失败: {e}")
                break
        
        logger.info(f"\n共抓取 {total_pages} 页, 新增 {total_added} 所学校")
        
        # 统计
        cursor.execute("SELECT COUNT(*) as cnt FROM schools")
        logger.info(f"schools 表当前记录数: {cursor.fetchone()['cnt']}")
        
        # 打印省份分布
        cursor.execute("SELECT province, COUNT(*) as cnt FROM schools GROUP BY province ORDER BY cnt DESC LIMIT 15")
        print("\n=== 各省份院校分布 ===")
        for row in cursor.fetchall():
            print(f"{row['province']}: {row['cnt']} 所")
        
    finally:
        conn.close()


if __name__ == '__main__':
    scrape_schools()
