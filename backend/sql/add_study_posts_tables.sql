-- 学习资料互助功能数据库表
-- 创建时间：2026-04-20

-- ========================================
-- 表1：study_posts（学习资料帖子表）
-- ========================================
CREATE TABLE IF NOT EXISTS study_posts (
  id BIGINT NOT NULL AUTO_INCREMENT,
  user_id BIGINT NOT NULL,                    -- 发布者
  title VARCHAR(200) NOT NULL,                -- 标题
  content TEXT NOT NULL,                      -- 详细介绍
  post_type ENUM('book', 'notes', 'video', 'other') NOT NULL DEFAULT 'other', -- 类型
  price DECIMAL(10,2) DEFAULT NULL,           -- 价格（元）
  original_price DECIMAL(10,2) DEFAULT NULL,  -- 原价（元）
  condition_level ENUM('new', 'like_new', 'good', 'fair') DEFAULT NULL, -- 新旧程度
  
  -- 位置信息
  province VARCHAR(50) DEFAULT NULL,          -- 省份
  city VARCHAR(50) DEFAULT NULL,              -- 城市
  detail_address VARCHAR(200) DEFAULT NULL,   -- 详细地址
  latitude DECIMAL(10,7) DEFAULT NULL,        -- 纬度
  longitude DECIMAL(10,7) DEFAULT NULL,       -- 经度
  
  -- 标签和分类
  tags JSON DEFAULT NULL,                     -- 标签 ["考研数学", "英语", "政治"]
  category VARCHAR(50) DEFAULT NULL,          -- 分类：数学、英语、政治、专业课
  
  -- 交易信息
  trade_method ENUM('online', 'offline', 'both') DEFAULT 'both', -- 交易方式
  contact_info VARCHAR(200) DEFAULT NULL,     -- 联系方式
  
  -- 状态
  status ENUM('active', 'sold', 'hidden', 'deleted') NOT NULL DEFAULT 'active',
  view_count INT NOT NULL DEFAULT 0,          -- 浏览次数
  like_count INT NOT NULL DEFAULT 0,          -- 点赞数
  comment_count INT NOT NULL DEFAULT 0,       -- 评论数
  
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_study_posts_user (user_id, status),
  KEY idx_study_posts_type (post_type, status),
  KEY idx_study_posts_category (category, status),
  KEY idx_study_posts_location (province, city, status),
  KEY idx_study_posts_price (price),
  KEY idx_study_posts_created (created_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='学习资料帖子';

-- ========================================
-- 表2：study_post_images（帖子图片表）
-- ========================================
CREATE TABLE IF NOT EXISTS study_post_images (
  id BIGINT NOT NULL AUTO_INCREMENT,
  post_id BIGINT NOT NULL,                    -- 所属帖子
  image_url VARCHAR(500) NOT NULL,            -- 图片URL
  sort_order INT NOT NULL DEFAULT 0,          -- 排序
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_study_post_images_post (post_id, sort_order),
  CONSTRAINT fk_study_post_images_post FOREIGN KEY (post_id) REFERENCES study_posts (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='帖子图片';

-- ========================================
-- 表3：study_post_likes（帖子点赞表）
-- ========================================
CREATE TABLE IF NOT EXISTS study_post_likes (
  id BIGINT NOT NULL AUTO_INCREMENT,
  post_id BIGINT NOT NULL,
  user_id BIGINT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_study_post_likes_unique (post_id, user_id),
  KEY idx_study_post_likes_user (user_id),
  CONSTRAINT fk_study_post_likes_post FOREIGN KEY (post_id) REFERENCES study_posts (id) ON DELETE CASCADE,
  CONSTRAINT fk_study_post_likes_user FOREIGN KEY (user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='帖子点赞';

-- ========================================
-- 验证创建
-- ========================================
SHOW TABLES LIKE 'study_%';

SELECT 'study_posts' AS table_name, COUNT(*) AS row_count FROM study_posts
UNION ALL
SELECT 'study_post_images', COUNT(*) FROM study_post_images
UNION ALL
SELECT 'study_post_likes', COUNT(*) FROM study_post_likes;
