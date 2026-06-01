-- 性能优化：添加缺失的关键数据库索引
-- 执行时间：2026-04-20
-- 目的：补充高频查询所需的索引

DELIMITER //

DROP PROCEDURE IF EXISTS add_index//

CREATE PROCEDURE add_index()
BEGIN
    -- 1. 专业表 - 加速按学位类型筛选
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.statistics 
        WHERE table_schema = DATABASE() 
        AND table_name = 'majors' 
        AND index_name = 'idx_majors_degree_type'
    ) THEN
        ALTER TABLE majors ADD INDEX idx_majors_degree_type (degree_type, is_active);
    END IF;

    -- 2. 学校表 - 加速热门学校查询
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.statistics 
        WHERE table_schema = DATABASE() 
        AND table_name = 'schools' 
        AND index_name = 'idx_schools_hot_score'
    ) THEN
        ALTER TABLE schools ADD INDEX idx_schools_hot_score (hot_score DESC, ranking ASC);
    END IF;

    -- 3. 浏览历史表 - 加速热门内容统计
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.statistics 
        WHERE table_schema = DATABASE() 
        AND table_name = 'user_browsing_history' 
        AND index_name = 'idx_browsing_content'
    ) THEN
        ALTER TABLE user_browsing_history ADD INDEX idx_browsing_content (target_type, target_id);
    END IF;

    -- 4. 收藏表 - 加速收藏内容统计
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.statistics 
        WHERE table_schema = DATABASE() 
        AND table_name = 'user_favorites' 
        AND index_name = 'idx_favorites_content'
    ) THEN
        ALTER TABLE user_favorites ADD INDEX idx_favorites_content (favorite_type, target_id);
    END IF;

    -- 5. 分数线表 - 加速按招生记录查询
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.statistics 
        WHERE table_schema = DATABASE() 
        AND table_name = 'score_lines' 
        AND index_name = 'idx_score_lines_enrollment'
    ) THEN
        ALTER TABLE score_lines ADD INDEX idx_score_lines_enrollment (enrollment_record_id);
    END IF;
END//

DELIMITER ;

CALL add_index();
DROP PROCEDURE IF EXISTS add_index;

-- 查看索引创建情况
SELECT 
    table_name,
    index_name,
    GROUP_CONCAT(column_name ORDER BY seq_in_index) AS columns
FROM information_schema.statistics
WHERE table_schema = DATABASE()
GROUP BY table_name, index_name
ORDER BY table_name, index_name;
