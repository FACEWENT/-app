-- 灵魂匹配功能数据库表（类似Soul灵魂匹配）
-- 创建时间：2026-04-21

-- ========================================
-- 表1：soul_matching_preferences（用户匹配偏好表）
-- ========================================
CREATE TABLE IF NOT EXISTS soul_matching_preferences (
  id BIGINT NOT NULL AUTO_INCREMENT,
  user_id BIGINT NOT NULL,                    -- 用户ID
  
  -- 基本要求
  gender_preference VARCHAR(20) DEFAULT 'any', -- 性别偏好（any/male/female）
  age_min INT DEFAULT NULL,                   -- 最小年龄
  age_max INT DEFAULT NULL,                   -- 最大年龄
  
  -- 考研相关
  exam_year INT DEFAULT NULL,                 -- 考研年份
  target_major VARCHAR(100) DEFAULT NULL,     -- 目标专业
  target_school_level VARCHAR(50) DEFAULT NULL, -- 目标学校层次（985/211/双非）
  target_degree_type VARCHAR(20) DEFAULT NULL,  -- 学位类型（学硕/专硕）
  
  -- 兴趣爱好
  study_style VARCHAR(50) DEFAULT NULL,       -- 学习风格（早起型/夜猫子/均衡型）
  personality_type VARCHAR(50) DEFAULT NULL,  -- 性格类型（内向/外向/均衡）
  study_intensity VARCHAR(20) DEFAULT NULL,   -- 学习强度（轻松/适中/高强度）
  
  -- 匹配设置
  preferred_provinces JSON DEFAULT NULL,      -- 偏好省份
  online_only TINYINT(1) NOT NULL DEFAULT 0,  -- 仅线上交流
  
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_soul_pref_user (user_id),
  KEY idx_soul_pref_exam_year (exam_year),
  KEY idx_soul_pref_major (target_major),
  CONSTRAINT fk_soul_pref_user FOREIGN KEY (user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='灵魂匹配偏好';

-- ========================================
-- 表2：soul_matching_orders（匹配订单表）
-- ========================================
CREATE TABLE IF NOT EXISTS soul_matching_orders (
  id BIGINT NOT NULL AUTO_INCREMENT,
  user_id BIGINT NOT NULL,                    -- 发起用户
  order_no VARCHAR(50) NOT NULL,              -- 订单号
  price DECIMAL(10,2) NOT NULL,               -- 价格
  status ENUM('pending', 'paid', 'matching', 'completed', 'cancelled') NOT NULL DEFAULT 'pending',
  pay_time DATETIME DEFAULT NULL,             -- 支付时间
  match_time DATETIME DEFAULT NULL,           -- 匹配时间
  completed_time DATETIME DEFAULT NULL,       -- 完成时间
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_soul_order_no (order_no),
  KEY idx_soul_order_user (user_id, status),
  KEY idx_soul_order_created (created_at DESC),
  CONSTRAINT fk_soul_order_user FOREIGN KEY (user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='匹配订单';

-- ========================================
-- 表3：soul_matching_records（匹配记录表）
-- ========================================
CREATE TABLE IF NOT EXISTS soul_matching_records (
  id BIGINT NOT NULL AUTO_INCREMENT,
  order_id BIGINT NOT NULL,                   -- 订单ID
  user_a_id BIGINT NOT NULL,                  -- 用户A
  user_b_id BIGINT NOT NULL,                  -- 用户B（匹配到的用户）
  match_score DECIMAL(5,2) DEFAULT NULL,      -- 匹配分数
  match_dimensions JSON DEFAULT NULL,         -- 匹配维度详情
  status ENUM('pending', 'accepted', 'rejected', 'chatting') NOT NULL DEFAULT 'pending',
  user_a_action ENUM('pending', 'accept', 'reject') DEFAULT 'pending',
  user_b_action ENUM('pending', 'accept', 'reject') DEFAULT 'pending',
  chat_id BIGINT DEFAULT NULL,                -- 关联聊天ID
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_soul_record_order (order_id),
  KEY idx_soul_record_user_a (user_a_id, status),
  KEY idx_soul_record_user_b (user_b_id, status),
  CONSTRAINT fk_soul_record_order FOREIGN KEY (order_id) REFERENCES soul_matching_orders (id),
  CONSTRAINT fk_soul_record_user_a FOREIGN KEY (user_a_id) REFERENCES users (id),
  CONSTRAINT fk_soul_record_user_b FOREIGN KEY (user_b_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='匹配记录';

-- ========================================
-- 表4：soul_matching_questions（匹配问答题库表）
-- ========================================
CREATE TABLE IF NOT EXISTS soul_matching_questions (
  id BIGINT NOT NULL AUTO_INCREMENT,
  question TEXT NOT NULL,                     -- 问题
  option_a VARCHAR(200) NOT NULL,             -- 选项A
  option_b VARCHAR(200) NOT NULL,             -- 选项B
  option_c VARCHAR(200) DEFAULT NULL,         -- 选项C
  category VARCHAR(50) DEFAULT NULL,          -- 分类（性格/学习/生活）
  sort_order INT NOT NULL DEFAULT 0,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_soul_question_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='匹配问答题库';

-- ========================================
-- 插入示例问答题
-- ========================================
INSERT INTO soul_matching_questions (question, option_a, option_b, option_c, category, sort_order) VALUES
('你更喜欢什么样的学习方式？', '独自学习，安静高效', '结伴学习，互相监督', '都可以，看情况', '学习', 1),
('考研期间，你每天学习多长时间？', '6小时以下', '6-10小时', '10小时以上', '学习', 2),
('你是一个什么样的人？', '早起鸟，精力充沛', '夜猫子，晚上效率高', '看当天状态', '性格', 3),
('遇到学习难题时，你通常会？', '自己死磕，独立解决', '立刻问别人', '先自己思考，不行再问', '性格', 4),
('考研期间，你的社交频率是？', '几乎不社交，专心备考', '偶尔和朋友聊天放松', '经常社交，保持状态', '生活', 5),
('你理想的研友关系是？', '纯粹学习伙伴，不聊别的', '好朋友，学习+生活', '互相监督，偶尔聊天', '生活', 6),
('面对考研压力，你通常如何调节？', '运动放松', '听音乐/看电影', '找朋友倾诉', '生活', 7),
('你对研友的性别有偏好吗？', '同性更好交流', '异性互补', '无所谓，看性格', '性格', 8);

-- ========================================
-- 验证创建
-- ========================================
SHOW TABLES LIKE 'soul_%';
