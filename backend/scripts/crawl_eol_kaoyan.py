"""
从中国教育在线爬取考研招生数据
网站: https://kaoyan.eol.cn
数据包括：院校库、专业库、分数线等
"""
import time
import requests
from bs4 import BeautifulSoup
import pymysql
import json
import re
from typing import Dict, List, Optional

BASE_URL = "https://kaoyan.eol.cn"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': 'lwt18251X',
    'database': 'kaoyan_system_v2',
}


class EolKaoyanSpider:
    """中国教育在线考研数据爬虫"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.conn = None
        
    def connect_db(self):
        self.conn = pymysql.connect(**DB_CONFIG, charset='utf8mb4')
        
    def close_db(self):
        if self.conn:
            self.conn.close()
    
    def fetch_page(self, url: str, retries: int = 3) -> Optional[str]:
        """获取页面"""
        for i in range(retries):
            try:
                response = self.session.get(url, timeout=10)
                response.encoding = 'utf-8'
                if response.status_code == 200:
                    return response.text
            except Exception as e:
                print(f"    [ERROR] 请求失败 ({i+1}/{retries}): {e}")
                time.sleep(2)
        return None
    
    def crawl_school_list(self) -> List[Dict]:
        """爬取院校列表"""
        print("正在爬取院校列表...")
        
        # 中国教育在线院校库
        url = f"{BASE_URL}/school_list/"
        html = self.fetch_page(url)
        
        if not html:
            print("  [ERROR] 获取院校列表失败")
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        schools = []
        
        # 按省份分类的院校
        province_sections = soup.select('.province-school')
        
        for section in province_sections:
            province_name = section.select_one('.province-name')
            if not province_name:
                continue
            
            province = province_name.get_text(strip=True)
            
            # 提取该省份下的所有院校
            school_links = section.select('a.school-name')
            for link in school_links:
                school_name = link.get_text(strip=True)
                school_url = link.get('href', '')
                
                schools.append({
                    'province': province,
                    'name': school_name,
                    'url': school_url if school_url.startswith('http') else f"{BASE_URL}{school_url}"
                })
        
        print(f"  ✓ 爬取到 {len(schools)} 所院校")
        return schools
    
    def crawl_school_detail(self, school_url: str, school_name: str) -> Optional[Dict]:
        """爬取院校详情"""
        html = self.fetch_page(school_url)
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        info = {
            'school_name': school_name,
            'basic_info': {},
            'enrollment_chapters': [],
            'score_lines': []
        }
        
        # 提取基本信息
        info_table = soup.select_one('.school-info-table')
        if info_table:
            rows = info_table.select('tr')
            for row in rows:
                cells = row.select('td')
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    info['basic_info'][key] = value
        
        # 提取招生简章列表
        chapter_list = soup.select('.chapter-list a')
        for link in chapter_list:
            title = link.get_text(strip=True)
            url = link.get('href', '')
            year_match = re.search(r'(20\d{2})', title)
            
            if year_match:
                info['enrollment_chapters'].append({
                    'title': title,
                    'year': int(year_match.group(1)),
                    'url': url if url.startswith('http') else f"{BASE_URL}{url}"
                })
        
        return info
    
    def crawl_score_lines(self) -> List[Dict]:
        """爬取历年考研分数线"""
        print("\n正在爬取考研分数线数据...")
        
        # 国家线页面
        url = f"{BASE_URL}/kaoyan/ksdj/fsx/"
        html = self.fetch_page(url)
        
        if not html:
            print("  [ERROR] 获取分数线页面失败")
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        score_lines = []
        
        # 查找分数线表格
        tables = soup.select('table')
        for table in tables:
            # 解析表格中的分数线数据
            rows = table.select('tr')
            for row in rows[1:]:  # 跳过表头
                cells = row.select('td, th')
                if len(cells) >= 5:
                    try:
                        year_text = cells[0].get_text(strip=True)
                        year_match = re.search(r'(20\d{2})', year_text)
                        
                        if year_match:
                            score_data = {
                                'year': int(year_match.group(1)),
                                'degree_type': cells[1].get_text(strip=True),
                                'category': cells[2].get_text(strip=True),
                                'total_score': cells[3].get_text(strip=True),
                                'single_score': cells[4].get_text(strip=True),
                                'data_source': '中国教育在线'
                            }
                            score_lines.append(score_data)
                    except:
                        continue
        
        print(f"  ✓ 爬取到 {len(score_lines)} 条分数线数据")
        return score_lines
    
    def save_score_lines(self, score_lines: List[Dict]):
        """保存分数线数据"""
        if not score_lines:
            return
        
        cursor = self.conn.cursor()
        inserted = 0
        
        for item in score_lines:
            try:
                # 这里可以根据实际情况调整保存逻辑
                # 暂时只打印，不保存到数据库
                print(f"    {item['year']}年 {item['category']}: "
                      f"总分{item['total_score']}, 单科{item['single_score']}")
                inserted += 1
            except Exception as e:
                print(f"    [ERROR] 处理分数线数据失败: {e}")
        
        print(f"\n  ✓ 处理了 {inserted} 条分数线数据")
    
    def run(self):
        """执行爬取任务"""
        self.connect_db()
        
        print("=" * 60)
        print("中国教育在线考研数据爬虫")
        print("=" * 60)
        
        # 1. 爬取分数线数据
        score_lines = self.crawl_score_lines()
        if score_lines:
            self.save_score_lines(score_lines)
        
        # 2. 爬取院校列表（可选）
        # schools = self.crawl_school_list()
        
        self.close_db()
        
        print("\n" + "=" * 60)
        print("爬取完成！")
        print("=" * 60)


def main():
    spider = EolKaoyanSpider()
    spider.run()


if __name__ == "__main__":
    main()
