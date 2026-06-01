-- kaoyan_system postcheck
-- Run this after schema upgrade and cleanup.

USE kaoyan_system;

SELECT 'school_list' AS table_name, COUNT(*) AS row_count FROM school_list
UNION ALL
SELECT 'majors', COUNT(*) FROM majors
UNION ALL
SELECT 'school_majors', COUNT(*) FROM school_majors
UNION ALL
SELECT 'exam_scores', COUNT(*) FROM exam_scores;

SELECT id, school_name, province, city, is_985, is_211, is_double_first_class, has_postgraduate
FROM school_list
ORDER BY id
LIMIT 50;

SELECT COUNT(*) AS empty_province_count
FROM school_list
WHERE province IS NULL OR TRIM(province) = '';

SELECT COUNT(*) AS empty_city_count
FROM school_list
WHERE city IS NULL OR TRIM(city) = '';

SELECT DISTINCT degree_type
FROM majors
ORDER BY degree_type;

SELECT id, major_code, major_name, discipline_code, discipline_name, degree_type
FROM majors
ORDER BY id
LIMIT 50;

SELECT COUNT(*) AS inactive_school_major_count
FROM school_majors
WHERE is_active = 0;

SELECT id, school_id, major_id, year, study_mode, reexam_total_score,
       politics_score, english_score, subject_one_score, subject_two_score,
       planned_enrollment, admission_count, recommended_exemption_count,
       admit_score, admit_avg_score, admit_high_score
FROM exam_scores
ORDER BY year DESC, id DESC
LIMIT 50;

SELECT COUNT(*) AS invalid_reexam_total_score_count
FROM exam_scores
WHERE reexam_total_score IS NOT NULL
  AND (reexam_total_score < 0 OR reexam_total_score > 500);

SELECT COUNT(*) AS invalid_single_subject_score_count
FROM exam_scores
WHERE (politics_score IS NOT NULL AND (politics_score < 0 OR politics_score > 100))
   OR (english_score IS NOT NULL AND (english_score < 0 OR english_score > 100))
   OR (subject_one_score IS NOT NULL AND (subject_one_score < 0 OR subject_one_score > 150))
   OR (subject_two_score IS NOT NULL AND (subject_two_score < 0 OR subject_two_score > 150));

SELECT COUNT(*) AS invalid_score_relation_count
FROM exam_scores
WHERE (admit_score IS NOT NULL AND admit_avg_score IS NOT NULL AND admit_score > admit_avg_score)
   OR (admit_avg_score IS NOT NULL AND admit_high_score IS NOT NULL AND admit_avg_score > admit_high_score);

SELECT *
FROM vw_school_major_scores
LIMIT 20;
