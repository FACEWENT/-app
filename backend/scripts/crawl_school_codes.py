"""
从研招网爬取正确的教育部院校代码
"""
import time
import requests
from bs4 import BeautifulSoup
import pymysql
import re

BASE_URL = "https://yz.chsi.com.cn"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
}

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': 'lwt18251X',
    'database': 'kaoyan_system_v2',
}

def crawl_school_codes():
    """爬取院校代码"""
    print("开始爬取院校代码...")
    
    school_codes = {}
    page = 0
    
    while True:
        url = f"{BASE_URL}/sch/?start={page}"
        print(f"  爬取第 {page//20 + 1} 页...")
        
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                print(f"  HTTP {response.status_code}，停止爬取")
                break
            
            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.select('div.sch-item')
            
            if not items:
                print("  无更多数据，停止爬取")
                break
            
            for item in items:
                # 提取院校名称
                name_elem = item.select_one('a.name')
                if not name_elem:
                    continue
                name = name_elem.get_text(strip=True)
                
                # 提取链接中的schId
                href = name_elem.get('href', '')
                sch_id_match = re.search(r'schId-(\d+)', href)
                sch_id = sch_id_match.group(1) if sch_id_match else None
                
                # 提取网报公告链接中的dwdm（单位代码）
                wb_link = item.select_one('a[href*="sswbgg"]')
                if wb_link:
                    wb_href = wb_link.get('href', '')
                    dwdm_match = re.search(r'dwdm=(\d+)', wb_href)
                    if dwdm_match:
                        code = dwdm_match.group(1)
                        school_codes[name] = {
                            'code': code,
                            'sch_id': sch_id,
                        }
            
            if len(items) < 20:
                break
                
            page += 20
            time.sleep(2)
            
        except Exception as e:
            print(f"  爬取失败: {e}")
            break
    
    print(f"共爬取到 {len(school_codes)} 所院校的代码")
    return school_codes

def update_database(school_codes):
    """更新数据库"""
    conn = pymysql.connect(**DB_CONFIG, charset='utf8mb4')
    cursor = conn.cursor()
    
    updated = 0
    skipped = 0
    
    for name, info in school_codes.items():
        code = info['code']
        
        try:
            cursor.execute("""
                UPDATE schools 
                SET school_code = %s
                WHERE school_name = %s AND status = 'active'
            """, (code, name))
            
            if cursor.rowcount > 0:
                updated += 1
        except Exception as e:
            if 'Duplicate' in str(e):
                skipped += 1
            else:
                print(f"  [ERROR] 更新 {name} 失败: {e}")
    
    conn.commit()
    print(f"数据库更新完成: 成功 {updated} 条, 跳过 {skipped} 条")
    
    conn.close()

if __name__ == "__main__":
    codes = crawl_school_codes()
    update_database(codes)
    
    # 显示部分结果
    print("\n部分院校代码示例:")
    for i, (name, info) in enumerate(list(codes.items())[:10]):
        print(f"  {name}: {info['code']}")
