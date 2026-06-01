"""
检查多个院校的标签信息
"""
import requests
from bs4 import BeautifulSoup

url = "https://yz.chsi.com.cn/sch/?start=0"

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
}

response = requests.get(url, headers=headers, timeout=30)
response.encoding = 'utf-8'

soup = BeautifulSoup(response.text, 'html.parser')

items = soup.select('div.sch-item')
print(f"共找到 {len(items)} 个院校\n")

for i, item in enumerate(items[:5]):
    name_elem = item.select_one('a.name')
    name = name_elem.get_text(strip=True) if name_elem else "未知"
    
    dept_elem = item.select_one('div.sch-department')
    dept_text = dept_elem.get_text(strip=True) if dept_elem else ""
    
    tags = item.select('span.sch-tag')
    tag_texts = [t.get_text(strip=True) for t in tags]
    
    print(f"{i+1}. {name}")
    print(f"   地区/主管部门: {dept_text}")
    print(f"   标签: {tag_texts}")
    print()
