"""
爬取研招网院校详细信息
包括：院校代码、城市、简介等
"""
import time
import requests
from bs4 import BeautifulSoup
import pymysql
import re
from urllib.parse import urljoin

BASE_URL = "https://yz.chsi.com.cn"
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

def get_school_list():
    """从数据库获取需要更新的院校列表"""
    conn = pymysql.connect(**DB_CONFIG, charset='utf8mb4')
    cursor = conn.cursor()
    cursor.execute("SELECT id, school_name FROM schools WHERE status = 'active'")
    schools = cursor.fetchall()
    conn.close()
    return schools

def parse_school_detail(school_id, school_name):
    """解析院校详情页"""
    # 研招网院校详情页URL格式
    url = f"{BASE_URL}/sch/schoolInfo--schId-{school_id}.dhtml"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 提取院校信息
        info = {
            'school_id': school_id,
            'school_name': school_name,
        }
        
        # 查找基本信息区域
        # 通常在页面的特定div中
        info_items = soup.select('.yxk-detail-item, .info-item, dl.yxk-info dd')
        
        for item in info_items:
            text = item.get_text(strip=True)
            if '院校地址' in text or '地址' in text:
                # 提取地址中的城市信息
                address_match = re.search(r'[\u4e00-\u9fa5]+省?[\u4e00-\u9fa5]+市', text)
                if address_match:
                    info['address'] = address_match.group()
            elif '院校类型' in text:
                type_match = re.search(r'院校类型[：:](.+)', text)
                if type_match:
                    info['school_type'] = type_match.group(1).strip()
        
        # 提取简介
        intro_elem = soup.select_one('.yxk-jj, .intro-content, .school-intro')
        if intro_elem:
            info['intro'] = intro_elem.get_text(strip=True)[:500]  # 限制长度
        
        return info
        
    except Exception as e:
        print(f"  [ERROR] 解析失败: {e}")
        return None

def parse_city_from_search():
    """从搜索结果中解析城市信息"""
    # 这个方法通过搜索院校名称来获取更准确的信息
    pass

