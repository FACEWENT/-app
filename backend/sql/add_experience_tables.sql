-- 经验分享（小红书笔记模式）数据库表
-- 创建时间：2026-04-21

-- ========================================
-- 表1：experience_notes（经验笔记表）
-- ========================================
CREATE TABLE IF NOT EXISTS experience_notes (
  id BIGINT NOT NULL AUTO_INCREMENT,
  user_id BIGINT NOT NULL,                    -- 发布者
  title VARCHAR(200) NOT NULL,                -- 标题
  content TEXT NOT NULL,                      -- 正文内容
  
  -- 分类标签
  category VARCHAR(50) DEFAULT NULL,          -- 分类（复习方法、时间规划、心态调整、院校选择等）
  tags JSON DEFAULT NULL,                     -- 标签数组 ["考研", "数学", "复习方法"]
  
  -- 统计
  like_count INT NOT NULL DEFAULT 0,          -- 点赞数
  comment_count INT NOT NULL DEFAULT 0,       -- 评论数
  view_count INT NOT NULL DEFAULT 0,          -- 浏览数
  collect_count INT NOT NULL DEFAULT 0,       -- 收藏数
  
  status ENUM('active', 'hidden', 'deleted') NOT NULL DEFAULT 'active',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_experience_notes_user (user_id, status),
  KEY idx_experience_notes_created (status, created_at DESC),
  KEY idx_experience_notes_category (category, status),
  KEY idx_experience_notes_likes (like_count DESC),
  CONSTRAINT fk_experience_notes_user FOREIGN KEY (user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='经验笔记';

-- ========================================
-- 表2：note_images（笔记图片表）
-- ========================================
CREATE TABLE IF NOT EXISTS note_images (
  id BIGINT NOT NULL AUTO_INCREMENT,
  note_id BIGINT NOT NULL,
  image_url VARCHAR(500) NOT NULL,
  is_cover TINYINT(1) NOT NULL DEFAULT 0,     -- 是否封面图
  sort_order INT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_note_images_note (note_id, sort_order),
  CONSTRAINT fk_note_images_note FOREIGN KEY (note_id) REFERENCES experience_notes (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='笔记图片';

-- ========================================
-- 表3：note_likes（笔记点赞表）
-- ========================================
CREATE TABLE IF NOT EXISTS note_likes (
  id BIGINT NOT NULL AUTO_INCREMENT,
  note_id BIGINT NOT NULL,
  user_id BIGINT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_note_like (note_id, user_id),
  KEY idx_note_likes_user (user_id),
  CONSTRAINT fk_note_likes_note FOREIGN KEY (note_id) REFERENCES experience_notes (id) ON DELETE CASCADE,
  CONSTRAINT fk_note_likes_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='笔记点赞';

-- ========================================
-- 表4：note_comments（笔记评论表）
-- ========================================
CREATE TABLE IF NOT EXISTS note_comments (
  id BIGINT NOT NULL AUTO_INCREMENT,
  note_id BIGINT NOT NULL,
  user_id BIGINT NOT NULL,                    -- 评论者
  content VARCHAR(500) NOT NULL,              -- 评论内容
  parent_id BIGINT DEFAULT NULL,              -- 父评论ID（用于回复）
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_note_comments_note (note_id, created_at),
  KEY idx_note_comments_user (user_id),
  KEY idx_note_comments_parent (parent_id),
  CONSTRAINT fk_note_comments_note FOREIGN KEY (note_id) REFERENCES experience_notes (id) ON DELETE CASCADE,
  CONSTRAINT fk_note_comments_user FOREIGN KEY (user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='笔记评论';

-- ========================================
-- 表5：note_collections（笔记收藏表）
-- ========================================
CREATE TABLE IF NOT EXISTS note_collections (
  id BIGINT NOT NULL AUTO_INCREMENT,
  note_id BIGINT NOT NULL,
  user_id BIGINT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_note_collection (note_id, user_id),
  KEY idx_note_collections_user (user_id),
  CONSTRAINT fk_note_collections_note FOREIGN KEY (note_id) REFERENCES experience_notes (id) ON DELETE CASCADE,
  CONSTRAINT fk_note_collections_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='笔记收藏';

-- ========================================
-- 验证创建
-- ========================================
SHOW TABLES LIKE 'note_%';
SHOW TABLES LIKE 'experience_notes';
