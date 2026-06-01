"""
性能优化验证测试
测试分页查询、索引效果、缓存效果
"""
import time
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.db import fetch_all, fetch_one
from app.core.cache import cache, cached
from app.services.catalog import list_institutions, list_programs, list_offerings, build_filters


def test_pagination_performance():
    """测试分页查询性能"""
    print("=" * 60)
    print("测试1：分页查询性能")
    print("=" * 60)
    
    # 测试院校列表分页
    start = time.time()
    result = list_institutions(page=1, page_size=20)
    duration = (time.time() - start) * 1000
    print(f"\n院校列表第1页（20条）：{duration:.2f}ms，总数：{result['total']}")
    
    # 测试专业列表分页（优化后应该是数据库分页）
    start = time.time()
    result = list_programs(page=1, page_size=20)
    duration = (time.time() - start) * 1000
    print(f"专业列表第1页（20条）：{duration:.2f}ms，总数：{result['total']}")
    
    # 测试招生记录分页
    start = time.time()
    result = list_offerings(page=1, page_size=20)
    duration = (time.time() - start) * 1000
    print(f"招生记录第1页（20条）：{duration:.2f}ms，总数：{result['total']}")


def test_cache_performance():
    """测试缓存性能"""
    print("\n" + "=" * 60)
    print("测试2：缓存效果")
    print("=" * 60)
    
    # 清除缓存
    cache.clear()
    
    # 第一次调用（无缓存）
    start = time.time()
    result1 = build_filters()
    duration1 = (time.time() - start) * 1000
    print(f"\nbuild_filters() 第1次（无缓存）：{duration1:.2f}ms")
    
    # 第二次调用（有缓存）
    start = time.time()
    result2 = build_filters()
    duration2 = (time.time() - start) * 1000
    print(f"build_filters() 第2次（有缓存）：{duration2:.2f}ms")
    
    # 计算加速比
    speedup = duration1 / duration2 if duration2 > 0 else float('inf')
    print(f"加速比：{speedup:.1f}x")


def test_complex_query():
    """测试复杂查询性能"""
    print("\n" + "=" * 60)
    print("测试3：复杂条件查询")
    print("=" * 60)
    
    # 多条件筛选
    start = time.time()
    result = list_institutions(
        keyword="",
        province="北京",
        school_level="985",
        page=1,
        page_size=20
    )
    duration = (time.time() - start) * 1000
    print(f"\n北京985院校查询：{duration:.2f}ms，结果：{result['total']}条")
    
    # 专业筛选
    start = time.time()
    result = list_programs(
        keyword="计算机",
        degree_type="academic",
        page=1,
        page_size=20
    )
    duration = (time.time() - start) * 1000
    print(f"计算机学术型专业查询：{duration:.2f}ms，结果：{result['total']}条")


def main():
    print("\n性能优化验证测试")
    print("=" * 60)
    
    test_pagination_performance()
    test_cache_performance()
    test_complex_query()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