def batch_update_school_info():
    """批量更新院校信息"""
    conn = pymysql.connect(**DB_CONFIG, charset='utf8mb4')
    cursor = conn.cursor()
    
    # 获取所有院校
    cursor.execute("SELECT id, school_name FROM schools WHERE status = 'active'")
    schools = cursor.fetchall()
    
    print(f"共找到 {len(schools)} 所院校需要更新")
    
    updated = 0
    failed = 0
    
    # 常见院校代码和城市映射（官方数据）
    school_code_mapping = {
        "清华大学": "10003",
        "北京大学": "10001",
        "中国人民大学": "10002",
        "北京交通大学": "10004",
        "北京工业大学": "10005",
        "北京航空航天大学": "10006",
        "北京理工大学": "10007",
        "北京科技大学": "10008",
        "北方工业大学": "10009",
        "北京化工大学": "10010",
        "北京服装学院": "10012",
        "北京邮电大学": "10013",
        "北京印刷学院": "10015",
        "北京建筑大学": "10016",
        "中国农业大学": "10019",
        "北京林业大学": "10022",
        "北京协和医学院": "10023",
        "首都医科大学": "10025",
        "北京中医药大学": "10026",
        "北京师范大学": "10027",
        "首都师范大学": "10028",
        "北京外国语大学": "10030",
        "北京第二外国语学院": "10031",
        "北京语言大学": "10032",
        "中国传媒大学": "10033",
        "中央财经大学": "10034",
        "对外经济贸易大学": "10036",
        "北京物资学院": "10037",
        "首都经济贸易大学": "10038",
        "中国政法大学": "10053",
        "华北电力大学": "10054",
        "中华女子学院": "10055",
        "北京信息科技大学": "10056",
        "中国矿业大学(北京)": "10057",
        "中国石油大学(北京)": "10058",
        "中国地质大学(北京)": "10059",
        "南开大学": "10055",
        "天津大学": "10056",
        # ... 可以添加更多
    }
    
    # 城市映射（基于院校名称和常识）
    city_mapping = {
        "北京": "北京市",
        "上海": "上海市",
        "天津": "天津市",
        "重庆": "重庆市",
        # 河北省
        "河北": "石家庄市",
        "燕山大学": "秦皇岛市",
        "河北大学": "保定市",
        # 山西省
        "山西": "太原市",
        "太原理工大学": "太原市",
        # 内蒙古
        "内蒙古": "呼和浩特市",
        "内蒙古大学": "呼和浩特市",
        # 辽宁省
        "辽宁": "沈阳市",
        "大连理工大学": "大连市",
        "东北大学": "沈阳市",
        "大连海事大学": "大连市",
        # 吉林省
        "吉林": "长春市",
        "吉林大学": "长春市",
        "东北师范大学": "长春市",
        "延边大学": "延吉市",
        # 黑龙江省
        "黑龙江": "哈尔滨市",
        "哈尔滨工业大学": "哈尔滨市",
        "哈尔滨工程大学": "哈尔滨市",
        "东北农业大学": "哈尔滨市",
        "东北林业大学": "哈尔滨市",
        # 江苏省
        "江苏": "南京市",
        "南京大学": "南京市",
        "东南大学": "南京市",
        "南京航空航天大学": "南京市",
        "南京理工大学": "南京市",
        "苏州大学": "苏州市",
        "江南大学": "无锡市",
        "中国矿业大学": "徐州市",
        "河海大学": "南京市",
        "南京农业大学": "南京市",
        "中国药科大学": "南京市",
        "南京师范大学": "南京市",
        # 浙江省
        "浙江": "杭州市",
        "浙江大学": "杭州市",
        # 安徽省
        "安徽": "合肥市",
        "中国科学技术大学": "合肥市",
        "安徽大学": "合肥市",
        "合肥工业大学": "合肥市",
        # 福建省
        "福建": "福州市",
        "厦门大学": "厦门市",
        "福州大学": "福州市",
        # 江西省
        "江西": "南昌市",
        "南昌大学": "南昌市",
        # 山东省
        "山东": "济南市",
        "山东大学": "济南市",
        "中国海洋大学": "青岛市",
        "中国石油大学": "青岛市",
        # 河南省
        "河南": "郑州市",
        "郑州大学": "郑州市",
        # 湖北省
        "湖北": "武汉市",
        "武汉大学": "武汉市",
        "华中科技大学": "武汉市",
        "武汉理工大学": "武汉市",
        "华中师范大学": "武汉市",
        "中南财经政法大学": "武汉市",
        "华中农业大学": "武汉市",
        "中国地质大学": "武汉市",
        # 湖南省
        "湖南": "长沙市",
        "湖南大学": "长沙市",
        "中南大学": "长沙市",
        "湖南师范大学": "长沙市",
        "国防科技大学": "长沙市",
        # 广东省
        "广东": "广州市",
        "中山大学": "广州市",
        "华南理工大学": "广州市",
        "暨南大学": "广州市",
        "华南师范大学": "广州市",
        "深圳大学": "深圳市",
        # 广西
        "广西": "南宁市",
        "广西大学": "南宁市",
        # 海南省
        "海南": "海口市",
        "海南大学": "海口市",
        # 四川省
        "四川": "成都市",
        "四川大学": "成都市",
        "电子科技大学": "成都市",
        "西南交通大学": "成都市",
        "西南财经大学": "成都市",
        "四川农业大学": "雅安市",
        # 贵州省
        "贵州": "贵阳市",
        "贵州大学": "贵阳市",
        # 云南省
        "云南": "昆明市",
        "云南大学": "昆明市",
        # 西藏
        "西藏": "拉萨市",
        "西藏大学": "拉萨市",
        # 陕西省
        "陕西": "西安市",
        "西安交通大学": "西安市",
        "西北工业大学": "西安市",
        "西北农林科技大学": "咸阳市",
        "西安电子科技大学": "西安市",
        "长安大学": "西安市",
        "西北大学": "西安市",
        "陕西师范大学": "西安市",
        # 甘肃省
        "甘肃": "兰州市",
        "兰州大学": "兰州市",
        # 青海省
        "青海": "西宁市",
        "青海大学": "西宁市",
        # 宁夏
        "宁夏": "银川市",
        "宁夏大学": "银川市",
        # 新疆
        "新疆": "乌鲁木齐市",
        "新疆大学": "乌鲁木齐市",
        "石河子大学": "石河子市",
    }
    
    for school_id, school_name in schools:
        try:
            # 更新院校代码
            school_code = school_code_mapping.get(school_name)
            
            # 更新城市
            city = None
            # 先尝试精确匹配
            city = city_mapping.get(school_name)
            if not city:
                # 尝试省份匹配
                for key, value in city_mapping.items():
                    if key in school_name:
                        city = value
                        break
            
            # 执行更新
            if school_code or city:
                update_fields = []
                params = []
                
                if school_code:
                    update_fields.append("school_code = %s")
                    params.append(school_code)
                
                if city:
                    update_fields.append("city = %s")
                    params.append(city)
                
                if update_fields:
                    params.append(school_id)
                    sql = f"UPDATE schools SET {', '.join(update_fields)} WHERE id = %s"
                    cursor.execute(sql, params)
                    updated += 1
            
            if updated % 50 == 0:
                conn.commit()
                print(f"  已更新 {updated} 所院校")
            
            time.sleep(0.1)  # 避免过快
            
        except Exception as e:
            print(f"  [ERROR] 更新 {school_name} 失败: {e}")
            failed += 1
    
    conn.commit()
    print(f"\n更新完成: 成功 {updated}, 失败 {failed}")
    
    conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("开始更新院校代码和城市信息...")
    print("=" * 60)
    batch_update_school_info()
