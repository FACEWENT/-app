# 考研招生数据获取完整方案

## 现状分析

当前数据库中：
- 2025年招生记录: 1088条
- 2024年招生记录: 172条
- 缺少2023年及更早的数据
- 部分字段为空（考试科目、学费、报录比等）

## 数据获取方案

### 方案一：研招网硕士专业目录爬取（推荐）

**数据来源**: https://yz.chsi.com.cn/zsml/

**可获取数据**:
- 招生专业目录
- 考试科目
- 招生人数（拟招生）
- 学习方式（全日制/非全日制）
- 院系信息

**爬虫脚本**: `scripts/crawl_enrollment_data.py`

**优点**: 
- 数据权威、格式统一
- 覆盖全国所有招生院校
- 包含完整的专业目录

**缺点**:
- 研招网有反爬机制
- 需要控制爬取频率
- 可能需要进行验证码识别

### 方案二：各院校研究生招生官网爬取

**数据来源**: 各院校研究生招生信息网

**可获取数据**:
- 招生简章/章程
- 复试分数线
- 报录比
- 学费标准
- 参考书目

**爬虫脚本**: `scripts/crawl_school_websites.py`

**优点**:
- 数据最详细
- 包含分数线、报录比等关键信息

**缺点**:
- 各网站结构差异大
- 需要针对每个网站编写解析器
- 维护成本高

### 方案三：公开数据集 + 手动整理（最实用）

**数据来源**:
1. **中国教育在线**: https://kaoyan.eol.cn
2. **考研帮**: http://www.kaoyan.com
3. **各院校研究生院官网**
4. **教育部公开数据**

**可获取数据**:
- 历年分数线
- 报录比统计
- 招生人数变化
- 学费信息

**导入工具**: `scripts/batch_import_enrollment.py`

**优点**:
- 数据质量高
- 可以人工校验
- 格式统一

**缺点**:
- 需要手动整理
- 工作量较大

## 推荐实施方案

### 第一阶段：补充2023-2025年核心数据

1. **使用批量导入工具**
   ```bash
   # 生成示例CSV
   python scripts/batch_import_enrollment.py --sample
   
   # 整理数据后导入
   python scripts/batch_import_enrollment.py your_data.csv
   ```

2. **CSV格式要求**:
   ```csv
   school_code,school_name,major_code,major_name,exam_year,degree_type,
   study_mode,department_name,planned_enrollment,actual_enrollment,
   application_count,retest_ratio,tuition_fee,exam_subjects
   ```

### 第二阶段：自动化爬取更新

1. **定期运行研招网爬虫**（每月一次）
   ```bash
   python scripts/crawl_enrollment_data.py
   ```

2. **监控数据完整性**
   ```bash
   python scripts/generate_data_report.py
   ```

### 第三阶段：数据校验与补充

1. **对比多个数据源**
2. **人工校验关键数据**
3. **建立数据更新机制**

## 数据完整性检查SQL

```sql
-- 检查各年份数据量
SELECT exam_year, COUNT(*) as count 
FROM enrollment_records 
GROUP BY exam_year 
ORDER BY exam_year DESC;

-- 检查缺失关键字段的记录
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN exam_subjects IS NULL THEN 1 ELSE 0 END) as missing_subjects,
    SUM(CASE WHEN planned_enrollment IS NULL THEN 1 ELSE 0 END) as missing_enrollment,
    SUM(CASE WHEN tuition_fee IS NULL THEN 1 ELSE 0 END) as missing_tuition
FROM enrollment_records;

-- 检查各院校数据覆盖度
SELECT 
    s.school_name,
    COUNT(DISTINCT er.exam_year) as year_count,
    COUNT(er.id) as record_count
FROM schools s
LEFT JOIN enrollment_records er ON s.id = er.school_id
WHERE s.is_985 = 1
GROUP BY s.id
ORDER BY year_count ASC
LIMIT 20;
```

## 建议的数据获取优先级

1. **P0 - 必须获取**:
   - 2023-2025年招生专业目录
   - 考试科目
   - 招生人数

2. **P1 - 重要数据**:
   - 复试分数线（国家线、院校线）
   - 学费标准
   - 学习方式

3. **P2 - 补充数据**:
   - 报录比
   - 实际录取人数
   - 参考书目

## 注意事项

1. **爬取频率**: 控制请求频率，避免被封IP
2. **数据校验**: 多源对比，确保数据准确性
3. **版权声明**: 仅用于个人学习和研究
4. **定期更新**: 每年考研数据公布后及时更新

## 后续优化建议

1. 建立数据质量监控机制
2. 实现自动化数据更新pipeline
3. 增加数据异常检测和告警
4. 提供数据导出和备份功能
