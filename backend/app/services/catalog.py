from app.core.db import fetch_all, fetch_one


def paginate(items: list[dict], page: int, page_size: int) -> dict:
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": items[start:end],
        "page": page,
        "page_size": page_size,
        "total": len(items),
    }


def build_filters() -> dict:
    province_expr = _normalized_province_sql("s")
    provinces = fetch_all(
        f"""
        SELECT DISTINCT {province_expr} AS province
        FROM schools s
        WHERE s.status = 'active'
          AND {province_expr} IS NOT NULL
          AND {province_expr} <> ''
        ORDER BY {province_expr}
        """
    )
    school_types = fetch_all(
        """
        SELECT DISTINCT TRIM(school_type) AS school_type
        FROM schools
        WHERE status = 'active' AND school_type IS NOT NULL AND school_type <> ''
        ORDER BY TRIM(school_type)
        """
    )
    disciplines = fetch_all(
        """
        SELECT DISTINCT discipline_code AS code, discipline_name AS name
        FROM majors
        WHERE is_active = 1 AND discipline_code IS NOT NULL
        ORDER BY discipline_code
        """
    )
    school_keywords = fetch_all(
        """
        SELECT school_name AS keyword
        FROM schools
        WHERE status = 'active'
        ORDER BY COALESCE(hot_score, 0) DESC, COALESCE(ranking, 999999) ASC, school_name ASC
        LIMIT 4
        """
    )
    major_keywords = fetch_all(
        """
        SELECT major_name AS keyword
        FROM majors
        WHERE is_active = 1
        ORDER BY major_name ASC
        LIMIT 4
        """
    )
    return {
        "provinces": [item["province"] for item in provinces],
        "school_types": [item["school_type"] for item in school_types],
        "school_levels": ["985", "211", "双一流"],
        "degrees": ["academic", "professional"],
        "learning_modes": ["full_time", "part_time"],
        "disciplines": disciplines,
        "hot_keywords": [item["keyword"] for item in school_keywords + major_keywords][:8],
    }


def list_institutions(
    keyword: str = "",
    province: str = "",
    city: str = "",
    school_level: str = "",
    school_type: str = "",
    discipline_code: str = "",
    page: int = 1,
    page_size: int = 20,
) -> dict:
    province_expr = _normalized_province_sql("schools")
    city_expr = _normalized_city_sql("schools")
    conditions = ["status = 'active'"]
    params: list = []
    if keyword:
        conditions.append("(school_name LIKE %s OR school_code LIKE %s)")
        wildcard = f"%{keyword}%"
        params.extend([wildcard, wildcard])
    if province:
        conditions.append(f"{province_expr} = %s")
        params.append(province)
    if city:
        conditions.append(f"{city_expr} = %s")
        params.append(city)
    if school_level == "985":
        conditions.append("is_985 = 1")
    elif school_level == "211":
        conditions.append("is_211 = 1")
    elif school_level == "双一流":
        conditions.append("is_double_first_class = 1")
    if school_type:
        conditions.append("TRIM(school_type) = %s")
        params.append(school_type.strip())

    # 如果指定了专业，筛选开设该专业的院校
    if discipline_code:
        conditions.append("""
            EXISTS (
                SELECT 1 FROM enrollment_records er
                JOIN majors m ON m.id = er.major_id
                WHERE er.school_id = schools.id
                AND m.discipline_code = %s
                AND m.is_active = 1
            )
        """)
        params.append(discipline_code)

    # 先查总数
    count_query = f"""
        SELECT COUNT(*) as total
        FROM schools
        WHERE {' AND '.join(conditions)}
    """
    count_result = fetch_one(count_query, tuple(params))
    total = count_result["total"] if count_result else 0

    # 数据库层分页
    offset = (page - 1) * page_size
    query = f"""
        SELECT
          id,
          school_name AS name,
          {province_expr} AS province,
          {city_expr} AS city,
          school_code,
          intro,
          ranking,
          is_985,
          is_211,
          is_double_first_class,
          school_type
        FROM schools
        WHERE {' AND '.join(conditions)}
        ORDER BY COALESCE(ranking, 999999) ASC, school_name ASC
        LIMIT %s OFFSET %s
    """
    params.extend([page_size, offset])
    items = fetch_all(query, tuple(params))
    for item in items:
        item["school_levels"] = _school_levels(item)

    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
    }


