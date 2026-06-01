-- Reporting logic for kaoyan_system_v2
-- Run this after kaoyan_system_v2_fresh_schema.sql

USE kaoyan_system_v2;

DROP VIEW IF EXISTS vw_report_school_competitiveness;
DROP VIEW IF EXISTS vw_report_major_heat;
DROP VIEW IF EXISTS vw_report_province_distribution;
DROP VIEW IF EXISTS vw_report_score_trends;
DROP VIEW IF EXISTS vw_report_user_activity;
DROP VIEW IF EXISTS vw_report_ai_session_effectiveness;
DROP VIEW IF EXISTS vw_report_recommendation_summary;
DROP VIEW IF EXISTS vw_report_dashboard_overview;

CREATE VIEW vw_report_dashboard_overview AS
SELECT
  (SELECT COUNT(*) FROM schools WHERE status = 'active') AS total_active_schools,
  (SELECT COUNT(*) FROM majors WHERE is_active = 1) AS total_active_majors,
  (SELECT COUNT(*) FROM enrollment_records) AS total_enrollment_records,
  (SELECT COUNT(*) FROM score_lines) AS total_score_lines,
  (SELECT COUNT(*) FROM users WHERE status = 'active') AS total_active_users,
  (SELECT COUNT(*) FROM ai_sessions) AS total_ai_sessions,
  (SELECT COUNT(*) FROM recommendation_plans) AS total_recommendation_plans,
  (
    SELECT ROUND(AVG(application_admission_ratio), 2)
    FROM enrollment_records
    WHERE application_admission_ratio IS NOT NULL
  ) AS avg_application_admission_ratio,
  (
    SELECT ROUND(AVG(retest_ratio), 2)
    FROM enrollment_records
    WHERE retest_ratio IS NOT NULL
  ) AS avg_retest_ratio,
  (
    SELECT ROUND(AVG(hot_score), 2)
    FROM schools
    WHERE hot_score IS NOT NULL
  ) AS avg_school_hot_score;

CREATE VIEW vw_report_school_competitiveness AS
SELECT
  s.id AS school_id,
  s.school_name,
  s.province,
  s.city,
  s.is_985,
  s.is_211,
  s.is_double_first_class,
  s.ranking,
  s.hot_score,
  COUNT(DISTINCT er.id) AS enrollment_record_count,
  COUNT(DISTINCT er.major_id) AS major_count,
  ROUND(AVG(er.planned_enrollment), 2) AS avg_planned_enrollment,
  ROUND(AVG(er.actual_enrollment), 2) AS avg_actual_enrollment,
  ROUND(AVG(er.application_admission_ratio), 2) AS avg_application_admission_ratio,
  ROUND(AVG(er.retest_ratio), 2) AS avg_retest_ratio,
  ROUND(AVG(sr.total_score), 2) AS avg_retest_total_score,
  ROUND(AVG(sa.admit_low_score), 2) AS avg_admit_low_score,
  ROUND(AVG(sa.admit_avg_score), 2) AS avg_admit_avg_score,
  ROUND(AVG(sa.admit_high_score), 2) AS avg_admit_high_score
FROM schools s
LEFT JOIN enrollment_records er ON er.school_id = s.id
LEFT JOIN score_lines sr
  ON sr.enrollment_record_id = er.id
 AND sr.score_line_type = 'school_retest'
LEFT JOIN score_lines sa
  ON sa.enrollment_record_id = er.id
 AND sa.score_line_type = 'school_admission'
WHERE s.status = 'active'
GROUP BY
  s.id, s.school_name, s.province, s.city,
  s.is_985, s.is_211, s.is_double_first_class, s.ranking, s.hot_score;

CREATE VIEW vw_report_major_heat AS
SELECT
  m.id AS major_id,
  m.major_code,
  m.major_name,
  m.degree_type,
  m.discipline_code,
  m.discipline_name,
  COUNT(DISTINCT er.school_id) AS school_count,
  COUNT(DISTINCT er.id) AS enrollment_record_count,
  ROUND(AVG(er.planned_enrollment), 2) AS avg_planned_enrollment,
  ROUND(AVG(er.application_count), 2) AS avg_application_count,
  ROUND(AVG(er.application_admission_ratio), 2) AS avg_application_admission_ratio,
  ROUND(AVG(er.retest_ratio), 2) AS avg_retest_ratio,
  ROUND(AVG(sr.total_score), 2) AS avg_retest_total_score,
  ROUND(AVG(sa.admit_low_score), 2) AS avg_admit_low_score,
  ROUND(AVG(sa.admit_avg_score), 2) AS avg_admit_avg_score,
  ROUND(AVG(sa.admit_high_score), 2) AS avg_admit_high_score
FROM majors m
LEFT JOIN enrollment_records er ON er.major_id = m.id
LEFT JOIN score_lines sr
  ON sr.enrollment_record_id = er.id
 AND sr.score_line_type = 'school_retest'
LEFT JOIN score_lines sa
  ON sa.enrollment_record_id = er.id
 AND sa.score_line_type = 'school_admission'
WHERE m.is_active = 1
GROUP BY
  m.id, m.major_code, m.major_name, m.degree_type, m.discipline_code, m.discipline_name;

