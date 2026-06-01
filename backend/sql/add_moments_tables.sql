-- 树洞瞬间功能数据库表（类似Soul瞬间）
-- 创建时间：2026-04-21

-- ========================================
-- 表1：user_moments（用户瞬间/树洞表）
-- ========================================
CREATE TABLE IF NOT EXISTS user_moments (
  id BIGINT NOT NULL AUTO_INCREMENT,
  user_id BIGINT NOT NULL,                    -- 发布者
  content TEXT NOT NULL,                      -- 瞬间内容
  mood_tag VARCHAR(50) DEFAULT NULL,          -- 心情标签（如：开心、焦虑、期待等）
  
  -- 定位信息
  location_name VARCHAR(200) DEFAULT NULL,    -- 位置名称
  province VARCHAR(50) DEFAULT NULL,          -- 省份
  city VARCHAR(50) DEFAULT NULL,              -- 城市
  district VARCHAR(50) DEFAULT NULL,          -- 区县
  latitude DECIMAL(10, 6) DEFAULT NULL,       -- 纬度
  longitude DECIMAL(10, 6) DEFAULT NULL,      -- 经度
  
  -- 统计
  like_count INT NOT NULL DEFAULT 0,          -- 点赞数
  comment_count INT NOT NULL DEFAULT 0,       -- 评论数
  view_count INT NOT NULL DEFAULT 0,          -- 浏览数
  
  status ENUM('active', 'hidden', 'deleted') NOT NULL DEFAULT 'active',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_user_moments_user (user_id, status),
  KEY idx_user_moments_created (status, created_at DESC),
  KEY idx_user_moments_location (province, city, status),
  KEY idx_user_moments_mood (mood_tag, status),
  CONSTRAINT fk_user_moments_user FOREIGN KEY (user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户瞬间/树洞';

-- ========================================
-- 表2：moment_images（瞬间图片表）
-- ========================================
CREATE TABLE IF NOT EXISTS moment_images (
  id BIGINT NOT NULL AUTO_INCREMENT,
  moment_id BIGINT NOT NULL,
  image_url VARCHAR(500) NOT NULL,
  sort_order INT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_moment_images_moment (moment_id, sort_order),
  CONSTRAINT fk_moment_images_moment FOREIGN KEY (moment_id) REFERENCES user_moments (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='瞬间图片';

-- ========================================
-- 表3：moment_likes（瞬间点赞表）
-- ========================================
CREATE TABLE IF NOT EXISTS moment_likes (
  id BIGINT NOT NULL AUTO_INCREMENT,
  moment_id BIGINT NOT NULL,
  user_id BIGINT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_moment_like (moment_id, user_id),
  KEY idx_moment_likes_user (user_id),
  CONSTRAINT fk_moment_likes_moment FOREIGN KEY (moment_id) REFERENCES user_moments (id) ON DELETE CASCADE,
  CONSTRAINT fk_moment_likes_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='瞬间点赞';

-- ========================================
-- 表4：moment_comments（瞬间评论表）
-- ========================================
CREATE TABLE IF NOT EXISTS moment_comments (
  id BIGINT NOT NULL AUTO_INCREMENT,
  moment_id BIGINT NOT NULL,
  user_id BIGINT NOT NULL,                    -- 评论者
  content VARCHAR(500) NOT NULL,              -- 评论内容
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_moment_comments_moment (moment_id, created_at),
  KEY idx_moment_comments_user (user_id),
  CONSTRAINT fk_moment_comments_moment FOREIGN KEY (moment_id) REFERENCES user_moments (id) ON DELETE CASCADE,
  CONSTRAINT fk_moment_comments_user FOREIGN KEY (user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='瞬间评论';

-- ========================================
-- 验证创建
-- ========================================
SHOW TABLES LIKE 'moment_%';
SHOW TABLES LIKE 'user_moments';
