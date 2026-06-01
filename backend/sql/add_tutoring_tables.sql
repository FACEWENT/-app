-- 问题咨询功能数据库表
-- 创建时间：2026-04-21

-- ========================================
-- 表1：user_target_schools（用户目标院校表）
-- ========================================
CREATE TABLE IF NOT EXISTS user_target_schools (
  id BIGINT NOT NULL AUTO_INCREMENT,
  user_id BIGINT NOT NULL,                    -- 用户ID
  school_id BIGINT NOT NULL,                  -- 目标学校ID
  school_name VARCHAR(100) NOT NULL,          -- 学校名称
  major_id BIGINT DEFAULT NULL,               -- 目标专业ID
  major_code VARCHAR(20) DEFAULT NULL,        -- 专业代码
  major_name VARCHAR(100) DEFAULT NULL,       -- 专业名称
  exam_year INT NOT NULL,                     -- 考研年份
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_user_target_schools_user (user_id),
  KEY idx_user_target_schools_school (school_id),
  KEY idx_user_target_schools_major (major_id),
  CONSTRAINT fk_user_target_schools_user FOREIGN KEY (user_id) REFERENCES users (id),
  CONSTRAINT fk_user_target_schools_school FOREIGN KEY (school_id) REFERENCES schools (id),
  CONSTRAINT fk_user_target_schools_major FOREIGN KEY (major_id) REFERENCES majors (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户目标院校';

-- ========================================
-- 表2：tutoring_posts（教学信息帖子表）
-- ========================================
CREATE TABLE IF NOT EXISTS tutoring_posts (
  id BIGINT NOT NULL AUTO_INCREMENT,
  user_id BIGINT NOT NULL,                    -- 发布者
  school_id BIGINT NOT NULL,                  -- 目标学校
  major_id BIGINT DEFAULT 0,                  -- 目标专业（0表示不限）
  
  -- 教学信息
  subject_type ENUM('math', 'english', 'politics', 'professional') NOT NULL, -- 科目类型
  subject_name VARCHAR(50) NOT NULL,          -- 科目名称
  title VARCHAR(200) NOT NULL,                -- 标题
  content TEXT NOT NULL,                      -- 详细介绍
  
  -- 教师信息
  current_school VARCHAR(100) DEFAULT NULL,   -- 就读学校
  current_major VARCHAR(100) DEFAULT NULL,    -- 就读专业
  exam_score INT DEFAULT NULL,                -- 考研总分
  subject_score INT DEFAULT NULL,             -- 该科目分数
  bio TEXT DEFAULT NULL,                      -- 个人介绍
  
  -- 交易信息
  price DECIMAL(10,2) NOT NULL,               -- 价格（元/小时或元/套）
  teaching_mode ENUM('online', 'offline', 'both') DEFAULT 'online', -- 教学方式
  contact_info VARCHAR(200) DEFAULT NULL,     -- 联系方式
  
  -- 统计
  status ENUM('active', 'hidden', 'deleted') NOT NULL DEFAULT 'active',
  view_count INT NOT NULL DEFAULT 0,
  like_count INT NOT NULL DEFAULT 0,
  order_count INT NOT NULL DEFAULT 0,         -- 订单数
  
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_tutoring_posts_school_major (school_id, major_id),
  KEY idx_tutoring_posts_subject (subject_type, status),
  KEY idx_tutoring_posts_user (user_id, status),
  KEY idx_tutoring_posts_price (price),
  KEY idx_tutoring_posts_created (created_at DESC),
  CONSTRAINT fk_tutoring_posts_user FOREIGN KEY (user_id) REFERENCES users (id),
  CONSTRAINT fk_tutoring_posts_school FOREIGN KEY (school_id) REFERENCES schools (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='教学信息帖子';

-- ========================================
-- 表3：tutoring_post_images（教学帖子图片表）
-- ========================================
CREATE TABLE IF NOT EXISTS tutoring_post_images (
  id BIGINT NOT NULL AUTO_INCREMENT,
  post_id BIGINT NOT NULL,
  image_url VARCHAR(500) NOT NULL,
  image_type ENUM('avatar', 'certificate', 'note', 'other') DEFAULT 'other',
  sort_order INT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_tutoring_post_images_post (post_id, sort_order),
  CONSTRAINT fk_tutoring_post_images_post FOREIGN KEY (post_id) REFERENCES tutoring_posts (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='教学帖子图片';

-- ========================================
-- 表4：tutoring_post_likes（教学帖子点赞表）
-- ========================================
CREATE TABLE IF NOT EXISTS tutoring_post_likes (
  id BIGINT NOT NULL AUTO_INCREMENT,
  post_id BIGINT NOT NULL,
  user_id BIGINT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_tutoring_like (post_id, user_id),
  KEY idx_tutoring_post_likes_user (user_id),
  CONSTRAINT fk_tutoring_post_likes_post FOREIGN KEY (post_id) REFERENCES tutoring_posts (id) ON DELETE CASCADE,
  CONSTRAINT fk_tutoring_post_likes_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='教学帖子点赞';

-- ========================================
-- 验证创建
-- ========================================
SHOW TABLES LIKE '%target%';
SHOW TABLES LIKE 'tutoring_%';
