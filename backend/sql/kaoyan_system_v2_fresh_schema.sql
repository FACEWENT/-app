-- Fresh schema for a graduate-school selection app with stronger AI features.
-- This script creates a brand new database so it will not affect old tables.

CREATE DATABASE IF NOT EXISTS kaoyan_system_v2
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;

USE kaoyan_system_v2;

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS recommendation_plan_items;
DROP TABLE IF EXISTS recommendation_plans;
DROP TABLE IF EXISTS ai_messages;
DROP TABLE IF EXISTS ai_sessions;
DROP TABLE IF EXISTS user_browsing_history;
DROP TABLE IF EXISTS user_favorites;
DROP TABLE IF EXISTS score_lines;
DROP TABLE IF EXISTS enrollment_records;
DROP TABLE IF EXISTS school_majors;
DROP TABLE IF EXISTS school_tags;
DROP TABLE IF EXISTS majors;
DROP TABLE IF EXISTS schools;
DROP TABLE IF EXISTS user_profiles;
DROP TABLE IF EXISTS users;

SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE users (
  id BIGINT NOT NULL AUTO_INCREMENT,
  openid VARCHAR(64) DEFAULT NULL COMMENT '微信openid',
  unionid VARCHAR(64) DEFAULT NULL COMMENT '微信unionid',
  nickname VARCHAR(100) DEFAULT NULL,
  avatar_url VARCHAR(255) DEFAULT NULL,
  mobile VARCHAR(30) DEFAULT NULL,
  status ENUM('active', 'disabled') NOT NULL DEFAULT 'active',
  last_login_at DATETIME DEFAULT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_users_openid (openid),
  UNIQUE KEY uk_users_unionid (unionid),
  KEY idx_users_mobile (mobile),
  KEY idx_users_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户表';

CREATE TABLE user_profiles (
  id BIGINT NOT NULL AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  exam_year INT DEFAULT NULL COMMENT '目标考研年份',
  target_degree_type ENUM('academic', 'professional') DEFAULT NULL,
  target_study_mode ENUM('full_time', 'part_time') DEFAULT NULL,
  target_major_code VARCHAR(20) DEFAULT NULL,
  target_major_name VARCHAR(100) DEFAULT NULL,
  score_total INT DEFAULT NULL,
  politics_score INT DEFAULT NULL,
  english_score INT DEFAULT NULL,
  subject_one_score INT DEFAULT NULL,
  subject_two_score INT DEFAULT NULL,
  undergraduate_school VARCHAR(100) DEFAULT NULL,
  undergraduate_major VARCHAR(100) DEFAULT NULL,
  preferred_provinces JSON DEFAULT NULL COMMENT '偏好省份列表',
  preferred_cities JSON DEFAULT NULL COMMENT '偏好城市列表',
  preferred_school_levels JSON DEFAULT NULL COMMENT '偏好院校层次',
  risk_preference ENUM('conservative', 'balanced', 'aggressive') NOT NULL DEFAULT 'balanced',
  notes VARCHAR(500) DEFAULT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_user_profiles_user_id (user_id),
  KEY idx_user_profiles_exam_year (exam_year),
  KEY idx_user_profiles_major_code (target_major_code),
  CONSTRAINT fk_user_profiles_user
    FOREIGN KEY (user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户考研画像';

CREATE TABLE schools (
  id BIGINT NOT NULL AUTO_INCREMENT,
  school_code VARCHAR(50) DEFAULT NULL COMMENT '学校代码',
  school_name VARCHAR(100) NOT NULL COMMENT '学校名称',
  province VARCHAR(50) NOT NULL,
  city VARCHAR(50) NOT NULL,
  location_text VARCHAR(100) DEFAULT NULL COMMENT '原始位置描述',
  school_type VARCHAR(50) DEFAULT NULL COMMENT '综合/理工/师范等',
  school_level_text VARCHAR(255) DEFAULT NULL COMMENT '原始层次文案',
  is_985 TINYINT(1) NOT NULL DEFAULT 0,
  is_211 TINYINT(1) NOT NULL DEFAULT 0,
  is_double_first_class TINYINT(1) NOT NULL DEFAULT 0,
  is_self_marking TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否自划线',
  has_postgraduate TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否具有研究生招生资格',
  ranking INT DEFAULT NULL COMMENT '学校排名',
  hot_score DECIMAL(6,2) DEFAULT NULL COMMENT '热度分',
  intro TEXT DEFAULT NULL COMMENT '学校简介',
  website VARCHAR(255) DEFAULT NULL,
  graduate_website VARCHAR(255) DEFAULT NULL,
  logo_url VARCHAR(255) DEFAULT NULL,
  status ENUM('active', 'inactive') NOT NULL DEFAULT 'active',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_schools_name (school_name),
  UNIQUE KEY uk_schools_code (school_code),
  KEY idx_schools_province_city (province, city),
  KEY idx_schools_flags (is_985, is_211, is_double_first_class),
  KEY idx_schools_ranking (ranking),
  KEY idx_schools_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='学校主表';

CREATE TABLE school_tags (
  id BIGINT NOT NULL AUTO_INCREMENT,
  school_id BIGINT NOT NULL,
  tag_name VARCHAR(50) NOT NULL COMMENT '985/211/双一流/区位好/就业强等',
  tag_type VARCHAR(50) DEFAULT NULL COMMENT 'system/custom',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_school_tags_school_id_tag_name (school_id, tag_name),
  KEY idx_school_tags_tag_name (tag_name),
  CONSTRAINT fk_school_tags_school
    FOREIGN KEY (school_id) REFERENCES schools (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='学校标签表';

CREATE TABLE majors (
  id BIGINT NOT NULL AUTO_INCREMENT,
  major_code VARCHAR(20) NOT NULL COMMENT '专业代码',
  major_name VARCHAR(100) NOT NULL COMMENT '专业名称',
  degree_type ENUM('academic', 'professional') NOT NULL COMMENT '学硕/专硕',
  study_mode_default ENUM('full_time', 'part_time') DEFAULT 'full_time',
  discipline_code VARCHAR(20) DEFAULT NULL COMMENT '学科门类代码',
  discipline_name VARCHAR(50) DEFAULT NULL COMMENT '学科门类名称',
  major_category_code VARCHAR(20) DEFAULT NULL COMMENT '专业类别代码',
  major_category_name VARCHAR(100) DEFAULT NULL COMMENT '专业类别名称',
  category VARCHAR(50) DEFAULT NULL COMMENT '旧版一级分类',
  subcategory VARCHAR(100) DEFAULT NULL COMMENT '旧版二级分类',
  intro TEXT DEFAULT NULL COMMENT '专业简介',
  employment_direction TEXT DEFAULT NULL COMMENT '就业方向',
  exam_subject_template VARCHAR(255) DEFAULT NULL COMMENT '常见考试科目模板',
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_majors_code_degree (major_code, degree_type),
  KEY idx_majors_name (major_name),
  KEY idx_majors_discipline (discipline_code, degree_type),
  KEY idx_majors_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='专业主表';

CREATE TABLE school_majors (
  id BIGINT NOT NULL AUTO_INCREMENT,
  school_id BIGINT NOT NULL,
  major_id BIGINT NOT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_school_majors_school_major (school_id, major_id),
  KEY idx_school_majors_major_school (major_id, school_id),
  CONSTRAINT fk_school_majors_school
    FOREIGN KEY (school_id) REFERENCES schools (id),
  CONSTRAINT fk_school_majors_major
    FOREIGN KEY (major_id) REFERENCES majors (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='学校与专业静态关系';

CREATE TABLE enrollment_records (
  id BIGINT NOT NULL AUTO_INCREMENT,
  school_id BIGINT NOT NULL,
  major_id BIGINT NOT NULL,
  exam_year INT NOT NULL COMMENT '考研年份',
  degree_type ENUM('academic', 'professional') NOT NULL,
  study_mode ENUM('full_time', 'part_time') NOT NULL DEFAULT 'full_time',
  department_name VARCHAR(100) DEFAULT NULL COMMENT '招生院系',
  research_direction VARCHAR(255) DEFAULT NULL COMMENT '研究方向',
  exam_subjects JSON DEFAULT NULL COMMENT '考试科目代码及名称',
  reference_books JSON DEFAULT NULL COMMENT '参考书目',
  planned_enrollment INT DEFAULT NULL COMMENT '计划招生人数',
  actual_enrollment INT DEFAULT NULL COMMENT '实际录取人数',
  recommended_exemption_count INT DEFAULT NULL COMMENT '推免人数',
  application_count INT DEFAULT NULL COMMENT '报名人数',
  application_admission_ratio DECIMAL(8,2) DEFAULT NULL COMMENT '报录比',
  retest_ratio DECIMAL(8,2) DEFAULT NULL COMMENT '复试比',
  tuition_fee DECIMAL(10,2) DEFAULT NULL COMMENT '学费',
  academic_system VARCHAR(50) DEFAULT NULL COMMENT '学制',
  remarks VARCHAR(500) DEFAULT NULL,
  data_source VARCHAR(255) DEFAULT NULL COMMENT '数据来源链接或说明',
  source_updated_at DATETIME DEFAULT NULL COMMENT '源数据更新时间',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_enrollment_records_unique (school_id, major_id, exam_year, degree_type, study_mode),
  KEY idx_enrollment_records_major_year (major_id, exam_year),
  KEY idx_enrollment_records_school_year (school_id, exam_year),
  KEY idx_enrollment_records_exam_year (exam_year),
  CONSTRAINT fk_enrollment_records_school
    FOREIGN KEY (school_id) REFERENCES schools (id),
  CONSTRAINT fk_enrollment_records_major
    FOREIGN KEY (major_id) REFERENCES majors (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='招生记录核心表';

CREATE TABLE score_lines (
  id BIGINT NOT NULL AUTO_INCREMENT,
  enrollment_record_id BIGINT NOT NULL,
  score_line_type ENUM('national', 'school_retest', 'school_admission') NOT NULL COMMENT '国家线/院校复试线/录取结果',
  total_score INT DEFAULT NULL COMMENT '总分线',
  politics_score INT DEFAULT NULL,
  english_score INT DEFAULT NULL,
  subject_one_score INT DEFAULT NULL,
  subject_two_score INT DEFAULT NULL,
  admit_low_score INT DEFAULT NULL COMMENT '录取最低分',
  admit_avg_score INT DEFAULT NULL COMMENT '录取平均分',
  admit_high_score INT DEFAULT NULL COMMENT '录取最高分',
  line_note VARCHAR(500) DEFAULT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_score_lines_unique (enrollment_record_id, score_line_type),
  KEY idx_score_lines_type_total (score_line_type, total_score),
  CONSTRAINT fk_score_lines_enrollment_record
    FOREIGN KEY (enrollment_record_id) REFERENCES enrollment_records (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='分数线与录取分表';

CREATE TABLE user_favorites (
  id BIGINT NOT NULL AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  favorite_type ENUM('school', 'major', 'enrollment_record', 'plan') NOT NULL,
  target_id BIGINT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_user_favorites_unique (user_id, favorite_type, target_id),
  KEY idx_user_favorites_user_type (user_id, favorite_type),
  CONSTRAINT fk_user_favorites_user
    FOREIGN KEY (user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户收藏';

CREATE TABLE user_browsing_history (
  id BIGINT NOT NULL AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  target_type ENUM('school', 'major', 'enrollment_record', 'ai_session') NOT NULL,
  target_id BIGINT NOT NULL,
  source_page VARCHAR(100) DEFAULT NULL COMMENT '来源页面',
  duration_seconds INT DEFAULT NULL COMMENT '停留时长',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_user_browsing_history_user_created (user_id, created_at),
  KEY idx_user_browsing_history_target (target_type, target_id),
  CONSTRAINT fk_user_browsing_history_user
    FOREIGN KEY (user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='浏览历史';

CREATE TABLE ai_sessions (
  id BIGINT NOT NULL AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  session_title VARCHAR(200) DEFAULT NULL,
  scene_type ENUM('qa', 'school_selection', 'school_compare', 'score_analysis', 'retest_consulting') NOT NULL DEFAULT 'school_selection',
  input_snapshot JSON DEFAULT NULL COMMENT '发起会话时的用户画像快照',
  summary TEXT DEFAULT NULL COMMENT '会话摘要',
  status ENUM('active', 'archived') NOT NULL DEFAULT 'active',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_ai_sessions_user_created (user_id, created_at),
  KEY idx_ai_sessions_scene_type (scene_type),
  CONSTRAINT fk_ai_sessions_user
    FOREIGN KEY (user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='AI会话表';

CREATE TABLE ai_messages (
  id BIGINT NOT NULL AUTO_INCREMENT,
  session_id BIGINT NOT NULL,
  role ENUM('user', 'assistant', 'system') NOT NULL,
  message_type ENUM('text', 'plan', 'recommendation', 'follow_up') NOT NULL DEFAULT 'text',
  content LONGTEXT NOT NULL,
  structured_payload JSON DEFAULT NULL COMMENT '结构化推荐结果',
  token_count INT DEFAULT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_ai_messages_session_created (session_id, created_at),
  CONSTRAINT fk_ai_messages_session
    FOREIGN KEY (session_id) REFERENCES ai_sessions (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='AI消息记录';

CREATE TABLE recommendation_plans (
  id BIGINT NOT NULL AUTO_INCREMENT,
  session_id BIGINT NOT NULL,
  user_id BIGINT NOT NULL,
  plan_name VARCHAR(200) DEFAULT NULL,
  score_total INT DEFAULT NULL,
  target_major_code VARCHAR(20) DEFAULT NULL,
  target_major_name VARCHAR(100) DEFAULT NULL,
  risk_preference ENUM('conservative', 'balanced', 'aggressive') NOT NULL DEFAULT 'balanced',
  preferred_provinces JSON DEFAULT NULL,
  summary TEXT DEFAULT NULL COMMENT 'AI给出的总结',
  model_name VARCHAR(100) DEFAULT NULL COMMENT '生成计划时使用的模型',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_recommendation_plans_user_created (user_id, created_at),
  KEY idx_recommendation_plans_session (session_id),
  CONSTRAINT fk_recommendation_plans_session
    FOREIGN KEY (session_id) REFERENCES ai_sessions (id),
  CONSTRAINT fk_recommendation_plans_user
    FOREIGN KEY (user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='AI择校方案';

CREATE TABLE recommendation_plan_items (
  id BIGINT NOT NULL AUTO_INCREMENT,
  plan_id BIGINT NOT NULL,
  enrollment_record_id BIGINT NOT NULL,
  bucket ENUM('rush', 'match', 'safe') NOT NULL COMMENT '冲/稳/保',
  ai_score DECIMAL(8,2) DEFAULT NULL COMMENT '模型评分',
  score_gap INT DEFAULT NULL COMMENT '与线差值',
  recommendation_reason VARCHAR(1000) DEFAULT NULL,
  sort_order INT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_recommendation_plan_items_unique (plan_id, enrollment_record_id, bucket),
  KEY idx_recommendation_plan_items_plan_bucket (plan_id, bucket, sort_order),
  CONSTRAINT fk_recommendation_plan_items_plan
    FOREIGN KEY (plan_id) REFERENCES recommendation_plans (id),
  CONSTRAINT fk_recommendation_plan_items_enrollment
    FOREIGN KEY (enrollment_record_id) REFERENCES enrollment_records (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='AI择校方案明细';

CREATE OR REPLACE VIEW vw_enrollment_overview AS
SELECT
  er.id AS enrollment_record_id,
  er.exam_year,
  er.degree_type,
  er.study_mode,
  er.department_name,
  er.research_direction,
  er.planned_enrollment,
  er.actual_enrollment,
  er.recommended_exemption_count,
  er.application_count,
  er.application_admission_ratio,
  er.retest_ratio,
  er.tuition_fee,
  er.academic_system,
  er.remarks,
  s.id AS school_id,
  s.school_name,
  s.school_code,
  s.province,
  s.city,
  s.is_985,
  s.is_211,
  s.is_double_first_class,
  s.ranking,
  m.id AS major_id,
  m.major_code,
  m.major_name,
  m.degree_type AS major_degree_type,
  m.discipline_code,
  m.discipline_name,
  national.total_score AS national_total_score,
  school_retest.total_score AS school_retest_total_score,
  school_retest.politics_score AS school_retest_politics_score,
  school_retest.english_score AS school_retest_english_score,
  school_retest.subject_one_score AS school_retest_subject_one_score,
  school_retest.subject_two_score AS school_retest_subject_two_score,
  school_admission.admit_low_score,
  school_admission.admit_avg_score,
  school_admission.admit_high_score
FROM enrollment_records er
JOIN schools s ON er.school_id = s.id
JOIN majors m ON er.major_id = m.id
LEFT JOIN score_lines national
  ON national.enrollment_record_id = er.id
 AND national.score_line_type = 'national'
LEFT JOIN score_lines school_retest
  ON school_retest.enrollment_record_id = er.id
 AND school_retest.score_line_type = 'school_retest'
LEFT JOIN score_lines school_admission
  ON school_admission.enrollment_record_id = er.id
 AND school_admission.score_line_type = 'school_admission';
