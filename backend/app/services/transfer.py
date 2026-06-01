"""
考研调剂相关服务
"""
from app.core.db import fetch_all, fetch_one


def get_transfer_opportunities(
    score_total: int,
    program_code: str,
    degree_type: str = "",
    preferred_provinces: list[str] | None = None,
    exclude_school_ids: list[str] | None = None,
) -> dict:
    """
    查询调剂机会
    调剂逻辑：
    1. 用户分数 >= 国家线
    2. 目标专业还有招生名额（actual_enrollment < planned_enrollment 或有剩余）
    3. 按分数匹配（用户分数 >= 复试线）
    """
    # 获取专业信息
    program = fetch_one(
        "SELECT id, major_code, major_name, degree_type FROM majors WHERE major_code = %s AND is_active = 1",
        (program_code,)
    )
    if not program:
        return {"summary": "未找到该专业", "opportunities": []}

    conditions = ["major_id = %s", "school_retest_total_score IS NOT NULL", "school_retest_total_score <= %s"]
    params: list = [program["id"], score_total]

    if degree_type:
        conditions.append("degree_type = %s")
        params.append(degree_type)

    if preferred_provinces:
        placeholders = ", ".join(["%s"] * len(preferred_provinces))
        conditions.append(f"province IN ({placeholders})")
        params.extend(preferred_provinces)

    if exclude_school_ids:
        placeholders = ", ".join(["%s"] * len(exclude_school_ids))
        conditions.append(f"school_id NOT IN ({placeholders})")
        params.extend(exclude_school_ids)

    # 查询符合条件的招生项目
    query = f"""
        SELECT
          enrollment_record_id AS id,
          school_id,
          school_name,
          province,
          city,
          major_name,
          major_code,
          degree_type,
          study_mode,
          planned_enrollment,
          actual_enrollment,
          school_retest_total_score AS reexam_score,
          admit_low_score,
          admit_avg_score,
          application_admission_ratio
        FROM vw_enrollment_overview
        WHERE {' AND '.join(conditions)}
        ORDER BY
          school_retest_total_score DESC,  -- 优先看分数要求高的（更有价值）
          COALESCE(application_admission_ratio, 0) ASC  -- 报录比低的更容易调剂
    """
    opportunities = fetch_all(query, tuple(params))

    # 为每个机会计算调剂友好度
    for item in opportunities:
        gap = score_total - (item.get("reexam_score") or 0)
        item["score_gap"] = gap
        item["transfer_difficulty"] = _calculate_transfer_difficulty(item, gap)

    # 统计
    summary = f"基于你的总分 {score_total} 分，在 {program['major_name']} 专业共找到 {len(opportunities)} 个可能的调剂机会。"

    return {
        "summary": summary,
        "program": program,
        "opportunities": opportunities,
    }


def _calculate_transfer_difficulty(offering: dict, gap: int) -> str:
    """计算调剂难度"""
    reexam_score = offering.get("reexam_score") or 0
    ratio = offering.get("application_admission_ratio") or 0
    planned = offering.get("planned_enrollment") or 0
    actual = offering.get("actual_enrollment") or 0

    # 分数优势
    score_factor = "high" if gap >= 20 else ("medium" if gap >= 10 else "low")

    # 报录比因素
    ratio_factor = "low" if ratio < 3 else ("medium" if ratio < 6 else "high")

    # 招生人数因素
    enrollment_factor = "low" if planned >= 30 else ("medium" if planned >= 15 else "high")

    # 综合判断
    if score_factor == "high" and ratio_factor == "low":
        return "easy"
    elif score_factor == "low" and ratio_factor == "high":
        return "hard"
    else:
        return "medium"


def get_transfer_guide(program_code: str = "") -> dict:
    """
    获取调剂指南
    包括：调剂流程、注意事项、常见问题的解答
    """
    return {
        "process": [
            "1. 确认自己是否达到国家线",
            "2. 在研招网调剂系统开放后填报调剂志愿",
            "3. 等待学校复试通知",
            "4. 参加复试",
            "5. 等待录取结果",
        ],
        "tips": [
            "调剂志愿可同时填报3个平行志愿",
            "48小时后可修改志愿",
            "建议优先选择本科母校或家乡附近的学校",
            "注意查看学校的调剂要求（是否接受跨专业调剂）",
            "提前联系目标院校的招生办",
        ],
        "notes": [
            "A区考生可调剂到B区，但B区考生不能调剂到A区",
            "学硕可以调剂到专硕，但专硕一般不能调剂到学硕",
            "同一学科门类内可以调剂",
        ],
    }