def _normalized_province_sql(alias: str) -> str:
    return f"""
        CASE
          WHEN {alias}.province IS NULL OR TRIM({alias}.province) = '' THEN NULL
          WHEN TRIM({alias}.province) LIKE '%%省%%' THEN CONCAT(SUBSTRING_INDEX(TRIM({alias}.province), '省', 1), '省')
          WHEN TRIM({alias}.province) LIKE '%%自治区%%' THEN CONCAT(SUBSTRING_INDEX(TRIM({alias}.province), '自治区', 1), '自治区')
          WHEN TRIM({alias}.province) LIKE '%%特别行政区%%' THEN CONCAT(SUBSTRING_INDEX(TRIM({alias}.province), '特别行政区', 1), '特别行政区')
          WHEN TRIM({alias}.province) LIKE '北京市%%' THEN '北京市'
          WHEN TRIM({alias}.province) LIKE '上海市%%' THEN '上海市'
          WHEN TRIM({alias}.province) LIKE '天津市%%' THEN '天津市'
          WHEN TRIM({alias}.province) LIKE '重庆市%%' THEN '重庆市'
          ELSE TRIM({alias}.province)
        END
    """


def _normalized_city_sql(alias: str) -> str:
    return f"""
        CASE
          WHEN {alias}.city IS NOT NULL AND TRIM({alias}.city) <> '' THEN
            CASE
              WHEN TRIM({alias}.city) LIKE '%%省%%市%%' THEN
                CONCAT(
                  SUBSTRING_INDEX(
                    SUBSTRING_INDEX(TRIM({alias}.city), '市', 1),
                    '省',
                    -1
                  ),
                  '市'
                )
              WHEN TRIM({alias}.city) LIKE '%%自治区%%市%%' THEN
                CONCAT(
                  SUBSTRING_INDEX(
                    SUBSTRING_INDEX(TRIM({alias}.city), '市', 1),
                    '自治区',
                    -1
                  ),
                  '市'
                )
              ELSE TRIM({alias}.city)
            END
          WHEN {alias}.province IS NOT NULL AND TRIM({alias}.province) LIKE '%%省%%市%%' THEN
            CONCAT(
              SUBSTRING_INDEX(
                SUBSTRING_INDEX(TRIM({alias}.province), '市', 1),
                '省',
                -1
              ),
              '市'
            )
          WHEN {alias}.province IS NOT NULL AND TRIM({alias}.province) LIKE '%%自治区%%市%%' THEN
            CONCAT(
              SUBSTRING_INDEX(
                SUBSTRING_INDEX(TRIM({alias}.province), '市', 1),
                '自治区',
                -1
              ),
              '市'
            )
          WHEN TRIM({alias}.province) LIKE '北京市%%' THEN '北京市'
          WHEN TRIM({alias}.province) LIKE '上海市%%' THEN '上海市'
          WHEN TRIM({alias}.province) LIKE '天津市%%' THEN '天津市'
          WHEN TRIM({alias}.province) LIKE '重庆市%%' THEN '重庆市'
          ELSE NULL
        END
    """


def get_institution(institution_id: str) -> dict | None:
    institution = fetch_one(
        """
        SELECT
          id,
          school_name AS name,
          province,
          city,
          school_code,
          school_type,
          school_level_text,
          ranking,
          hot_score,
          intro,
          website,
          graduate_website,
          is_985,
          is_211,
          is_double_first_class,
          is_self_marking,
          has_postgraduate
        FROM schools
        WHERE id = %s AND status = 'active'
        """,
        (institution_id,),
    )
    if not institution:
        return None

    institution["school_levels"] = _school_levels(institution)
    offerings = fetch_all(
        """
        SELECT
          enrollment_record_id AS id,
          exam_year AS year,
          major_id AS program_id,
          major_name AS program_name,
          major_code AS program_code,
          degree_type,
          study_mode AS learning_mode,
          department_name,
          planned_enrollment AS enrollment,
          recommended_exemption_count,
          application_admission_ratio,
          retest_ratio,
          school_retest_total_score AS reexam_score,
          admit_low_score,
          admit_avg_score,
          admit_high_score,
          remarks
        FROM vw_enrollment_overview
        WHERE school_id = %s
        ORDER BY exam_year DESC, major_code ASC
        """,
        (institution_id,),
    )
    stats = fetch_one(
        """
        SELECT
          COUNT(*) AS program_count,
          ROUND(AVG(school_retest_total_score), 1) AS average_reexam_score
        FROM vw_enrollment_overview
        WHERE school_id = %s
        """,
        (institution_id,),
    ) or {"program_count": 0, "average_reexam_score": None}

    return {
        **institution,
        "offerings": offerings,
        "stats": stats,
    }


