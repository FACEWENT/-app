"""
研招网官方数据爬虫
从 yz.chsi.com.cn 爬取权威的院校、专业、招生数据
"""
import time
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import pymysql
import re
from urllib.parse import urljoin

# 配置
BASE_URL = "https://yz.chsi.com.cn"
SCHOOLS_PER_PAGE = 20
REQUEST_DELAY = 3  # 请求间隔（秒）

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://yz.chsi.com.cn/",
}


class YZChsiSpider:
    """研招网爬虫"""
    
    def __init__(self, db_config: Dict):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.db_config = db_config
        self.conn = None
        
    def connect_db(self):
        """连接数据库"""
        self.conn = pymysql.connect(
            host=self.db_config['host'],
            port=self.db_config['port'],
            user=self.db_config['user'],
            password=self.db_config['password'],
            database=self.db_config['database'],
            charset='utf8mb4'
        )
        
    def close_db(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            
    def fetch_page(self, url: str, retries: int = 3) -> Optional[str]:
        """获取页面内容"""
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=30)
                response.encoding = 'utf-8'
                if response.status_code == 200:
                    return response.text
                else:
                    print(f"  [WARN] HTTP {response.status_code}: {url}")
            except Exception as e:
                print(f"  [ERROR] 请求失败 (尝试 {attempt+1}/{retries}): {e}")
                time.sleep(5)
        return None
    
    def parse_schools_list(self, html: str) -> List[Dict]:
        """解析院校列表页"""
        soup = BeautifulSoup(html, 'html.parser')
        schools = []
        
        # 查找所有院校卡片
        items = soup.select('div.sch-item')
        if not items:
            # 尝试其他选择器
            items = soup.select('.sch-list li, .yxk-table tr')
            
        for item in items:
            try:
                # 院校名称和链接
                name_elem = item.select_one('a.name.js-yxk-yxmc, a.name')
                if not name_elem:
                    continue
                    
                school_name = name_elem.get_text(strip=True)
                detail_url = name_elem.get('href', '')
                if detail_url:
                    detail_url = urljoin(BASE_URL, detail_url)
                    # 提取 schId
                    sch_id_match = re.search(r'schId-(\d+)', detail_url)
                    sch_id = sch_id_match.group(1) if sch_id_match else None
                
                # 所在地区和主管部门
                dept_elem = item.select_one('div.sch-department')
                location = ""
                department = ""
                if dept_elem:
                    text = dept_elem.get_text()
                    # 提取地区（通常在最前面）
                    location = text.split('主管部门')[0].strip() if '主管部门' in text else text.strip()
                    # 提取主管部门
                    dept_match = re.search(r'主管部门[：:](\S+)', text)
                    department = dept_match.group(1) if dept_match else ""
                
                # 院校特性标签
                tags = item.select('span.sch-tag')
                tag_texts = [tag.get_text(strip=True) for tag in tags]
                
                is_985 = False
                is_211 = False
                is_double_first_class = False
                is_self_line = False
                
                for tag in tag_texts:
                    if '985' in tag:
                        is_985 = True
                    if '211' in tag:
                        is_211 = True
                    if '双一流' in tag:
                        is_double_first_class = True
                    if '自划线' in tag:
                        is_self_line = True
                
                # 检查文本中是否包含985/211标识
                full_text = item.get_text()
                if '985' in full_text and '工程' not in full_text:
                    is_985 = True
                if '211' in full_text and '工程' not in full_text:
                    is_211 = True
                
                schools.append({
                    'sch_id': sch_id,
                    'name': school_name,
                    'province': location,
                    'department': department,
                    'is_985': is_985,
                    'is_211': is_211,
                    'is_double_first_class': is_double_first_class,
                    'is_self_line': is_self_line,
                    'detail_url': detail_url,
                    'tags': tag_texts
                })
                
            except Exception as e:
                print(f"  [WARN] 解析院校卡片失败: {e}")
                continue
                
        return schools
    
    def crawl_all_schools(self) -> List[Dict]:
        """爬取所有院校列表"""
        print("=" * 60)
        print("开始爬取研招网院校列表...")
        print("=" * 60)
        
        all_schools = []
        page = 0
        
        while True:
            url = f"{BASE_URL}/sch/?start={page}"
            print(f"\n[INFO] 正在爬取第 {page//SCHOOLS_PER_PAGE + 1} 页: {url}")
            
            html = self.fetch_page(url)
            if not html:
                print("  [ERROR] 获取页面失败，跳过")
                break
                
            schools = self.parse_schools_list(html)
            if not schools:
                print("  [WARN] 未解析到院校数据，可能是最后一页")
                break
                
            print(f"  [OK] 解析到 {len(schools)} 所院校")
            all_schools.extend(schools)
            
            # 检查是否还有下一页
            if len(schools) < SCHOOLS_PER_PAGE:
                print("  [INFO] 已到达最后一页")
                break
                
            page += SCHOOLS_PER_PAGE
            time.sleep(REQUEST_DELAY)
            
        print(f"\n[OK] 院校列表爬取完成，共 {len(all_schools)} 所院校")
        return all_schools
    
    def parse_province(self, province_text: str) -> str:
        """标准化省份名称"""
        province_map = {
            '北京': '北京',
            '天津': '天津',
            '上海': '上海',
            '重庆': '重庆',
            '河北': '河北',
            '山西': '山西',
            '辽宁': '辽宁',
            '吉林': '吉林',
            '黑龙江': '黑龙江',
            '江苏': '江苏',
            '浙江': '浙江',
            '安徽': '安徽',
            '福建': '福建',
            '江西': '江西',
            '山东': '山东',
            '河南': '河南',
            '湖北': '湖北',
            '湖南': '湖南',
            '广东': '广东',
            '海南': '海南',
            '四川': '四川',
            '贵州': '贵州',
            '云南': '云南',
            '陕西': '陕西',
            '甘肃': '甘肃',
            '青海': '青海',
            '台湾': '台湾',
            '内蒙古': '内蒙古',
            '广西': '广西',
            '西藏': '西藏',
            '宁夏': '宁夏',
            '新疆': '新疆',
        }
        
        for key, value in province_map.items():
            if key in province_text:
                return value
        return province_text.strip()
    
    def save_schools_to_db(self, schools: List[Dict]):
        """保存院校数据到数据库"""
        print("\n" + "=" * 60)
        print("开始保存院校数据到数据库...")
        print("=" * 60)
        
        self.connect_db()
        try:
            cursor = self.conn.cursor()
            
            # 清空现有数据（可选）
            # cursor.execute("DELETE FROM schools")
            
            inserted = 0
            updated = 0
            
            for school in schools:
                province = self.parse_province(school['province'])
                
                # 检查是否已存在
                cursor.execute("SELECT id FROM schools WHERE school_name = %s", (school['name'],))
                existing = cursor.fetchone()
                
                if existing:
                    # 更新现有记录
                    cursor.execute("""
                        UPDATE schools SET
                            province = %s,
                            is_985 = %s,
                            is_211 = %s,
                            is_double_first_class = %s,
                            school_type = %s
                        WHERE school_name = %s
                    """, (
                        province,
                        school['is_985'],
                        school['is_211'],
                        school['is_double_first_class'],
                        school.get('department', ''),
                        school['name']
                    ))
                    updated += 1
                else:
                    # 插入新记录
                    cursor.execute("""
                        INSERT INTO schools (
                            school_name, province, is_985, is_211, 
                            is_double_first_class, school_type, status
                        ) VALUES (%s, %s, %s, %s, %s, %s, 'active')
                    """, (
                        school['name'],
                        province,
                        school['is_985'],
                        school['is_211'],
                        school['is_double_first_class'],
                        school.get('department', '')
                    ))
                    inserted += 1
                
                if (inserted + updated) % 50 == 0:
                    self.conn.commit()
                    print(f"  [INFO] 已处理 {inserted + updated} 所院校 (新增: {inserted}, 更新: {updated})")
                    
            self.conn.commit()
            print(f"\n[OK] 数据库保存完成 (新增: {inserted}, 更新: {updated})")
            
        finally:
            self.close_db()
    
    def run(self):
        """执行爬取任务"""
        start_time = time.time()
        
        # 爬取院校列表
        schools = self.crawl_all_schools()
        
        if schools:
            # 保存到数据库
            self.save_schools_to_db(schools)
            
            # 统计信息
            print("\n" + "=" * 60)
            print("爬取统计:")
            print("=" * 60)
            print(f"  院校总数: {len(schools)}")
            
            provinces = {}
            for s in schools:
                p = self.parse_province(s['province'])
                provinces[p] = provinces.get(p, 0) + 1
            
            print(f"\n  省份分布 (前10):")
            for p, count in sorted(provinces.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"    {p}: {count} 所")
            
            count_985 = sum(1 for s in schools if s['is_985'])
            count_211 = sum(1 for s in schools if s['is_211'])
            count_double = sum(1 for s in schools if s['is_double_first_class'])
            
            print(f"\n  985院校: {count_985} 所")
            print(f"  211院校: {count_211} 所")
            print(f"  双一流: {count_double} 所")
        
        elapsed = time.time() - start_time
        print(f"\n总耗时: {elapsed:.2f} 秒")


if __name__ == "__main__":
    # 数据库配置
    DB_CONFIG = {
        'host': '127.0.0.1',
        'port': 3306,
        'user': 'root',
        'password': 'lwt18251X',
        'database': 'kaoyan_system_v2',
    }
    
    spider = YZChsiSpider(DB_CONFIG)
    spider.run()
