-- 社交功能：匹配网友和聊天
-- 创建时间：2026-04-20

-- ========================================
-- 表1：user_matches（用户匹配记录表）
-- ========================================
CREATE TABLE IF NOT EXISTS user_matches (
  id BIGINT NOT NULL AUTO_INCREMENT,
  user_id BIGINT NOT NULL,                    -- 发起匹配的用户
  matched_user_id BIGINT NOT NULL,            -- 被匹配到的用户
  match_score DECIMAL(5,2) DEFAULT NULL,      -- 匹配分数 0-100
  match_dimensions JSON DEFAULT NULL,         -- 匹配维度详情 {"exam_year": 100, "major": 80, ...}
  status ENUM('pending', 'accepted', 'rejected', 'chatting', 'blocked') NOT NULL DEFAULT 'pending',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_user_matches_unique (user_id, matched_user_id),
  KEY idx_user_matches_user (user_id, status),
  KEY idx_user_matches_matched (matched_user_id, status),
  KEY idx_user_matches_score (match_score DESC),
  CONSTRAINT fk_user_matches_user FOREIGN KEY (user_id) REFERENCES users (id),
  CONSTRAINT fk_user_matches_matched FOREIGN KEY (matched_user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户匹配记录';

-- ========================================
-- 表2：user_chats（聊天会话表）
-- ========================================
CREATE TABLE IF NOT EXISTS user_chats (
  id BIGINT NOT NULL AUTO_INCREMENT,
  user_a_id BIGINT NOT NULL,                  -- 用户A（ID较小）
  user_b_id BIGINT NOT NULL,                  -- 用户B（ID较大）
  last_message TEXT DEFAULT NULL,             -- 最后一条消息
  last_message_at DATETIME DEFAULT NULL,      -- 最后消息时间
  unread_count_a INT NOT NULL DEFAULT 0,      -- 用户A的未读数
  unread_count_b INT NOT NULL DEFAULT 0,      -- 用户B的未读数
  status ENUM('active', 'closed') NOT NULL DEFAULT 'active',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_user_chats_unique (user_a_id, user_b_id),
  KEY idx_user_chats_user_a (user_a_id, status, last_message_at DESC),
  KEY idx_user_chats_user_b (user_b_id, status, last_message_at DESC),
  CONSTRAINT fk_user_chats_a FOREIGN KEY (user_a_id) REFERENCES users (id),
  CONSTRAINT fk_user_chats_b FOREIGN KEY (user_b_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户聊天会话';

-- ========================================
-- 表3：user_messages（聊天消息表）
-- ========================================
CREATE TABLE IF NOT EXISTS user_messages (
  id BIGINT NOT NULL AUTO_INCREMENT,
  chat_id BIGINT NOT NULL,                    -- 所属聊天会话
  sender_id BIGINT NOT NULL,                  -- 发送者
  receiver_id BIGINT NOT NULL,                -- 接收者
  content TEXT NOT NULL,                      -- 消息内容
  message_type ENUM('text', 'image', 'emoji') NOT NULL DEFAULT 'text',
  is_read TINYINT(1) NOT NULL DEFAULT 0,      -- 是否已读
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_user_messages_chat (chat_id, created_at),
  KEY idx_user_messages_sender (sender_id),
  KEY idx_user_messages_receiver (receiver_id, is_read),
  CONSTRAINT fk_user_messages_chat FOREIGN KEY (chat_id) REFERENCES user_chats (id),
  CONSTRAINT fk_user_messages_sender FOREIGN KEY (sender_id) REFERENCES users (id),
  CONSTRAINT fk_user_messages_receiver FOREIGN KEY (receiver_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户聊天消息';

-- ========================================
-- 表4：user_blocks（用户屏蔽表）
-- ========================================
CREATE TABLE IF NOT EXISTS user_blocks (
  id BIGINT NOT NULL AUTO_INCREMENT,
  blocker_id BIGINT NOT NULL,                 -- 屏蔽方
  blocked_id BIGINT NOT NULL,                 -- 被屏蔽方
  reason VARCHAR(255) DEFAULT NULL,           -- 屏蔽原因
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_user_blocks_unique (blocker_id, blocked_id),
  KEY idx_user_blocks_blocker (blocker_id),
  CONSTRAINT fk_user_blocks_blocker FOREIGN KEY (blocker_id) REFERENCES users (id),
  CONSTRAINT fk_user_blocks_blocked FOREIGN KEY (blocked_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户屏蔽列表';

-- ========================================
-- 扩展user_profiles表：添加社交属性字段
-- ========================================

-- 使用存储过程安全地添加列
DELIMITER //

DROP PROCEDURE IF EXISTS add_social_columns//

CREATE PROCEDURE add_social_columns()
BEGIN
    -- 添加 is_visible_to_others
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = DATABASE() 
        AND TABLE_NAME = 'user_profiles' 
        AND COLUMN_NAME = 'is_visible_to_others'
    ) THEN
        ALTER TABLE user_profiles ADD COLUMN is_visible_to_others TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否允许他人看到我';
    END IF;

    -- 添加 bio
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = DATABASE() 
        AND TABLE_NAME = 'user_profiles' 
        AND COLUMN_NAME = 'bio'
    ) THEN
        ALTER TABLE user_profiles ADD COLUMN bio VARCHAR(500) DEFAULT NULL COMMENT '个性签名/自我介绍';
    END IF;

    -- 添加 last_active_at
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = DATABASE() 
        AND TABLE_NAME = 'user_profiles' 
        AND COLUMN_NAME = 'last_active_at'
    ) THEN
        ALTER TABLE user_profiles ADD COLUMN last_active_at DATETIME DEFAULT NULL COMMENT '最后活跃时间';
    END IF;
END//

DELIMITER ;

CALL add_social_columns();
DROP PROCEDURE IF EXISTS add_social_columns;

-- 为现有用户设置默认活跃时间
UPDATE user_profiles 
SET last_active_at = NOW() 
WHERE last_active_at IS NULL;

-- ========================================
-- 创建匹配用户池视图（优化查询性能）
-- ========================================
CREATE OR REPLACE VIEW vw_user_match_pool AS
SELECT 
  u.id AS user_id,
  u.nickname,
  u.avatar_url,
  up.exam_year,
  up.target_degree_type,
  up.target_study_mode,
  up.target_major_code,
  up.target_major_name,
  up.score_total,
  up.undergraduate_school,
  up.preferred_provinces,
  up.preferred_school_levels,
  up.risk_preference,
  up.is_visible_to_others,
  up.bio,
  up.last_active_at
FROM users u
JOIN user_profiles up ON u.id = up.user_id
WHERE u.status = 'active'
  AND up.is_visible_to_others = 1;

-- ========================================
-- 验证创建结果
-- ========================================
SHOW TABLES LIKE 'user_%';

SELECT 'user_matches' AS table_name, COUNT(*) AS row_count FROM user_matches
UNION ALL
SELECT 'user_chats', COUNT(*) FROM user_chats
UNION ALL
SELECT 'user_messages', COUNT(*) FROM user_messages
UNION ALL
SELECT 'user_blocks', COUNT(*) FROM user_blocks;
