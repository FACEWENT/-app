"""
从各院校研究生招生官网爬取招生章程和历年数据
这是一个更可靠的数据获取方案
"""
import time
import requests
from bs4 import BeautifulSoup
import pymysql
import re
import json
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

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


class SchoolWebsiteSpider:
    """院校官网爬虫"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.conn = None
        
        # 常见院校研究生招生网站URL映射
        self.school_urls = {
            "清华大学": "https://yz.tsinghua.edu.cn",
            "北京大学": "https://admission.pku.edu.cn",
            "中国人民大学": "https://pgs.ruc.edu.cn",
            "北京师范大学": "https://yz.bnu.edu.cn",
            "北京航空航天大学": "https://yzb.buaa.edu.cn",
            "北京理工大学": "https://gradschool.bit.edu.cn",
            "中国农业大学": "https://yz.cau.edu.cn",
            "南开大学": "https://yzb.nankai.edu.cn",
            "天津大学": "https://yzb.tju.edu.cn",
            "大连理工大学": "http://ss.dlut.edu.cn",
            "东北大学": "https://yz.neu.edu.cn",
            "吉林大学": "http://yjsy.jlu.edu.cn",
            "哈尔滨工业大学": "https://yzb.hit.edu.cn",
            "复旦大学": "https://gsao.fudan.edu.cn",
            "同济大学": "https://yz.tongji.edu.cn",
            "上海交通大学": "https://yzb.sjtu.edu.cn",
            "华东师范大学": "https://yjszs.ecnu.edu.cn",
            "南京大学": "https://get.nju.edu.cn",
            "东南大学": "https://yzb.seu.edu.cn",
            "浙江大学": "https://grs.zju.edu.cn",
            "中国科学技术大学": "https://yzb.ustc.edu.cn",
            "厦门大学": "https://zs.xmu.edu.cn",
            "山东大学": "https://yz.sdu.edu.cn",
            "中国海洋大学": "https://yz.ouc.edu.cn",
            "武汉大学": "https://gs.whu.edu.cn",
            "华中科技大学": "http://yzs.hust.edu.cn",
            "湖南大学": "https://gra.hnu.edu.cn",
            "中南大学": "https://gra.csu.edu.cn",
            "中山大学": "https://gradschool.sysu.edu.cn",
            "华南理工大学": "https://yz.scut.edu.cn",
            "四川大学": "https://yz.scu.edu.cn",
            "电子科技大学": "https://yz.uestc.edu.cn",
            "重庆大学": "http://yz.cqu.edu.cn",
            "西安交通大学": "http://yz.xjtu.edu.cn",
            "西北工业大学": "https://yzb.nwpu.edu.cn",
            "兰州大学": "https://yz.lzu.edu.cn",
        }
    
    def connect_db(self):
        self.conn = pymysql.connect(**DB_CONFIG, charset='utf8mb4')
    
    def close_db(self):
        if self.conn:
            self.conn.close()
    
    def fetch_page(self, url: str, timeout: int = 10) -> Optional[str]:
        """获取页面内容"""
        try:
            response = self.session.get(url, timeout=timeout, allow_redirects=True)
            response.encoding = response.apparent_encoding
            if response.status_code == 200:
                return response.text
        except Exception as e:
            print(f"    [ERROR] 获取页面失败: {e}")
        return None
    
    def parse_enrollment_chapter(self, html: str, school_name: str) -> Dict:
        """解析招生章程页面"""
        soup = BeautifulSoup(html, 'html.parser')
        
        chapter_info = {
            'school_name': school_name,
            'title': '',
            'year': None,
            'total_enrollment': None,
            'exam_subjects': [],
            'retest_ratio': None,
            'notes': []
        }
        
        # 提取标题
        title_elem = soup.find('h1') or soup.find('h2') or soup.find('h3')
        if title_elem:
            chapter_info['title'] = title_elem.get_text(strip=True)
            # 从标题中提取年份
            year_match = re.search(r'(20\d{2})', chapter_info['title'])
            if year_match:
                chapter_info['year'] = int(year_match.group(1))
        
        # 提取正文内容
        content = soup.get_text()
        
        # 提取招生人数
        enrollment_patterns = [
            r'计划招生[^\d]*(\d+)[^名]',
            r'拟招收[^\d]*(\d+)[^名]',
            r'招生人数[^\d]*(\d+)',
        ]
        
        for pattern in enrollment_patterns:
            match = re.search(pattern, content)
            if match:
                chapter_info['total_enrollment'] = int(match.group(1))
                break
        
        # 提取复试比例
        retest_patterns = [
            r'复试比例[^\d]*(\d+\.?\d*)%',
            r'差额复试比例[^\d]*(\d+\.?\d*)[:：]',
        ]
        
        for pattern in retest_patterns:
            match = re.search(pattern, content)
            if match:
                chapter_info['retest_ratio'] = float(match.group(1))
                break
        
        return chapter_info
    
    def crawl_school_website(self, school_name: str, school_code: str) -> List[Dict]:
        """爬取单个院校的招生信息"""
        results = []
        
        # 获取院校官网URL
        base_url = self.school_urls.get(school_name)
        if not base_url:
            print(f"    [WARN] 未找到 {school_name} 的研究生招生网站")
            return results
        
        print(f"    正在爬取 {school_name} ({base_url})...")
        
        # 尝试爬取招生章程列表页
        list_urls = [
            f"{base_url}/zsgz/zszc.htm",
            f"{base_url}/zsgz/zsjz.htm",
            f"{base_url}/zs/zszc.htm",
            f"{base_url}/zsxx/zszc.htm",
        ]
        
        list_html = None
        for url in list_urls:
            html = self.fetch_page(url)
            if html and len(html) > 1000:
                list_html = html
                print(f"    ✓ 找到招生章程列表: {url}")
                break
        
        if not list_html:
            print(f"    [WARN] 未找到招生章程列表")
            return results
        
        # 解析列表页，获取章程链接
        soup = BeautifulSoup(list_html, 'html.parser')
        links = soup.find_all('a', href=True)
        
        chapter_urls = []
        for link in links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # 匹配招生章程链接
            if any(keyword in text for keyword in ['招生简章', '招生章程', '硕士招生']):
                if href.startswith('http'):
                    chapter_urls.append(href)
                else:
                    chapter_urls.append(f"{base_url}/{href.lstrip('/')}")
        
        # 爬取前3个章程
        for url in chapter_urls[:3]:
            try:
                html = self.fetch_page(url)
                if html:
                    chapter = self.parse_enrollment_chapter(html, school_name)
                    chapter['url'] = url
                    results.append(chapter)
                    print(f"    ✓ 爬取到章程: {chapter['title']}")
                
                time.sleep(1)
            except Exception as e:
                print(f"    [ERROR] 爬取章程失败: {e}")
        
        return results
    
    def crawl_top_schools(self, limit: int = 10):
        """爬取TOP院校的招生信息"""
        self.connect_db()
        
        cursor = self.conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("""
            SELECT id, school_name, school_code, province
            FROM schools 
            WHERE status = 'active' 
            AND school_code IS NOT NULL
            AND is_985 = 1
            ORDER BY ranking
            LIMIT %s
        """, (limit,))
        
        schools = cursor.fetchall()
        
        print(f"=" * 60)
        print(f"开始爬取 {len(schools)} 所985院校的招生信息")
        print(f"=" * 60)
        
        all_results = []
        
        for i, school in enumerate(schools):
            print(f"\n[{i+1}/{len(schools)}] {school['school_name']}")
            
            results = self.crawl_school_website(
                school['school_name'], 
                school['school_code']
            )
            
            all_results.extend(results)
            
            # 每爬取5所院校休息一次
            if (i + 1) % 5 == 0:
                print("  休息3秒...")
                time.sleep(3)
        
        # 保存结果
        print(f"\n{'=' * 60}")
        print(f"爬取完成！共获取 {len(all_results)} 条招生章程")
        print(f"{'=' * 60}")
        
        # 显示结果
        for result in all_results:
            print(f"\n{result['school_name']}:")
            print(f"  标题: {result['title']}")
            print(f"  年份: {result['year']}")
            print(f"  招生人数: {result['total_enrollment']}")
            print(f"  复试比例: {result['retest_ratio']}")
            print(f"  URL: {result.get('url', 'N/A')}")
        
        self.close_db()
        
        return all_results


def main():
    """主函数"""
    spider = SchoolWebsiteSpider()
    
    # 爬取TOP 10的985院校
    spider.crawl_top_schools(limit=10)


if __name__ == "__main__":
    main()
