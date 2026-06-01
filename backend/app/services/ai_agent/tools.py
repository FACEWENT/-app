"""考研Agent工具集 - 封装数据库查询为可被LLM调用的Function"""
from typing import Any

from app.core.db import fetch_all, fetch_one
from app.services.recommendation import generate_plan
from app.services.transfer import get_transfer_opportunities


# ===================== Tool Schemas (供 LLM Function Calling 使用) =====================

TOOL_SCHEMAS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "search_schools",
            "description": "按名称/省份/层次搜索院校，返回院校基础信息列表。当用户提到学校名（可能不完整）或想了解某地某层次的院校时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "学校名称关键词，模糊匹配"},
                    "province": {"type": "string", "description": "省份名，如'江苏'、'北京'"},
                    "is_985": {"type": "boolean", "description": "是否仅查询985院校"},
                    "is_211": {"type": "boolean", "description": "是否仅查询211院校"},
                    "is_double_first_class": {"type": "boolean", "description": "是否仅查询双一流"},
                    "limit": {"type": "integer", "description": "返回数量上限，默认10", "default": 10},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_majors",
            "description": "按名称或代码搜索专业，确认专业代码。当用户给出专业名但你不确定代码时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "专业名称或专业代码关键词"},
                    "degree_type": {"type": "string", "enum": ["academic", "professional"], "description": "学硕academic/专硕professional"},
                    "limit": {"type": "integer", "default": 10},
                },
                "required": ["keyword"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_enrollment",
            "description": "查询某院校某专业的招生记录，包含招生人数、报录比、复试线、录取分数等关键数据。这是评估学校的核心工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "school_name": {"type": "string", "description": "学校名称（精确或模糊）"},
                    "major_code": {"type": "string", "description": "专业代码（6位数字）"},
                    "major_name": {"type": "string", "description": "专业名称"},
                    "exam_year": {"type": "integer", "description": "考研年份，如2025、2024、2023"},
                    "limit": {"type": "integer", "default": 20},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recommend_schools",
            "description": "【核心】根据用户的分数、目标专业、偏好，生成冲刺/稳妥/保底三档择校方案。当用户给出明确的分数和专业时优先调用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "score_total": {"type": "integer", "description": "考生总分，0-500"},
                    "program_code": {"type": "string", "description": "目标专业代码（6位数字）"},
                    "preferred_provinces": {"type": "array", "items": {"type": "string"}, "description": "偏好省份列表，如['江苏','浙江']"},
                    "school_levels": {"type": "array", "items": {"type": "string"}, "description": "院校层次偏好，可填'985'/'211'/'双一流'"},
                    "risk_preference": {"type": "string", "enum": ["conservative", "balanced", "aggressive"], "description": "风险偏好：保守/均衡/激进", "default": "balanced"},
                    "degree_type": {"type": "string", "enum": ["academic", "professional"], "description": "学硕或专硕"},
                },
                "required": ["score_total", "program_code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_transfer",
            "description": "调剂分析：过国家线但未进目标院校复试或未录取的考生，寻找可调剂的院校。",
            "parameters": {
                "type": "object",
                "properties": {
                    "score_total": {"type": "integer", "description": "考生总分"},
                    "program_code": {"type": "string", "description": "原报考或拟调剂专业代码"},
                    "degree_type": {"type": "string", "enum": ["academic", "professional"]},
                    "preferred_provinces": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["score_total", "program_code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_schools",
            "description": "对比多所院校在同一专业上的招生差异（分数线、报录比、招生人数、学费等）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "school_names": {"type": "array", "items": {"type": "string"}, "description": "要对比的学校名列表，2-5所"},
                    "major_code": {"type": "string", "description": "专业代码"},
                    "major_name": {"type": "string", "description": "专业名称（与代码二选一）"},
                    "exam_year": {"type": "integer", "default": 2025},
                },
                "required": ["school_names"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_score_lines",
            "description": "查询某专业在指定年份的国家线、院校复试线、录取分数详情。",
            "parameters": {
                "type": "object",
                "properties": {
                    "school_name": {"type": "string"},
                    "major_code": {"type": "string"},
                    "exam_year": {"type": "integer", "default": 2025},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_profile",
            "description": "获取当前用户的考研画像（分数、目标专业、本科背景等）。当用户问'根据我的情况...'时调用。",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


# ===================== Tool Implementations =====================


def search_schools(keyword: str = "", province: str = "", is_985: bool | None = None,
                   is_211: bool | None = None, is_double_first_class: bool | None = None,
                   limit: int = 10) -> dict:
    conditions = ["status = 'active'"]
    params: list = []
    if keyword:
        conditions.append("school_name LIKE %s")
        params.append(f"%{keyword}%")
    if province:
        conditions.append("province = %s")
        params.append(province)
    if is_985:
        conditions.append("is_985 = 1")
    if is_211:
        conditions.append("is_211 = 1")
    if is_double_first_class:
        conditions.append("is_double_first_class = 1")

    rows = fetch_all(
        f"""SELECT id, school_code, school_name, province, city, school_type,
                   is_985, is_211, is_double_first_class, ranking
            FROM schools
            WHERE {' AND '.join(conditions)}
            ORDER BY (is_985 + is_211 + is_double_first_class) DESC, ranking IS NULL, ranking
            LIMIT %s""",
        tuple(params + [min(limit, 30)])
    )
    return {"count": len(rows), "schools": rows}


def search_majors(keyword: str, degree_type: str = "", limit: int = 10) -> dict:
    conditions = ["is_active = 1"]
    params: list = []
    if keyword.isdigit():
        conditions.append("major_code LIKE %s")
        params.append(f"{keyword}%")
    else:
        conditions.append("(major_name LIKE %s OR major_category_name LIKE %s)")
        params.append(f"%{keyword}%")
        params.append(f"%{keyword}%")
    if degree_type:
        conditions.append("degree_type = %s")
        params.append(degree_type)

    rows = fetch_all(
        f"""SELECT id, major_code, major_name, degree_type,
                   discipline_code, discipline_name, major_category_name
            FROM majors
            WHERE {' AND '.join(conditions)}
            ORDER BY major_code
            LIMIT %s""",
        tuple(params + [min(limit, 30)])
    )
    return {"count": len(rows), "majors": rows}


def query_enrollment(school_name: str = "", major_code: str = "", major_name: str = "",
                     exam_year: int | None = None, limit: int = 20) -> dict:
    conditions = []
    params: list = []
    if school_name:
        conditions.append("school_name LIKE %s")
        params.append(f"%{school_name}%")
    if major_code:
        conditions.append("major_code = %s")
        params.append(major_code)
    if major_name:
        conditions.append("major_name LIKE %s")
        params.append(f"%{major_name}%")
    if exam_year:
        conditions.append("exam_year = %s")
        params.append(exam_year)

    if not conditions:
        return {"error": "至少需要提供一个查询条件（学校/专业/年份）"}

    rows = fetch_all(
        f"""SELECT enrollment_record_id, exam_year, school_name, province, city,
                   is_985, is_211,
                   major_code, major_name, major_degree_type AS degree_type, study_mode,
                   department_name, planned_enrollment, actual_enrollment,
                   recommended_exemption_count, application_count,
                   application_admission_ratio, retest_ratio,
                   tuition_fee, academic_system,
                   national_total_score, school_retest_total_score,
                   admit_low_score, admit_avg_score, admit_high_score
            FROM vw_enrollment_overview
            WHERE {' AND '.join(conditions)}
            ORDER BY exam_year DESC, school_retest_total_score DESC
            LIMIT %s""",
        tuple(params + [min(limit, 50)])
    )
    return {"count": len(rows), "records": rows}


def recommend_schools(score_total: int, program_code: str,
                       preferred_provinces: list[str] | None = None,
                       school_levels: list[str] | None = None,
                       risk_preference: str = "balanced",
                       degree_type: str | None = None) -> dict:
    plan = generate_plan({
        "score_total": score_total,
        "program_code": program_code,
        "preferred_provinces": preferred_provinces or [],
        "school_levels": school_levels or [],
        "risk_preference": risk_preference,
        "degree_type": degree_type,
    })
    # 精简返回字段，避免提示词膨胀
    def _trim(items):
        return [{
            "school_name": it.get("school_name"),
            "province": it.get("province"),
            "program_name": it.get("program_name"),
            "degree_type": it.get("degree_type"),
            "reexam_score": it.get("reexam_score"),
            "admit_avg_score": it.get("admit_avg_score"),
            "score_gap": it.get("score_gap"),
            "enrollment": it.get("enrollment"),
            "application_admission_ratio": it.get("application_admission_ratio"),
            "reason": it.get("reason"),
        } for it in items]
    return {
        "summary": plan.get("summary"),
        "rush": _trim(plan.get("rush", [])),
        "match": _trim(plan.get("match", [])),
        "safe": _trim(plan.get("safe", [])),
    }


def analyze_transfer(score_total: int, program_code: str, degree_type: str = "",
                      preferred_provinces: list[str] | None = None) -> dict:
    result = get_transfer_opportunities(
        score_total=score_total,
        program_code=program_code,
        degree_type=degree_type,
        preferred_provinces=preferred_provinces or [],
        exclude_school_ids=[],
    )
    opps = result.get("opportunities", [])[:15]
    trimmed = [{
        "school_name": o.get("school_name"),
        "province": o.get("province"),
        "major_name": o.get("major_name"),
        "degree_type": o.get("degree_type"),
        "reexam_score": o.get("reexam_score"),
        "score_gap": o.get("score_gap"),
        "transfer_difficulty": o.get("transfer_difficulty"),
        "planned_enrollment": o.get("planned_enrollment"),
        "actual_enrollment": o.get("actual_enrollment"),
        "application_admission_ratio": o.get("application_admission_ratio"),
    } for o in opps]
    return {
        "summary": result.get("summary"),
        "opportunities": trimmed,
        "total": len(result.get("opportunities", [])),
    }


def compare_schools(school_names: list[str], major_code: str = "",
                     major_name: str = "", exam_year: int = 2025) -> dict:
    if not school_names:
        return {"error": "请提供要对比的学校名列表"}

    results = []
    for name in school_names[:5]:
        rows = query_enrollment(
            school_name=name,
            major_code=major_code,
            major_name=major_name,
            exam_year=exam_year,
            limit=3,
        )["records"]
        if rows:
            best = rows[0]
            results.append({
                "school_name": best.get("school_name"),
                "province": best.get("province"),
                "is_985": best.get("is_985"),
                "is_211": best.get("is_211"),
                "major_name": best.get("major_name"),
                "exam_year": best.get("exam_year"),
                "planned_enrollment": best.get("planned_enrollment"),
                "actual_enrollment": best.get("actual_enrollment"),
                "recommended_exemption_count": best.get("recommended_exemption_count"),
                "application_count": best.get("application_count"),
                "application_admission_ratio": best.get("application_admission_ratio"),
                "retest_ratio": best.get("retest_ratio"),
                "school_retest_total_score": best.get("school_retest_total_score"),
                "admit_low_score": best.get("admit_low_score"),
                "admit_avg_score": best.get("admit_avg_score"),
                "tuition_fee": best.get("tuition_fee"),
                "academic_system": best.get("academic_system"),
            })
        else:
            results.append({"school_name": name, "warning": "未查到该校在此专业的招生数据"})
    return {"count": len(results), "schools": results, "exam_year": exam_year}


def get_score_lines(school_name: str = "", major_code: str = "", exam_year: int = 2025) -> dict:
    conditions = ["er.exam_year = %s"]
    params: list = [exam_year]
    if school_name:
        conditions.append("s.school_name LIKE %s")
        params.append(f"%{school_name}%")
    if major_code:
        conditions.append("m.major_code = %s")
        params.append(major_code)

    if not (school_name or major_code):
        return {"error": "至少需要school_name或major_code"}

    rows = fetch_all(
        f"""SELECT er.id, s.school_name, s.province, m.major_code, m.major_name, m.degree_type,
                   er.exam_year,
                   sl_n.total_score AS national_total,
                   sl_n.politics_score AS national_politics,
                   sl_n.english_score AS national_english,
                   sl_r.total_score AS retest_total,
                   sl_r.politics_score AS retest_politics,
                   sl_r.english_score AS retest_english,
                   sl_r.subject_one_score AS retest_subject_one,
                   sl_r.subject_two_score AS retest_subject_two,
                   sl_a.admit_low_score, sl_a.admit_avg_score, sl_a.admit_high_score
            FROM enrollment_records er
            JOIN schools s ON er.school_id = s.id
            JOIN majors m ON er.major_id = m.id
            LEFT JOIN score_lines sl_n ON sl_n.enrollment_record_id = er.id AND sl_n.score_line_type='national'
            LEFT JOIN score_lines sl_r ON sl_r.enrollment_record_id = er.id AND sl_r.score_line_type='school_retest'
            LEFT JOIN score_lines sl_a ON sl_a.enrollment_record_id = er.id AND sl_a.score_line_type='school_admission'
            WHERE {' AND '.join(conditions)}
            LIMIT 15""",
        tuple(params)
    )
    return {"count": len(rows), "score_lines": rows}


def get_user_profile(user_id: int | None) -> dict:
    if not user_id:
        return {"error": "未登录或无user_id"}
    row = fetch_one(
        """SELECT exam_year, target_degree_type, target_study_mode,
                  target_major_code, target_major_name,
                  score_total, politics_score, english_score,
                  subject_one_score, subject_two_score,
                  undergraduate_school, undergraduate_major,
                  preferred_provinces, preferred_cities,
                  preferred_school_levels, risk_preference, notes
           FROM user_profiles WHERE user_id = %s""",
        (user_id,)
    )
    if not row:
        return {"error": "用户未填写考研画像", "profile": None}
    return {"profile": row}


# ===================== Tool Dispatcher =====================


def execute_tool(name: str, arguments: dict, context: dict | None = None) -> Any:
    """根据工具名分发到具体实现"""
    context = context or {}
    try:
        if name == "search_schools":
            return search_schools(**arguments)
        if name == "search_majors":
            return search_majors(**arguments)
        if name == "query_enrollment":
            return query_enrollment(**arguments)
        if name == "recommend_schools":
            return recommend_schools(**arguments)
        if name == "analyze_transfer":
            return analyze_transfer(**arguments)
        if name == "compare_schools":
            return compare_schools(**arguments)
        if name == "get_score_lines":
            return get_score_lines(**arguments)
        if name == "get_user_profile":
            return get_user_profile(user_id=context.get("user_id"))
        return {"error": f"未知工具: {name}"}
    except TypeError as e:
        return {"error": f"工具参数错误: {e}"}
    except Exception as e:
        return {"error": f"工具执行异常: {type(e).__name__}: {e}"}
