-- kaoyan_system precheck
-- Run this before schema upgrade and cleanup.

USE kaoyan_system;

SELECT 'school_list' AS table_name, COUNT(*) AS row_count FROM school_list
UNION ALL
SELECT 'majors', COUNT(*) FROM majors
UNION ALL
SELECT 'school_majors', COUNT(*) FROM school_majors
UNION ALL
SELECT 'exam_scores', COUNT(*) FROM exam_scores;

SELECT id, school_name
FROM school_list
WHERE school_name IS NULL OR TRIM(school_name) = '';

SELECT DISTINCT school_level
FROM school_list
ORDER BY school_level;

SELECT DISTINCT has_postgraduate
FROM school_list
ORDER BY has_postgraduate;

SELECT id, school_name, location
FROM school_list
WHERE location IS NULL OR TRIM(location) = ''
LIMIT 50;

SELECT school_name, COUNT(*) AS duplicate_count
FROM school_list
GROUP BY school_name
HAVING COUNT(*) > 1;

SELECT id, major_code, major_name, degree_type
FROM majors
WHERE major_code IS NULL OR TRIM(major_code) = '';

SELECT DISTINCT degree_type
FROM majors
ORDER BY degree_type;

SELECT major_code, degree_type, COUNT(*) AS duplicate_count
FROM majors
GROUP BY major_code, degree_type
HAVING COUNT(*) > 1;

SELECT id, major_code, major_name, category, subcategory
FROM majors
WHERE major_name IS NULL OR TRIM(major_name) = ''
LIMIT 50;

SELECT sm.*
FROM school_majors sm
LEFT JOIN school_list s ON sm.school_id = s.id
WHERE s.id IS NULL
LIMIT 50;

SELECT sm.*
FROM school_majors sm
LEFT JOIN majors m ON sm.major_id = m.id
WHERE m.id IS NULL
LIMIT 50;

SELECT id, school_id, major_id, year
FROM exam_scores
WHERE year < 2000 OR year > 2100;

SELECT school_id, major_id, year, COUNT(*) AS duplicate_count
FROM exam_scores
GROUP BY school_id, major_id, year
HAVING COUNT(*) > 1;

SELECT *
FROM exam_scores
WHERE total_score < 0 OR total_score > 500
LIMIT 50;

SELECT *
FROM exam_scores
WHERE politics_score < 0 OR politics_score > 100
   OR english_score < 0 OR english_score > 100
   OR major_score < 0 OR major_score > 300
LIMIT 50;

SELECT *
FROM exam_scores
WHERE admission_count < 0
   OR application_admission_ratio < 0
   OR retest_ratio < 0
LIMIT 50;

SELECT es.*
FROM exam_scores es
LEFT JOIN school_list s ON es.school_id = s.id
WHERE s.id IS NULL
LIMIT 50;

SELECT es.*
FROM exam_scores es
LEFT JOIN majors m ON es.major_id = m.id
WHERE m.id IS NULL
LIMIT 50;
