"""
从研招网爬取硕士招生专业目录和历年招生信息
包括：考试科目、招生人数、复试分数线等
"""
import time
import requests
from bs4 import BeautifulSoup
import pymysql
import re
import json
from urllib.parse import urljoin, urlencode
from typing import Dict, List, Optional

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


class EnrollmentDataSpider:
    """招生数据爬虫"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.conn = None
        
    def connect_db(self):
        """连接数据库"""
        self.conn = pymysql.connect(**DB_CONFIG, charset='utf8mb4')
        
    def close_db(self):
        """关闭数据库"""
        if self.conn:
            self.conn.close()
    
    def get_school_list_from_db(self) -> List[Dict]:
        """从数据库获取院校列表"""
        cursor = self.conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("""
            SELECT id, school_name, school_code, province, city
            FROM schools 
            WHERE status = 'active' AND school_code IS NOT NULL
            ORDER BY school_code
        """)
        return cursor.fetchall()
    
    def get_major_list_from_db(self) -> List[Dict]:
        """从数据库获取专业列表"""
        cursor = self.conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("""
            SELECT id, major_code, major_name, discipline_code
            FROM majors
            WHERE is_active = 1
        """)
        return cursor.fetchall()
    
    def crawl_zsml_page(self, ssdm: str, dwdm: str, yjfxdm: str = '', 
                       xxfsdm: str = '', size: int = 20, page: int = 1) -> Optional[Dict]:
        """
        爬取硕士专业目录页
        ssdm: 省市代码
        dwdm: 单位代码（院校代码）
        yjfxdm: 一级学科代码
        xxfsdm: 学习方式代码
        """
        url = f"{BASE_URL}/zsml/code/list"
        params = {
            'ssdm': ssdm,
            'dwdm': dwdm,
            'yjfxdm': yjfxdm,
            'xxfsdm': xxfsdm,
            'size': size,
            'page': page,
        }
        
        try:
            response = self.session.post(url, data=params, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"  [ERROR] 请求失败: {e}")
        
        return None
    
    def parse_zsml_data(self, zsml_data: Dict, school_id: int, exam_year: int = 2025) -> List[Dict]:
        """解析专业目录数据"""
        results = []
        
        if not zsml_data or 'data' not in zsml_data:
            return results
        
        for item in zsml_data['data']:
            try:
                # 提取专业信息
                major_info = {
                    'school_id': school_id,
                    'major_code': item.get('zymc', ''),  # 专业名称
                    'major_name': item.get('zymc', ''),
                    'exam_year': exam_year,
                    'degree_type': 'professional' if item.get('xxfsdm') == '2' else 'academic',
                    'study_mode': 'full_time',
                    'department_name': item.get('yxsmc', ''),  # 院系名称
                    'research_direction': item.get('yjfxmc', ''),  # 研究方向
                    'planned_enrollment': item.get('zsrs', ''),  # 招生人数
                    'exam_subjects': item.get('kskm', ''),  # 考试科目
                    'data_source': '研招网',
                }
                
                results.append(major_info)
                
            except Exception as e:
                print(f"  [WARN] 解析专业数据失败: {e}")
                continue
        
        return results
    
    def crawl_school_enrollment(self, school: Dict, exam_year: int = 2025) -> List[Dict]:
        """爬取单个院校的招生信息"""
        school_name = school['school_name']
        school_code = school['school_code']
        school_id = school['id']
        
        # 省市代码映射（简化版）
        province_code_map = {
            '北京': '11', '天津': '12', '上海': '31', '重庆': '50',
            '河北': '13', '山西': '14', '辽宁': '21', '吉林': '22',
            '黑龙江': '23', '江苏': '32', '浙江': '33', '安徽': '34',
            '福建': '35', '江西': '36', '山东': '37', '河南': '41',
            '湖北': '42', '湖南': '43', '广东': '44', '海南': '46',
            '四川': '51', '贵州': '52', '云南': '53', '陕西': '61',
            '甘肃': '62', '青海': '63', '内蒙古': '15', '广西': '45',
            '西藏': '54', '宁夏': '64', '新疆': '65',
        }
        
        ssdm = province_code_map.get(school['province'], '11')
        
        print(f"\n  爬取 {school_name} ({school_code}) {exam_year}年招生信息...")
        
        all_enrollment = []
        page = 1
        
        while page <= 10:  # 最多爬取10页
            zsml_data = self.crawl_zsml_page(ssdm, school_code, page=page)
            
            if not zsml_data or not zsml_data.get('data'):
                break
            
            enrollment = self.parse_zsml_data(zsml_data, school_id, exam_year)
            all_enrollment.extend(enrollment)
            
            # 检查是否还有下一页
            if len(zsml_data['data']) < 20:
                break
            
            page += 1
            time.sleep(1)  # 避免过快
        
        print(f"  ✓ 爬取到 {len(all_enrollment)} 条招生记录")
        return all_enrollment
    
    def save_enrollment_data(self, enrollment_list: List[Dict]):
        """保存招生数据到数据库"""
        if not enrollment_list:
            return
        
        cursor = self.conn.cursor()
        inserted = 0
        
        for item in enrollment_list:
            try:
                # 检查是否已存在
                cursor.execute("""
                    SELECT id FROM enrollment_records 
                    WHERE school_id = %s AND exam_year = %s AND department_name = %s
                    AND planned_enrollment = %s
                """, (
                    item['school_id'],
                    item['exam_year'],
                    item.get('department_name', ''),
                    item.get('planned_enrollment', 0)
                ))
                
                if cursor.fetchone():
                    continue  # 已存在，跳过
                
                # 插入新记录
                cursor.execute("""
                    INSERT INTO enrollment_records (
                        school_id, major_id, exam_year, degree_type, study_mode,
                        department_name, research_direction, planned_enrollment,
                        exam_subjects, data_source
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    item['school_id'],
                    0,  # major_id 暂时为0，后续可关联
                    item['exam_year'],
                    item.get('degree_type', 'academic'),
                    item.get('study_mode', 'full_time'),
                    item.get('department_name', ''),
                    item.get('research_direction', ''),
                    item.get('planned_enrollment', 0),
                    json.dumps(item.get('exam_subjects', ''), ensure_ascii=False),
                    item.get('data_source', '研招网')
                ))
                
                inserted += 1
                
            except Exception as e:
                print(f"  [ERROR] 保存数据失败: {e}")
                continue
        
        self.conn.commit()
        print(f"  ✓ 新增 {inserted} 条记录")
    
    def crawl_all_schools(self, exam_year: int = 2025, limit: int = None):
        """爬取所有院校的招生信息"""
        self.connect_db()
        
        schools = self.get_school_list_from_db()
        if limit:
            schools = schools[:limit]
        
        print(f"=" * 60)
        print(f"开始爬取 {len(schools)} 所院校的 {exam_year} 年招生信息")
        print(f"=" * 60)
        
        total_enrollment = 0
        
        for i, school in enumerate(schools):
            print(f"\n[{i+1}/{len(schools)}]", end='')
            
            enrollment = self.crawl_school_enrollment(school, exam_year)
            if enrollment:
                self.save_enrollment_data(enrollment)
                total_enrollment += len(enrollment)
            
            # 每爬取10所院校休息一次
            if (i + 1) % 10 == 0:
                print("  休息5秒...")
                time.sleep(5)
        
        print(f"\n{'=' * 60}")
        print(f"爬取完成！共获取 {total_enrollment} 条招生记录")
        print(f"{'=' * 60}")
        
        self.close_db()


def main():
    """主函数"""
    spider = EnrollmentDataSpider()
    
    # 先爬取少量院校测试
    print("开始测试爬取前5所院校...")
    spider.crawl_all_schools(exam_year=2025, limit=5)
    
    # 测试成功后，可以爬取全部
    # spider.crawl_all_schools(exam_year=2025)


if __name__ == "__main__":
    main()
