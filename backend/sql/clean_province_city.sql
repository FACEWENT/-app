-- 清洗schools表的province和city字段
-- 执行时间：2026-04-20
-- 目的：province只保留省/自治区/直辖市，city只保留市/州名

-- ========================================
-- 步骤1：清洗包含"省+市"格式的province
-- ========================================
-- 例如："浙江省杭州市" -> "浙江省"
UPDATE schools 
SET province = CONCAT(SUBSTRING_INDEX(province, '省', 1), '省')
WHERE province LIKE '%省%市%';

-- ========================================
-- 步骤2：清洗包含"自治区+市"格式的province
-- ========================================
-- 例如："内蒙古自治区呼和浩特市" -> "内蒙古自治区"
UPDATE schools 
SET province = CONCAT(SUBSTRING_INDEX(province, '自治区', 1), '自治区')
WHERE province LIKE '%自治区%市%';

-- ========================================
-- 步骤3：清洗自治州的province（特殊情况）
-- ========================================
-- 例如："吉林省延边朝鲜族自治州" -> "吉林省"
UPDATE schools 
SET province = CASE
    WHEN province LIKE '吉林%' THEN '吉林省'
    WHEN province LIKE '云南%' THEN '云南省'
    WHEN province LIKE '湖南%' THEN '湖南省'
    ELSE province
END
WHERE province LIKE '%自治州%';

-- ========================================
-- 步骤4：清洗包含"省+市"格式的city
-- ========================================
-- 例如："浙江省杭州市" -> "杭州市"
UPDATE schools 
SET city = SUBSTRING_INDEX(city, '省', -1)
WHERE city LIKE '%省%市%';

-- ========================================
-- 步骤5：清洗包含"自治区+市"格式的city
-- ========================================
UPDATE schools 
SET city = SUBSTRING_INDEX(city, '自治区', -1)
WHERE city LIKE '%自治区%市%' AND city NOT LIKE '%市%市%';

-- ========================================
-- 步骤6：清洗自治州的city（特殊情况）
-- ========================================
UPDATE schools 
SET city = CASE
    WHEN city LIKE '%延边朝鲜族自治州' THEN '延边朝鲜族自治州'
    WHEN city LIKE '%大理白族自治州' THEN '大理白族自治州'
    WHEN city LIKE '%湘西土家族苗族自治州' THEN '湘西土家族苗族自治州'
    ELSE city
END
WHERE city LIKE '%自治州%';

-- ========================================
-- 步骤7：验证结果
-- ========================================

-- 查看清洗后的示例数据
SELECT id, school_name, province, city 
FROM schools 
LIMIT 20;

-- 查看不同的province值
SELECT DISTINCT province, COUNT(*) as cnt 
FROM schools 
GROUP BY province 
ORDER BY cnt DESC;

-- 查看不同的city值
SELECT DISTINCT city, COUNT(*) as cnt 
FROM schools 
GROUP BY city 
ORDER BY cnt DESC;
