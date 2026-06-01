-- kaoyan_system data cleanup
-- Run this after schema upgrade.
-- Review each update before applying in production.

USE kaoyan_system;

UPDATE school_list
SET school_name = TRIM(school_name)
WHERE school_name IS NOT NULL;

UPDATE school_list
SET school_level = TRIM(school_level)
WHERE school_level IS NOT NULL;

UPDATE school_list
SET location = TRIM(location)
WHERE location IS NOT NULL;

UPDATE school_list
SET has_postgraduate = 1
WHERE CAST(has_postgraduate AS CHAR) IN ('1', '是', 'yes', 'YES', 'true', 'TRUE', '有');

UPDATE school_list
SET has_postgraduate = 0
WHERE CAST(has_postgraduate AS CHAR) IN ('0', '否', 'no', 'NO', 'false', 'FALSE', '无');

UPDATE school_list
SET is_985 = IF(school_level LIKE '%985%', 1, 0),
    is_211 = IF(school_level LIKE '%211%', 1, 0),
    is_double_first_class = IF(school_level LIKE '%双一流%', 1, 0);

UPDATE school_list
SET province = SUBSTRING_INDEX(location, ' ', 1),
    city = CASE
      WHEN INSTR(location, ' ') > 0 THEN SUBSTRING_INDEX(location, ' ', -1)
      ELSE location
    END
WHERE location IS NOT NULL
  AND TRIM(location) <> ''
  AND (province IS NULL OR city IS NULL);

UPDATE majors
SET major_code = TRIM(major_code),
    major_name = TRIM(major_name),
    category = TRIM(category),
    subcategory = TRIM(subcategory)
WHERE 1 = 1;

UPDATE majors
SET degree_type = 'academic'
WHERE degree_type IN ('学硕', 'academic', 'Academic', 'ACADEMIC');

UPDATE majors
SET degree_type = 'professional'
WHERE degree_type IN ('专硕', 'professional', 'Professional', 'PROFESSIONAL');

UPDATE majors
SET discipline_code = LEFT(major_code, 2)
WHERE discipline_code IS NULL
  AND major_code IS NOT NULL
  AND LENGTH(major_code) >= 2;

UPDATE majors
SET discipline_name = CASE discipline_code
  WHEN '02' THEN '经济学'
  WHEN '03' THEN '法学'
  WHEN '04' THEN '教育学'
  WHEN '05' THEN '文学'
  WHEN '06' THEN '历史学'
  WHEN '07' THEN '理学'
  WHEN '08' THEN '工学'
  WHEN '09' THEN '农学'
  WHEN '10' THEN '医学'
  WHEN '12' THEN '管理学'
  WHEN '13' THEN '艺术学'
  ELSE discipline_name
END
WHERE discipline_code IS NOT NULL
  AND (discipline_name IS NULL OR TRIM(discipline_name) = '');

UPDATE school_majors
SET is_active = 1
WHERE is_active IS NULL;

UPDATE exam_scores
SET study_mode = 'full_time'
WHERE study_mode IS NULL OR TRIM(study_mode) = '';

UPDATE exam_scores
SET admission_count = NULL
WHERE admission_count IS NOT NULL AND admission_count < 0;

UPDATE exam_scores
SET planned_enrollment = NULL
WHERE planned_enrollment IS NOT NULL AND planned_enrollment < 0;

UPDATE exam_scores
SET recommended_exemption_count = NULL
WHERE recommended_exemption_count IS NOT NULL AND recommended_exemption_count < 0;

UPDATE exam_scores
SET application_admission_ratio = NULL
WHERE application_admission_ratio IS NOT NULL AND application_admission_ratio < 0;

UPDATE exam_scores
SET retest_ratio = NULL
WHERE retest_ratio IS NOT NULL AND retest_ratio < 0;

UPDATE exam_scores
SET admit_score = NULL
WHERE admit_score IS NOT NULL AND (admit_score < 0 OR admit_score > 500);

UPDATE exam_scores
SET admit_avg_score = NULL
WHERE admit_avg_score IS NOT NULL AND (admit_avg_score < 0 OR admit_avg_score > 500);

UPDATE exam_scores
SET admit_high_score = NULL
WHERE admit_high_score IS NOT NULL AND (admit_high_score < 0 OR admit_high_score > 500);

UPDATE exam_scores
SET reexam_total_score = NULL
WHERE reexam_total_score IS NOT NULL AND (reexam_total_score < 0 OR reexam_total_score > 500);

UPDATE exam_scores
SET politics_score = NULL
WHERE politics_score IS NOT NULL AND (politics_score < 0 OR politics_score > 100);

UPDATE exam_scores
SET english_score = NULL
WHERE english_score IS NOT NULL AND (english_score < 0 OR english_score > 100);

UPDATE exam_scores
SET subject_one_score = NULL
WHERE subject_one_score IS NOT NULL AND (subject_one_score < 0 OR subject_one_score > 150);

UPDATE exam_scores
SET subject_two_score = NULL
WHERE subject_two_score IS NOT NULL AND (subject_two_score < 0 OR subject_two_score > 150);

UPDATE exam_scores
SET year = NULL
WHERE year IS NOT NULL AND (year < 2000 OR year > 2100);

UPDATE exam_scores
SET admit_high_score = admit_avg_score
WHERE admit_high_score IS NULL
  AND admit_avg_score IS NOT NULL;

UPDATE exam_scores
SET admit_avg_score = admit_score
WHERE admit_avg_score IS NULL
  AND admit_score IS NOT NULL;

UPDATE exam_scores
SET remarks = CONCAT_WS('；', remarks, '录取分数字段待人工复核')
WHERE admit_score IS NOT NULL
  AND admit_avg_score IS NOT NULL
  AND admit_score > admit_avg_score;

UPDATE exam_scores
SET remarks = CONCAT_WS('；', remarks, '录取最高分字段待人工复核')
WHERE admit_avg_score IS NOT NULL
  AND admit_high_score IS NOT NULL
  AND admit_avg_score > admit_high_score;
