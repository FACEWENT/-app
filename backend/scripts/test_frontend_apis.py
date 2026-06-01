#!/usr/bin/env python3
"""
前端数据接口测试报告
测试所有微信小程序使用的API接口
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_api(endpoint, params=None, description=""):
    """测试单个API"""
    print(f"\n{'='*60}")
    print(f"测试: {description or endpoint}")
    print(f"URL: {BASE_URL}{endpoint}")
    if params:
        print(f"参数: {params}")
    
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 0:
                print(f"✓ 状态: 成功")
                print(f"✓ 返回数据量: {len(data.get('data', {}))} 项")
                
                # 显示部分数据
                if 'items' in data['data']:
                    items = data['data']['items']
                    print(f"✓ 数据条数: {len(items)}")
                    if items:
                        print(f"✓ 示例数据: {json.dumps(items[0], ensure_ascii=False, indent=2)}")
                
                return True
            else:
                print(f"✗ 业务错误: {data.get('message')}")
        else:
            print(f"✗ HTTP错误: {response.status_code}")
            
    except Exception as e:
        print(f"✗ 请求失败: {e}")
    
    return False

def main():
    print("=" * 60)
    print("考研择校调剂系统 - 前端数据接口测试")
    print("=" * 60)
    
    tests = [
        # 院校库相关
        ("/institutions", {"page": 1, "page_size": 5}, "院校列表"),
        ("/institutions/filters", None, "筛选条件"),
        ("/institutions", {"province": "北京", "page": 1, "page_size": 3}, "按省份筛选"),
        ("/institutions", {"school_level": "985", "page": 1, "page_size": 3}, "按层次筛选"),
        ("/institutions", {"discipline_code": "08", "page": 1, "page_size": 3}, "按专业筛选"),
        
        # 院校详情
        ("/institutions/1", None, "院校详情（清华大学）"),
        ("/institutions/1/detail", None, "院校详细数据"),
    ]
    
    success_count = 0
    total_count = len(tests)
    
    for endpoint, params, description in tests:
        if test_api(endpoint, params, description):
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"测试总结: {success_count}/{total_count} 通过")
    print(f"{'='*60}")
    
    if success_count == total_count:
        print("✓ 所有接口正常工作")
    else:
        print("✗ 部分接口存在问题，需要修复")

if __name__ == "__main__":
    main()