def get_institution_detail_with_history(institution_id: str) -> dict | None:
    """获取院校详细信息，包括近三年招录数据、学费、参考书目等"""
    institution = fetch_one(
        """
        SELECT
          id,
          school_name AS name,
          province,
          city,
          school_code,
          school_type,
          school_level_text,
          ranking,
          hot_score,
          intro,
          website,
          graduate_website,
          is_985,
          is_211,
          is_double_first_class,
          is_self_marking,
          has_postgraduate
        FROM schools
        WHERE id = %s AND status = 'active'
        """,
        (institution_id,),
    )
    if not institution:
        return None

    institution["school_levels"] = _school_levels(institution)

    # 获取近三年数据（按专业分组）
    programs_data = fetch_all(
        """
        SELECT
          er.id AS enrollment_record_id,
          er.exam_year AS year,
          er.major_id AS program_id,
          m.major_name AS program_name,
          m.major_code AS program_code,
          m.degree_type,
          er.study_mode AS learning_mode,
          er.department_name,
          er.planned_enrollment,
          er.actual_enrollment,
          er.recommended_exemption_count,
          er.application_count,
          er.application_admission_ratio,
          er.retest_ratio,
          er.tuition_fee,
          er.academic_system,
          er.exam_subjects,
          er.reference_books,
          sl_retest.total_score AS retest_total_score,
          sl_retest.politics_score AS retest_politics_score,
          sl_retest.english_score AS retest_english_score,
          sl_retest.subject_one_score AS retest_subject_one_score,
          sl_retest.subject_two_score AS retest_subject_two_score,
          sl_admission.total_score AS admission_total_score,
          sl_admission.admit_low_score,
          sl_admission.admit_avg_score,
          sl_admission.admit_high_score
        FROM enrollment_records er
        JOIN majors m ON m.id = er.major_id
        LEFT JOIN score_lines sl_retest 
          ON sl_retest.enrollment_record_id = er.id 
          AND sl_retest.score_line_type = 'school_retest'
        LEFT JOIN score_lines sl_admission 
          ON sl_admission.enrollment_record_id = er.id 
          AND sl_admission.score_line_type = 'school_admission'
        WHERE er.school_id = %s
        AND er.exam_year >= YEAR(CURRENT_DATE) - 3
        ORDER BY m.major_code ASC, er.exam_year DESC
        """,
        (institution_id,),
    )

    # 按专业分组
    programs_map: dict[str, dict] = {}
    for record in programs_data:
        program_id = str(record["program_id"])
        if program_id not in programs_map:
            programs_map[program_id] = {
                "program_id": program_id,
                "program_name": record["program_name"],
                "program_code": record["program_code"],
                "degree_type": record["degree_type"],
                "learning_mode": record["learning_mode"],
                "department_name": record["department_name"],
                "exam_subjects": record["exam_subjects"],
                "reference_books": record["reference_books"],
                "academic_system": record["academic_system"],
                "tuition_fee": record["tuition_fee"],
                "history": []
            }
        
        programs_map[program_id]["history"].append({
            "year": record["year"],
            "enrollment_record_id": record["enrollment_record_id"],
            "planned_enrollment": record["planned_enrollment"],
            "actual_enrollment": record["actual_enrollment"],
            "recommended_exemption_count": record["recommended_exemption_count"],
            "application_count": record["application_count"],
            "application_admission_ratio": record["application_admission_ratio"],
            "retest_ratio": record["retest_ratio"],
            "tuition_fee": record["tuition_fee"],
            "retest_total_score": record["retest_total_score"],
            "retest_politics_score": record["retest_politics_score"],
            "retest_english_score": record["retest_english_score"],
            "retest_subject_one_score": record["retest_subject_one_score"],
            "retest_subject_two_score": record["retest_subject_two_score"],
            "admission_total_score": record["admission_total_score"],
            "admit_low_score": record["admit_low_score"],
            "admit_avg_score": record["admit_avg_score"],
            "admit_high_score": record["admit_high_score"]
        })

    # 获取统计信息
    stats = fetch_one(
        """
        SELECT
          COUNT(DISTINCT er.major_id) AS program_count,
          COUNT(DISTINCT er.exam_year) AS year_count,
          ROUND(AVG(er.application_admission_ratio), 2) AS avg_admission_ratio,
          ROUND(AVG(sl.total_score), 1) AS avg_retest_score
        FROM enrollment_records er
        LEFT JOIN score_lines sl 
          ON sl.enrollment_record_id = er.id 
          AND sl.score_line_type = 'school_retest'
        WHERE er.school_id = %s
        AND er.exam_year >= YEAR(CURRENT_DATE) - 3
        """,
        (institution_id,),
    ) or {"program_count": 0, "year_count": 0, "avg_admission_ratio": None, "avg_retest_score": None}

    return {
        **institution,
        "programs": list(programs_map.values()),
        "stats": stats,
    }