CREATE VIEW vw_report_province_distribution AS
SELECT
  s.province,
  COUNT(DISTINCT s.id) AS school_count,
  COUNT(DISTINCT er.id) AS enrollment_record_count,
  COUNT(DISTINCT er.major_id) AS major_count,
  ROUND(AVG(s.ranking), 2) AS avg_ranking,
  ROUND(AVG(s.hot_score), 2) AS avg_hot_score,
  ROUND(AVG(er.planned_enrollment), 2) AS avg_planned_enrollment,
  ROUND(AVG(er.application_admission_ratio), 2) AS avg_application_admission_ratio,
  ROUND(AVG(sr.total_score), 2) AS avg_retest_total_score,
  ROUND(AVG(sa.admit_low_score), 2) AS avg_admit_low_score
FROM schools s
LEFT JOIN enrollment_records er ON er.school_id = s.id
LEFT JOIN score_lines sr
  ON sr.enrollment_record_id = er.id
 AND sr.score_line_type = 'school_retest'
LEFT JOIN score_lines sa
  ON sa.enrollment_record_id = er.id
 AND sa.score_line_type = 'school_admission'
WHERE s.status = 'active'
GROUP BY s.province;

CREATE VIEW vw_report_score_trends AS
SELECT
  er.exam_year,
  m.major_code,
  m.major_name,
  m.degree_type,
  s.province,
  COUNT(DISTINCT er.id) AS enrollment_record_count,
  ROUND(AVG(sr.total_score), 2) AS avg_retest_total_score,
  ROUND(AVG(sr.politics_score), 2) AS avg_retest_politics_score,
  ROUND(AVG(sr.english_score), 2) AS avg_retest_english_score,
  ROUND(AVG(sr.subject_one_score), 2) AS avg_retest_subject_one_score,
  ROUND(AVG(sr.subject_two_score), 2) AS avg_retest_subject_two_score,
  ROUND(AVG(sa.admit_low_score), 2) AS avg_admit_low_score,
  ROUND(AVG(sa.admit_avg_score), 2) AS avg_admit_avg_score,
  ROUND(AVG(sa.admit_high_score), 2) AS avg_admit_high_score
FROM enrollment_records er
JOIN majors m ON m.id = er.major_id
JOIN schools s ON s.id = er.school_id
LEFT JOIN score_lines sr
  ON sr.enrollment_record_id = er.id
 AND sr.score_line_type = 'school_retest'
LEFT JOIN score_lines sa
  ON sa.enrollment_record_id = er.id
 AND sa.score_line_type = 'school_admission'
GROUP BY er.exam_year, m.major_code, m.major_name, m.degree_type, s.province;

CREATE VIEW vw_report_user_activity AS
SELECT
  u.id AS user_id,
  u.nickname,
  u.mobile,
  u.status,
  u.created_at AS user_created_at,
  u.last_login_at,
  COUNT(DISTINCT uf.id) AS favorite_count,
  COUNT(DISTINCT ubh.id) AS browsing_count,
  COUNT(DISTINCT ais.id) AS ai_session_count,
  COUNT(DISTINCT rp.id) AS recommendation_plan_count,
  MAX(ubh.created_at) AS last_browsing_at,
  MAX(ais.created_at) AS last_ai_session_at
FROM users u
LEFT JOIN user_favorites uf ON uf.user_id = u.id
LEFT JOIN user_browsing_history ubh ON ubh.user_id = u.id
LEFT JOIN ai_sessions ais ON ais.user_id = u.id
LEFT JOIN recommendation_plans rp ON rp.user_id = u.id
GROUP BY
  u.id, u.nickname, u.mobile, u.status, u.created_at, u.last_login_at;

CREATE VIEW vw_report_ai_session_effectiveness AS
SELECT
  ais.id AS session_id,
  ais.user_id,
  ais.scene_type,
  ais.status,
  ais.created_at,
  COUNT(DISTINCT am.id) AS message_count,
  SUM(CASE WHEN am.role = 'user' THEN 1 ELSE 0 END) AS user_message_count,
  SUM(CASE WHEN am.role = 'assistant' THEN 1 ELSE 0 END) AS assistant_message_count,
  SUM(CASE WHEN am.message_type = 'recommendation' THEN 1 ELSE 0 END) AS recommendation_message_count,
  COUNT(DISTINCT rp.id) AS generated_plan_count,
  COUNT(DISTINCT rpi.id) AS generated_plan_item_count
FROM ai_sessions ais
LEFT JOIN ai_messages am ON am.session_id = ais.id
LEFT JOIN recommendation_plans rp ON rp.session_id = ais.id
LEFT JOIN recommendation_plan_items rpi ON rpi.plan_id = rp.id
GROUP BY
  ais.id, ais.user_id, ais.scene_type, ais.status, ais.created_at;

CREATE VIEW vw_report_recommendation_summary AS
SELECT
  rp.id AS plan_id,
  rp.user_id,
  rp.plan_name,
  rp.score_total,
  rp.target_major_code,
  rp.target_major_name,
  rp.risk_preference,
  rp.created_at,
  COUNT(DISTINCT rpi.id) AS total_items,
  SUM(CASE WHEN rpi.bucket = 'rush' THEN 1 ELSE 0 END) AS rush_count,
  SUM(CASE WHEN rpi.bucket = 'match' THEN 1 ELSE 0 END) AS match_count,
  SUM(CASE WHEN rpi.bucket = 'safe' THEN 1 ELSE 0 END) AS safe_count,
  ROUND(AVG(rpi.ai_score), 2) AS avg_ai_score,
  ROUND(AVG(rpi.score_gap), 2) AS avg_score_gap
FROM recommendation_plans rp
LEFT JOIN recommendation_plan_items rpi ON rpi.plan_id = rp.id
GROUP BY
  rp.id, rp.user_id, rp.plan_name, rp.score_total,
  rp.target_major_code, rp.target_major_name, rp.risk_preference, rp.created_at;
