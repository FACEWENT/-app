-- kaoyan_system schema upgrade
-- Apply this script in DBeaver/MySQL after backing up your database.
-- It upgrades the current schema toward a production-ready graduate-school selection system.

USE kaoyan_system;

SET FOREIGN_KEY_CHECKS = 0;

-- 1) Upgrade school_list
ALTER TABLE school_list
  ADD COLUMN school_code VARCHAR(50) NULL COMMENT '学校代码' AFTER school_name,
  ADD COLUMN province VARCHAR(50) NULL COMMENT '省份' AFTER location,
  ADD COLUMN city VARCHAR(50) NULL COMMENT '城市' AFTER province,
  ADD COLUMN is_985 TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否985' AFTER ranking,
  ADD COLUMN is_211 TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否211' AFTER is_985,
  ADD COLUMN is_double_first_class TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否双一流' AFTER is_211,
  ADD COLUMN intro TEXT NULL COMMENT '学校简介' AFTER has_postgraduate,
  ADD COLUMN website VARCHAR(255) NULL COMMENT '学校官网' AFTER intro,
  ADD COLUMN graduate_website VARCHAR(255) NULL COMMENT '研究生院官网' AFTER website,
  ADD COLUMN update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER create_time;

ALTER TABLE school_list
  MODIFY COLUMN has_postgraduate TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否具有研究生招生资格';

UPDATE school_list
SET has_postgraduate = CASE
  WHEN has_postgraduate IN ('是', 'yes', 'YES', 'true', 'TRUE', '1') THEN 1
  ELSE 0
END;

UPDATE school_list
SET province = SUBSTRING_INDEX(location, ' ', 1),
    city = CASE
      WHEN INSTR(location, ' ') > 0 THEN SUBSTRING_INDEX(location, ' ', -1)
      ELSE location
    END
WHERE province IS NULL OR city IS NULL;

UPDATE school_list SET is_985 = IF(school_level LIKE '%985%', 1, 0);
UPDATE school_list SET is_211 = IF(school_level LIKE '%211%', 1, 0);
UPDATE school_list SET is_double_first_class = IF(school_level LIKE '%双一流%', 1, 0);

CREATE INDEX idx_school_name ON school_list (school_name);
CREATE INDEX idx_school_code ON school_list (school_code);
CREATE INDEX idx_school_province_city ON school_list (province, city);
CREATE INDEX idx_school_ranking ON school_list (ranking);

-- 2) Upgrade majors
ALTER TABLE majors
  ADD COLUMN discipline_code VARCHAR(20) NULL COMMENT '学科门类代码' AFTER major_name,
  ADD COLUMN discipline_name VARCHAR(50) NULL COMMENT '学科门类名称' AFTER discipline_code,
  ADD COLUMN major_category_code VARCHAR(20) NULL COMMENT '专业类别代码' AFTER discipline_name,
  ADD COLUMN major_category_name VARCHAR(100) NULL COMMENT '专业类别名称' AFTER major_category_code;

ALTER TABLE majors
  MODIFY COLUMN degree_type VARCHAR(20) NOT NULL COMMENT 'academic/professional';

CREATE INDEX idx_major_code ON majors (major_code);
CREATE INDEX idx_major_name ON majors (major_name);
CREATE INDEX idx_major_degree_type ON majors (degree_type);
CREATE INDEX idx_major_discipline ON majors (discipline_code, degree_type);

UPDATE majors
SET degree_type = CASE
  WHEN degree_type IN ('学硕', 'academic') THEN 'academic'
  WHEN degree_type IN ('专硕', 'professional') THEN 'professional'
  ELSE degree_type
END;

-- 3) Upgrade school_majors
ALTER TABLE school_majors
  ADD COLUMN is_active TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否有效' AFTER major_id,
  ADD COLUMN create_time DATETIME DEFAULT CURRENT_TIMESTAMP AFTER is_active,
  ADD COLUMN update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER create_time;

CREATE INDEX idx_major_school ON school_majors (major_id, school_id);

-- 4) Upgrade exam_scores
ALTER TABLE exam_scores
  CHANGE COLUMN total_score reexam_total_score INT NOT NULL COMMENT '复试总分线',
  CHANGE COLUMN major_score subject_one_score INT DEFAULT NULL COMMENT '业务课一分数线',
  ADD COLUMN subject_two_score INT DEFAULT NULL COMMENT '业务课二分数线' AFTER subject_one_score,
  ADD COLUMN planned_enrollment INT DEFAULT NULL COMMENT '计划招生人数' AFTER retest_score,
  ADD COLUMN recommended_exemption_count INT DEFAULT NULL COMMENT '推免人数' AFTER planned_enrollment,
  ADD COLUMN admit_high_score INT DEFAULT NULL COMMENT '录取最高分' AFTER admit_avg_score,
  ADD COLUMN study_mode VARCHAR(20) NOT NULL DEFAULT 'full_time' COMMENT 'full_time/part_time' AFTER year,
  ADD COLUMN remarks VARCHAR(255) NULL COMMENT '备注' AFTER admit_high_score,
  ADD COLUMN created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP AFTER remarks,
  ADD COLUMN updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER created_at;

ALTER TABLE exam_scores
  MODIFY COLUMN retest_score INT DEFAULT NULL COMMENT '复试成绩或复试相关备注数值';

CREATE INDEX idx_exam_year ON exam_scores (year);
CREATE INDEX idx_exam_school_year ON exam_scores (school_id, year);
CREATE INDEX idx_exam_major_year ON exam_scores (major_id, year);
CREATE INDEX idx_exam_school_major_year_mode ON exam_scores (school_id, major_id, year, study_mode);

SET FOREIGN_KEY_CHECKS = 1;

CREATE OR REPLACE VIEW vw_school_major_scores AS
SELECT
  es.id,
  es.year,
  es.study_mode,
  es.reexam_total_score,
  es.politics_score,
  es.english_score,
  es.subject_one_score,
  es.subject_two_score,
  es.retest_score,
  es.planned_enrollment,
  es.admission_count,
  es.recommended_exemption_count,
  es.application_admission_ratio,
  es.retest_ratio,
  es.admit_score,
  es.admit_avg_score,
  es.admit_high_score,
  es.remarks,
  s.id AS school_id,
  s.school_name,
  s.school_code,
  s.province,
  s.city,
  s.is_985,
  s.is_211,
  s.is_double_first_class,
  m.id AS major_id,
  m.major_code,
  m.major_name,
  m.degree_type,
  m.discipline_code,
  m.discipline_name
FROM exam_scores es
JOIN school_list s ON es.school_id = s.id
JOIN majors m ON es.major_id = m.id;