def list_programs(keyword: str = "", degree_type: str = "", page: int = 1, page_size: int = 20) -> dict:
    conditions = ["is_active = 1"]
    params: list = []
    if keyword:
        conditions.append("(major_name LIKE %s OR major_code LIKE %s)")
        wildcard = f"%{keyword}%"
        params.extend([wildcard, wildcard])
    if degree_type:
        conditions.append("degree_type = %s")
        params.append(degree_type)

    # 先查总数
    count_query = f"""
        SELECT COUNT(*) as total
        FROM majors
        WHERE {' AND '.join(conditions)}
    """
    count_result = fetch_one(count_query, tuple(params))
    total = count_result["total"] if count_result else 0

    # 数据库层分页
    offset = (page - 1) * page_size
    query = f"""
        SELECT
          id,
          major_code AS code,
          major_name AS name,
          discipline_code,
          discipline_name,
          degree_type,
          study_mode_default AS learning_mode,
          category,
          subcategory
        FROM majors
        WHERE {' AND '.join(conditions)}
        ORDER BY major_code ASC, major_name ASC
        LIMIT %s OFFSET %s
    """
    params.extend([page_size, offset])
    items = fetch_all(query, tuple(params))

    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
    }


def get_program(program_id: str) -> dict | None:
    program = fetch_one(
        """
        SELECT
          id,
          major_code AS code,
          major_name AS name,
          degree_type,
          study_mode_default AS learning_mode,
          discipline_code,
          discipline_name,
          major_category_code,
          major_category_name,
          category,
          subcategory,
          intro,
          employment_direction,
          exam_subject_template
        FROM majors
        WHERE id = %s AND is_active = 1
        """,
        (program_id,),
    )
    if not program:
        return None

    offerings = fetch_all(
        """
        SELECT
          enrollment_record_id AS id,
          exam_year AS year,
          school_id AS institution_id,
          school_name,
          province,
          city,
          degree_type,
          study_mode AS learning_mode,
          planned_enrollment AS enrollment,
          application_admission_ratio,
          retest_ratio,
          school_retest_total_score AS reexam_score,
          admit_low_score,
          admit_avg_score,
          admit_high_score
        FROM vw_enrollment_overview
        WHERE major_id = %s
        ORDER BY exam_year DESC, school_name ASC
        """,
        (program_id,),
    )
    stats = fetch_one(
        """
        SELECT
          COUNT(DISTINCT school_id) AS institution_count,
          ROUND(AVG(school_retest_total_score), 1) AS average_reexam_score
        FROM vw_enrollment_overview
        WHERE major_id = %s
        """,
        (program_id,),
    ) or {"institution_count": 0, "average_reexam_score": None}

    return {
        **program,
        "offerings": offerings,
        "stats": stats,
    }


def list_offerings(
    year: int | None = None,
    institution_id: str = "",
    program_id: str = "",
    keyword: str = "",
    province: str = "",
    page: int = 1,
    page_size: int = 20,
) -> dict:
    conditions = ["1 = 1"]
    params: list = []
    if year is not None:
        conditions.append("exam_year = %s")
        params.append(year)
    if institution_id:
        conditions.append("school_id = %s")
        params.append(institution_id)
    if program_id:
        conditions.append("major_id = %s")
        params.append(program_id)
    if keyword:
        conditions.append("(school_name LIKE %s OR major_name LIKE %s OR major_code LIKE %s)")
        wildcard = f"%{keyword}%"
        params.extend([wildcard, wildcard, wildcard])
    if province:
        conditions.append("province = %s")
        params.append(province)

    # 先查总数
    count_query = f"""
        SELECT COUNT(*) as total
        FROM vw_enrollment_overview
        WHERE {' AND '.join(conditions)}
    """
    count_result = fetch_one(count_query, tuple(params))
    total = count_result["total"] if count_result else 0

    # 数据库层分页
    offset = (page - 1) * page_size
    query = f"""
        SELECT
          enrollment_record_id AS id,
          school_id AS institution_id,
          major_id AS program_id,
          exam_year AS year,
          school_name,
          province,
          city,
          major_name AS program_name,
          major_code AS program_code,
          degree_type,
          study_mode AS learning_mode,
          planned_enrollment AS enrollment,
          actual_enrollment,
          recommended_exemption_count,
          application_admission_ratio,
          retest_ratio,
          school_retest_total_score AS reexam_score,
          school_retest_politics_score AS politics_score,
          school_retest_english_score AS english_score,
          school_retest_subject_one_score AS subject_one_score,
          school_retest_subject_two_score AS subject_two_score,
          admit_low_score,
          admit_avg_score,
          admit_high_score,
          remarks
        FROM vw_enrollment_overview
        WHERE {' AND '.join(conditions)}
        ORDER BY exam_year DESC, COALESCE(admit_avg_score, 0) DESC, school_name ASC
        LIMIT %s OFFSET %s
    """
    params.extend([page_size, offset])
    items = fetch_all(query, tuple(params))

    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
    }


