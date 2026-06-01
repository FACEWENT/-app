# 考研招生数据批量导入使用指南

## 快速开始

### 1. 生成示例CSV模板
```bash
cd /Users/face/Desktop/grad-school-data-system/backend
python scripts/batch_import_enrollment.py --sample
```

### 2. 准备你的数据

CSV文件格式要求（第一行为表头）：

```csv
school_code,school_name,major_code,major_name,exam_year,degree_type,study_mode,department_name,planned_enrollment,actual_enrollment,application_count,retest_ratio,tuition_fee,exam_subjects
```

**字段说明**：
- `school_code`: 教育部院校代码（5位），如 10001（北京大学）
- `school_name`: 院校名称
- `major_code`: 专业代码（6位），如 010100（哲学）
- `major_name`: 专业名称
- `exam_year`: 考研年份，如 2025、2024、2023
- `degree_type`: 学位类型，`academic`（学硕）或 `professional`（专硕）
- `study_mode`: 学习方式，`full_time`（全日制）或 `part_time`（非全日制）
- `department_name`: 院系名称
- `planned_enrollment`: 计划招生人数
- `actual_enrollment`: 实际录取人数
- `application_count`: 报考人数
- `retest_ratio`: 复试比例（如 1.2 表示1:1.2）
- `tuition_fee`: 学费（元/年）
- `exam_subjects`: 考试科目（用逗号分隔）

### 3. 导入数据
```bash
python scripts/batch_import_enrollment.py your_data.csv
```

## 数据获取途径

### 推荐数据源

1. **中国教育在线** (https://kaoyan.eol.cn)
   - 院校库：https://kaoyan.eol.cn/school_list
   - 专业库：https://kaoyan.eol.cn/profession_list
   - 分数线：https://kaoyan.eol.cn/kaoyan/ksdj/fsx/

2. **研招网** (https://yz.chsi.com.cn)
   - 硕士目录：https://yz.chsi.com.cn/zsml/
   - 院校库：https://yz.chsi.com.cn/sch/

3. **考研帮** (http://www.kaoyan.com)
   - 院校库
   - 专业库
   - 分数线

4. **各院校研究生招生官网**
   - 招生简章
   - 专业目录
   - 历年分数线
   - 报录比统计

### 数据整理技巧

1. **从Excel导出CSV**：
   - 在Excel中整理好数据
   - 文件 → 另存为 → CSV (UTF-8)

2. **批量获取院校代码**：
   - 已存储在数据库中：`SELECT school_name, school_code FROM schools;`

3. **批量获取专业代码**：
   - 已存储在数据库中：`SELECT major_code, major_name FROM majors;`

## 示例数据

我已经创建了一个示例文件 `sample_enrollment_3years.csv`，包含：
- 北京大学、清华大学、浙江大学、武汉大学等985院校
- 2023-2025三年数据
- 涵盖哲学、经济学、法学、计算机等专业

你可以参考这个格式来整理自己的数据。

## 数据验证

导入后可以使用以下SQL验证数据：

```sql
-- 查看各年份数据量
SELECT exam_year, COUNT(*) as count 
FROM enrollment_records 
GROUP BY exam_year 
ORDER BY exam_year DESC;

-- 查看某院校的完整招生数据
SELECT s.school_name, m.major_name, er.exam_year, 
       er.planned_enrollment, er.actual_enrollment,
       er.application_count, er.retest_ratio
FROM enrollment_records er
JOIN schools s ON s.id = er.school_id
LEFT JOIN majors m ON m.id = er.major_id
WHERE s.school_name = '清华大学'
ORDER BY er.exam_year DESC, m.major_name;

-- 查看数据完整度
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN exam_subjects IS NOT NULL THEN 1 ELSE 0 END) as with_subjects,
    SUM(CASE WHEN planned_enrollment IS NOT NULL THEN 1 ELSE 0 END) as with_enrollment,
    SUM(CASE WHEN tuition_fee IS NOT NULL THEN 1 ELSE 0 END) as with_tuition
FROM enrollment_records;
```

## 常见问题

### Q1: 导入时报错"Cannot add or update a child row"
**A**: 这是因为外键约束。确保：
- 院校代码在 `schools` 表中存在
- 专业代码在 `majors` 表中存在（或设为0）

### Q2: 如何获取历史数据？
**A**: 推荐途径：
1. 中国教育在线 - 历年分数线
2. 考研帮 - 院校库数据
3. 各院校研究生院官网 - 招生简章和历年数据
4. 教育部公开数据

### Q3: 数据导入后可以修改吗？
**A**: 可以。直接使用SQL UPDATE语句修改，或重新导入覆盖。

### Q4: 如何批量更新学费信息？
**A**: 
```sql
UPDATE enrollment_records 
SET tuition_fee = 8000 
WHERE exam_year = 2025 AND degree_type = 'academic';
```

## 下一步优化建议

1. **自动化爬虫**：
   - 定期从研招网同步最新数据
   - 监控各院校官网更新的招生简章

2. **数据校验**：
   - 建立数据异常检测机制
   - 多源数据对比验证

3. **数据补充**：
   - 参考书目信息
   - 导师信息
   - 就业指导数据

4. **用户反馈**：
   - 允许用户纠错
   - 建立数据贡献机制

## 联系与支持

如有问题或建议，请查看：
- 爬虫脚本目录：`backend/scripts/`
- 数据文档：`backend/docs/`
- SQL脚本：`backend/sql/`
