import re

from app.core.db import fetch_all, fetch_one


def _score_item(offering: dict, score_total: int, preferred_provinces: list[str]) -> dict:
    reexam_score = offering.get("school_retest_total_score") or offering.get("reexam_score") or 0
    gap = score_total - reexam_score
    province_bonus = 0
    if preferred_provinces and offering.get("province") in preferred_provinces:
        province_bonus = 10
    enrollment = offering.get("planned_enrollment") or offering.get("enrollment") or 0
    stability_bonus = 4 if enrollment >= 35 else 1
    total_score = gap * 2 + stability_bonus + province_bonus
    return {"gap": gap, "total_score": total_score}


def _risk_bucket(gap: int) -> str:
    if gap >= 20:
        return "safe"
    if gap >= 8:
        return "match"
    return "rush"


def generate_plan(payload: dict) -> dict:
    program = fetch_one(
        """
        SELECT id, major_code AS code, major_name AS name, degree_type
        FROM majors
        WHERE major_code = %s
          AND is_active = 1
          AND (%s IS NULL OR degree_type = %s)
        ORDER BY degree_type ASC
        LIMIT 1
        """,
        (payload["program_code"], payload.get("degree_type"), payload.get("degree_type")),
    )
    if not program:
        return {
            "summary": "没有找到对应专业代码，请先确认目标专业代码。",
            "rush": [],
            "match": [],
            "safe": [],
        }

    conditions = ["major_id = %s"]
    params: list = [program["id"]]
    if payload.get("degree_type"):
        conditions.append("degree_type = %s")
        params.append(payload["degree_type"])
    preferred_provinces = payload.get("preferred_provinces", [])
    if preferred_provinces:
        placeholders = ", ".join(["%s"] * len(preferred_provinces))
        conditions.append(f"province IN ({placeholders})")
        params.extend(preferred_provinces)
    school_levels = payload.get("school_levels", [])
    for school_level in school_levels:
        if school_level == "985":
            conditions.append("is_985 = 1")
        elif school_level == "211":
            conditions.append("is_211 = 1")
        elif school_level == "双一流":
            conditions.append("is_double_first_class = 1")

    candidates = fetch_all(
        f"""
        SELECT
          enrollment_record_id AS id,
          school_id AS institution_id,
          school_name,
          province,
          city,
          major_name AS program_name,
          major_code AS program_code,
          degree_type,
          study_mode AS learning_mode,
          planned_enrollment AS enrollment,
          planned_enrollment,
          application_admission_ratio,
          retest_ratio,
          school_retest_total_score AS reexam_score,
          school_retest_total_score,
          admit_low_score,
          admit_avg_score,
          admit_high_score
        FROM vw_enrollment_overview
        WHERE {' AND '.join(conditions)}
          AND school_retest_total_score IS NOT NULL
        ORDER BY school_retest_total_score ASC, COALESCE(application_admission_ratio, 0) DESC
        """,
        tuple(params),
    )

    enriched = []
    for item in candidates:
        scored = _score_item(item, payload["score_total"], preferred_provinces)
        risk = _risk_bucket(scored["gap"])
        enriched.append(
            {
                **item,
                "risk_bucket": risk,
                "score_gap": scored["gap"],
                "reason": _build_reason(item, scored["gap"]),
                "match_score": scored["total_score"],
            }
        )

    enriched.sort(key=lambda item: item["match_score"], reverse=True)
    return {
        "summary": _build_summary(payload["score_total"], program["name"], len(enriched)),
        "rush": [item for item in enriched if item["risk_bucket"] == "rush"][:3],
        "match": [item for item in enriched if item["risk_bucket"] == "match"][:3],
        "safe": [item for item in enriched if item["risk_bucket"] == "safe"][:3],
    }


def interpret_question(
    question: str,
    score_total: int | None,
    program_code: str | None,
    preferred_provinces: list[str] | None = None,
) -> dict:
    detected_score = score_total or _extract_score(question)
    detected_program_code = program_code or _extract_program_code(question)

    if not detected_score or not detected_program_code:
        return {
            "summary": "我先能帮你做择校判断，但还需要总分和专业代码。",
            "parsed_profile": {
                "score_total": detected_score,
                "program_code": detected_program_code,
            },
            "plan": None,
            "follow_up": "请补充例如“340分，085404，江苏浙江优先”。",
        }

    plan = generate_plan(
        {
            "score_total": detected_score,
            "program_code": detected_program_code,
            "preferred_provinces": preferred_provinces or [],
            "school_levels": [],
            "risk_preference": "balanced",
        }
    )
    return {
        "summary": plan["summary"],
        "parsed_profile": {
            "score_total": detected_score,
            "program_code": detected_program_code,
        },
        "plan": plan,
        "follow_up": "你还可以继续补充地区偏好、本科背景、是否接受高风险冲刺。",
    }


def _extract_score(question: str) -> int | None:
    match = re.search(r"(\d{3})\s*分", question) or re.search(r"\b(\d{3})\b", question)
    return int(match.group(1)) if match else None


def _extract_program_code(question: str) -> str | None:
    # 先尝试从问题中匹配 6 位数字专业代码
    match = re.search(r'\b(\d{6})\b', question)
    if match:
        code = match.group(1)
        # 验证代码是否存在于数据库中
        program = fetch_one(
            "SELECT id FROM majors WHERE major_code = %s AND is_active = 1",
            (code,)
        )
        if program:
            return code

    # 尝试从专业名称匹配
    program_keywords = {
        "计算机技术": "085404",
        "计算机科学与技术": "081200",
        "新闻与传播": "055200",
        "软件工程": "083500",
        "电子信息": "085400",
        "机械工程": "080200",
        "电气工程": "080800",
        "土木工程": "081400",
        "金融学": "020200",
        "工商管理": "120200",
        "法学": "030100",
        "教育学": "040100",
        "心理学": "040200",
        "中国语言文学": "050100",
        "外国语言文学": "050200",
        "数学": "070100",
        "物理学": "070200",
        "化学": "070300",
        "生物学": "071000",
        "临床医学": "100200",
    }
    for name, code in program_keywords.items():
        if name in question:
            return code
    return None


def _build_reason(offering: dict, gap: int) -> str:
    enrollment = offering.get("planned_enrollment") or offering.get("enrollment") or "未知"
    if gap >= 20:
        return f"你的分数高于复试线 {gap} 分，计划招生 {enrollment} 人，适合作为保底或稳妥选择。"
    if gap >= 8:
        return f"你的分数高于复试线 {gap} 分，进入复试相对有空间，适合作为稳妥选择。"
    return f"你的分数与复试线接近，仅高出 {max(gap, 0)} 分，适合作为冲刺备选。"


def _build_summary(score_total: int, program_name: str, candidate_count: int) -> str:
    return (
        f"基于当前数据库数据，你的总分 {score_total} 分在 {program_name} 方向共有 "
        f"{candidate_count} 个可分析项目，建议优先看稳妥项目，再搭配 1 到 2 个冲刺校。"
    )