def get_offering(offering_id: str) -> dict | None:
    item = fetch_one(
        """
        SELECT
          v.*,
          er.exam_subjects,
          er.reference_books,
          er.data_source,
          er.source_updated_at
        FROM vw_enrollment_overview v
        JOIN enrollment_records er ON er.id = v.enrollment_record_id
        WHERE v.enrollment_record_id = %s
        """,
        (offering_id,),
    )
    if not item:
        return None
    item["single_subject_note"] = _build_single_subject_note(item)
    return item


def get_offering_score_lines(offering_id: str) -> dict | None:
    item = get_offering(offering_id)
    if not item:
        return None

    trend = fetch_all(
        """
        SELECT
          exam_year AS year,
          school_retest_total_score AS score
        FROM vw_enrollment_overview
        WHERE school_id = %s AND major_id = %s AND study_mode = %s
          AND school_retest_total_score IS NOT NULL
        ORDER BY exam_year ASC
        """,
        (item["school_id"], item["major_id"], item["study_mode"]),
    )
    return {
        "latest": {
            "year": item["exam_year"],
            "reexam_score": item["school_retest_total_score"],
            "single_subject_note": item["single_subject_note"],
        },
        "trend": trend,
    }


def get_search_suggestions(q: str) -> dict:
    wildcard = f"%{q}%"
    matched_schools = fetch_all(
        """
        SELECT id, school_name AS name, province, city
        FROM schools
        WHERE status = 'active' AND school_name LIKE %s
        ORDER BY COALESCE(hot_score, 0) DESC, school_name ASC
        LIMIT 5
        """,
        (wildcard,),
    )
    matched_programs = fetch_all(
        """
        SELECT id, major_name AS name, major_code AS code, degree_type
        FROM majors
        WHERE is_active = 1 AND (major_name LIKE %s OR major_code LIKE %s)
        ORDER BY major_code ASC
        LIMIT 5
        """,
        (wildcard, wildcard),
    )
    return {
        "schools": matched_schools,
        "programs": matched_programs,
    }


def build_compare_payload(offering_ids: list[str]) -> list[dict]:
    if not offering_ids:
        return []
    placeholders = ", ".join(["%s"] * len(offering_ids))
    targets = fetch_all(
        f"""
        SELECT
          enrollment_record_id AS id,
          major_name AS program_name,
          school_name,
          exam_year AS year,
          school_retest_total_score AS reexam_score,
          admit_low_score,
          admit_avg_score
        FROM vw_enrollment_overview
        WHERE enrollment_record_id IN ({placeholders})
        ORDER BY program_name ASC, school_name ASC
        """,
        tuple(offering_ids),
    )
    grouped: dict[str, list[dict]] = {}
    for item in targets:
        grouped.setdefault(item["program_name"], []).append(item)
    return [{"program_name": key, "items": value} for key, value in grouped.items()]


def _school_levels(item: dict) -> list[str]:
    levels: list[str] = []
    if item.get("is_985"):
        levels.append("985")
    if item.get("is_211"):
        levels.append("211")
    if item.get("is_double_first_class"):
        levels.append("双一流")
    return levels


def _build_single_subject_note(item: dict) -> str:
    parts = []
    if item.get("school_retest_politics_score") is not None:
        parts.append(f"政治 {item['school_retest_politics_score']}")
    if item.get("school_retest_english_score") is not None:
        parts.append(f"英语 {item['school_retest_english_score']}")
    if item.get("school_retest_subject_one_score") is not None:
        parts.append(f"业务课一 {item['school_retest_subject_one_score']}")
    if item.get("school_retest_subject_two_score") is not None:
        parts.append(f"业务课二 {item['school_retest_subject_two_score']}")
    return "，".join(parts)
