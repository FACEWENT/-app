"""
检查研招网页面结构，特别是985/211标签
"""
import requests
from bs4 import BeautifulSoup

url = "https://yz.chsi.com.cn/sch/?start=0"

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

response = requests.get(url, headers=headers, timeout=30)
response.encoding = 'utf-8'

soup = BeautifulSoup(response.text, 'html.parser')

# 查找第一个院校卡片
first_item = soup.select_one('div.sch-item')
if first_item:
    print("=== 第一个院校卡片的完整HTML ===")
    print(first_item.prettify())
    print("\n=== 所有标签 ===")
    tags = first_item.find_all('span')
    for tag in tags:
        print(f"  Class: {tag.get('class')}, Text: {tag.get_text(strip=True)}")
else:
    print("未找到 sch-item，尝试其他选择器...")
    items = soup.select('.sch-list li, table tr')
    if items:
        print(f"找到 {len(items)} 个项目")
        print(items[0].prettify() if items else "无内容")
