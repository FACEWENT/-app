# kaoyan_system_v2 报表逻辑说明

这套报表围绕 3 个目标设计：

- 业务运营：看学校、专业、招生竞争度
- 用户增长：看收藏、浏览、AI 使用情况
- AI 产品：看会话、推荐方案、冲稳保产出效果

## 使用顺序

1. 先执行 [kaoyan_system_v2_fresh_schema.sql](/Users/face/Desktop/grad-school-data-system/backend/sql/kaoyan_system_v2_fresh_schema.sql)
2. 再执行 [kaoyan_system_v2_reporting.sql](/Users/face/Desktop/grad-school-data-system/backend/sql/kaoyan_system_v2_reporting.sql)
3. 然后在 DBeaver 或后端 API 中查询这些视图

## 报表视图

### 1. `vw_report_dashboard_overview`

总览大盘：

- 活跃学校数
- 活跃专业数
- 招生记录数
- 分数线记录数
- 活跃用户数
- AI 会话数
- AI 方案数
- 平均报录比
- 平均复试比
- 学校平均热度

适合首页仪表盘。

### 2. `vw_report_school_competitiveness`

学校竞争力报表：

- 学校层次
- 省市
- 覆盖专业数
- 招生记录数
- 平均招生人数
- 平均报录比
- 平均复试线
- 平均录取最低分、平均分、最高分

适合学校排行榜、热门院校榜单。

### 3. `vw_report_major_heat`

专业热度与竞争报表：

- 专业代码、名称、学硕/专硕
- 覆盖学校数
- 招生记录数
- 平均计划招生
- 平均报名人数
- 平均报录比
- 平均复试线
- 平均录取分

适合专业热榜、专业竞争度分析。

### 4. `vw_report_province_distribution`

地域分布报表：

- 每个省份的学校数
- 招生项目数
- 专业覆盖数
- 平均学校排名
- 平均热度
- 平均报录比
- 平均复试线

适合地域择校图谱。

### 5. `vw_report_score_trends`

分数趋势报表：

- 按年份
- 按专业
- 按省份
- 查看复试线和录取分趋势

适合折线图和趋势分析。

### 6. `vw_report_user_activity`

用户活跃报表：

- 收藏数
- 浏览数
- AI 会话数
- 生成方案数
- 最近浏览时间
- 最近 AI 使用时间

适合用户运营后台。

### 7. `vw_report_ai_session_effectiveness`

AI 效果报表：

- 会话类型
- 用户消息数
- 助手消息数
- 推荐消息数
- 生成方案数
- 生成方案明细数

适合分析 AI 功能使用深度。

### 8. `vw_report_recommendation_summary`

推荐方案报表：

- 每个方案的冲稳保数量
- 平均 AI 评分
- 平均分差

适合查看 AI 方案产出质量。

## 常用查询示例

### 查看学校竞争力前 20

```sql
SELECT *
FROM vw_report_school_competitiveness
ORDER BY avg_application_admission_ratio DESC, avg_retest_total_score DESC
LIMIT 20;
```

### 查看热门专业前 20

```sql
SELECT *
FROM vw_report_major_heat
ORDER BY school_count DESC, avg_application_count DESC
LIMIT 20;
```

### 查看某个专业近年趋势

```sql
SELECT *
FROM vw_report_score_trends
WHERE major_code = '085404'
ORDER BY exam_year ASC;
```

### 查看 AI 使用最活跃用户

```sql
SELECT *
FROM vw_report_user_activity
ORDER BY ai_session_count DESC, recommendation_plan_count DESC
LIMIT 20;
```
