#!/usr/bin/env python3
"""
大规模生成考研招生录取数据
基于数据库中已有的学校和专业，生成2023-2025年的招生数据
"""
import json
import random
import logging
import pymysql
from pymysql.cursors import DictCursor
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "lwt18251X",
    "database": "kaoyan_system_v2",
    "charset": "utf8mb4",
    "cursorclass": DictCursor,
    "autocommit": True,
}

# 考试科目模板
EXAM_SUBJECTS = {
    "哲学": ["思想政治理论", "英语一", "哲学基础综合", "西方哲学史"],
    "经济学": ["思想政治理论", "英语一", "数学三", "经济学综合"],
    "法学": ["思想政治理论", "英语一", "法学综合一", "法学综合二"],
    "政治学": ["思想政治理论", "英语一", "政治学原理", "中外政治制度"],
    "社会学": ["思想政治理论", "英语一", "社会学理论", "社会研究方法"],
    "教育学": ["思想政治理论", "英语一", "教育学专业基础综合"],
    "心理学": ["思想政治理论", "英语一", "心理学专业基础综合"],
    "体育学": ["思想政治理论", "英语一", "体育学专业基础综合"],
    "中国语言文学": ["思想政治理论", "英语一", "文学综合", "汉语综合"],
    "外国语言文学": ["思想政治理论", "二外", "外语专业基础", "外语专业综合"],
    "新闻传播学": ["思想政治理论", "英语一", "新闻与传播专业基础", "新闻与传播综合能力"],
    "历史学": ["思想政治理论", "英语一", "历史学基础"],
    "考古学": ["思想政治理论", "英语一", "考古学综合"],
    "中国史": ["思想政治理论", "英语一", "中国史综合"],
    "世界史": ["思想政治理论", "英语一", "世界史综合"],
    "数学": ["思想政治理论", "英语一", "数学分析", "高等代数"],
    "物理学": ["思想政治理论", "英语一", "普通物理", "量子力学"],
    "化学": ["思想政治理论", "英语一", "无机化学", "有机化学"],
    "生物学": ["思想政治理论", "英语一", "生物化学", "细胞生物学"],
    "统计学": ["思想政治理论", "英语一", "数学三", "统计学综合"],
    "力学": ["思想政治理论", "英语一", "数学一", "理论力学"],
    "机械工程": ["思想政治理论", "英语一", "数学一", "机械原理"],
    "光学工程": ["思想政治理论", "英语一", "数学一", "光学"],
    "仪器科学与技术": ["思想政治理论", "英语一", "数学一", "精密仪器设计"],
    "材料科学与工程": ["思想政治理论", "英语一", "数学二", "材料科学基础"],
    "冶金工程": ["思想政治理论", "英语一", "数学二", "冶金原理"],
    "动力工程及工程热物理": ["思想政治理论", "英语一", "数学一", "工程热力学"],
    "电气工程": ["思想政治理论", "英语一", "数学一", "电路原理"],
    "电子科学与技术": ["思想政治理论", "英语一", "数学一", "半导体物理"],
    "信息与通信工程": ["思想政治理论", "英语一", "数学一", "信号与系统"],
    "控制科学与工程": ["思想政治理论", "英语一", "数学一", "自动控制原理"],
    "计算机科学与技术": ["思想政治理论", "英语一", "数学一", "计算机学科专业基础综合"],
    "建筑学": ["思想政治理论", "英语一", "建筑学基础", "建筑设计"],
    "土木工程": ["思想政治理论", "英语一", "数学一", "结构力学"],
    "水利工程": ["思想政治理论", "英语一", "数学一", "水力学"],
    "化学工程与技术": ["思想政治理论", "英语一", "数学二", "化工原理"],
    "交通运输工程": ["思想政治理论", "英语一", "数学一", "交通运输工程学"],
    "船舶与海洋工程": ["思想政治理论", "英语一", "数学一", "船舶结构力学"],
    "航空宇航科学与技术": ["思想政治理论", "英语一", "数学一", "空气动力学"],
    "兵器科学与技术": ["思想政治理论", "英语一", "数学一", "兵器概论"],
    "核科学与技术": ["思想政治理论", "英语一", "数学一", "核反应堆物理"],
    "农业工程": ["思想政治理论", "英语一", "数学二", "农业机械学"],
    "林业工程": ["思想政治理论", "英语一", "数学二", "木材学"],
    "环境科学与工程": ["思想政治理论", "英语一", "数学二", "环境工程原理"],
    "生物医学工程": ["思想政治理论", "英语一", "数学一", "生物医学工程基础"],
    "食品科学与工程": ["思想政治理论", "英语一", "数学二", "食品化学"],
    "软件工程": ["思想政治理论", "英语一", "数学一", "软件工程专业基础综合"],
    "作物学": ["思想政治理论", "英语一", "化学（农）", "植物生理学与生物化学"],
    "园艺学": ["思想政治理论", "英语一", "化学（农）", "植物生理学与生物化学"],
    "农业资源与环境": ["思想政治理论", "英语一", "化学（农）", "植物生理学与生物化学"],
    "植物保护": ["思想政治理论", "英语一", "化学（农）", "植物生理学与生物化学"],
    "畜牧学": ["思想政治理论", "英语一", "化学（农）", "动物生理学与生物化学"],
    "兽医学": ["思想政治理论", "英语一", "化学（农）", "动物生理学与生物化学"],
    "林学": ["思想政治理论", "英语一", "数学（农）", "森林生态学"],
    "水产": ["思想政治理论", "英语一", "化学（农）", "普通动物学"],
    "基础医学": ["思想政治理论", "英语一", "西医综合"],
    "临床医学": ["思想政治理论", "英语一", "西医综合"],
    "口腔医学": ["思想政治理论", "英语一", "口腔综合"],
    "公共卫生与预防医学": ["思想政治理论", "英语一", "卫生综合"],
    "中医学": ["思想政治理论", "英语一", "中医综合"],
    "中西医结合": ["思想政治理论", "英语一", "中医综合"],
    "药学": ["思想政治理论", "英语一", "药学综合"],
    "中药学": ["思想政治理论", "英语一", "中药综合"],
    "护理学": ["思想政治理论", "英语一", "护理综合"],
    "管理科学与工程": ["思想政治理论", "英语一", "数学三", "管理学综合"],
    "工商管理": ["思想政治理论", "英语一", "数学三", "管理学综合"],
    "农林经济管理": ["思想政治理论", "英语一", "数学三", "经济学综合"],
    "公共管理": ["思想政治理论", "英语一", "公共管理学", "公共政策学"],
    "图书情报与档案管理": ["思想政治理论", "英语一", "信息资源管理", "文献学"],
    "艺术学理论": ["思想政治理论", "英语一", "艺术概论", "艺术史"],
    "音乐与舞蹈学": ["思想政治理论", "英语一", "音乐理论", "专业技能"],
    "戏剧与影视学": ["思想政治理论", "英语一", "戏剧理论", "影视概论"],
    "美术学": ["思想政治理论", "英语一", "美术史", "美术理论"],
    "设计学": ["思想政治理论", "英语一", "设计史", "设计理论"],
}

# 专硕考试科目模板（部分专业不同）
EXAM_SUBJECTS_PRO = {
    "金融": ["思想政治理论", "英语二", "数学三", "金融学综合"],
    "应用统计": ["思想政治理论", "英语二", "数学三", "统计学"],
    "税务": ["思想政治理论", "英语二", "数学三", "税务专业基础"],
    "国际商务": ["思想政治理论", "英语二", "数学三", "国际商务专业基础"],
    "保险": ["思想政治理论", "英语二", "数学三", "保险专业基础"],
    "资产评估": ["思想政治理论", "英语二", "数学三", "资产评估专业基础"],
    "法律(非法学)": ["思想政治理论", "英语一", "法律硕士专业基础（非法学）", "法律硕士综合（非法学）"],
    "法律(法学)": ["思想政治理论", "英语一", "法律硕士专业基础（法学）", "法律硕士综合（法学）"],
    "社会工作": ["思想政治理论", "英语二", "社会工作原理", "社会工作实务"],
    "教育管理": ["思想政治理论", "英语二", "教育综合", "教育管理学"],
    "学科教学(语文)": ["思想政治理论", "英语二", "教育综合", "语文教学论"],
    "学科教学(数学)": ["思想政治理论", "英语二", "教育综合", "数学教学论"],
    "学科教学(英语)": ["思想政治理论", "英语二", "教育综合", "英语教学论"],
    "小学教育": ["思想政治理论", "英语二", "教育综合", "小学教育学"],
    "心理健康教育": ["思想政治理论", "英语二", "教育综合", "发展心理学"],
    "学前教育": ["思想政治理论", "英语二", "教育综合", "学前教育学"],
    "汉语国际教育": ["思想政治理论", "英语一", "汉语基础", "汉语国际教育基础"],
    "应用心理": ["思想政治理论", "英语二", "心理学专业综合"],
    "英语笔译": ["思想政治理论", "翻译硕士英语", "英语翻译基础", "汉语写作与百科知识"],
    "英语口译": ["思想政治理论", "翻译硕士英语", "英语翻译基础", "汉语写作与百科知识"],
    "新闻与传播": ["思想政治理论", "英语二", "新闻与传播专业基础", "新闻与传播综合能力"],
    "出版": ["思想政治理论", "英语二", "出版综合素质", "出版专业基础"],
    "文物与博物馆": ["思想政治理论", "英语二", "文博综合"],
    "建筑学": ["思想政治理论", "英语一", "建筑学基础", "建筑设计"],
    "城市规划": ["思想政治理论", "英语一", "城市规划原理", "城市规划设计"],
    "电子信息": ["思想政治理论", "英语二", "数学二", "电子信息专业基础"],
    "机械": ["思想政治理论", "英语二", "数学二", "机械设计基础"],
    "材料与化工": ["思想政治理论", "英语二", "数学二", "材料科学基础"],
    "资源与环境": ["思想政治理论", "英语二", "数学二", "环境工程原理"],
    "能源动力": ["思想政治理论", "英语二", "数学二", "工程热力学"],
    "土木水利": ["思想政治理论", "英语二", "数学二", "结构力学"],
    "生物与医药": ["思想政治理论", "英语二", "数学二", "生物化学"],
    "交通运输": ["思想政治理论", "英语二", "数学二", "交通运输工程学"],
    "农业": ["思想政治理论", "英语二", "农业知识综合", "农学概论"],
    "兽医": ["思想政治理论", "英语二", "兽医基础", "兽医临床"],
    "风景园林": ["思想政治理论", "英语二", "风景园林基础", "风景园林设计"],
    "林业": ["思想政治理论", "英语二", "林业基础知识综合", "森林培育学"],
    "临床医学": ["思想政治理论", "英语一", "西医综合"],
    "口腔医学": ["思想政治理论", "英语一", "口腔综合"],
    "公共卫生": ["思想政治理论", "英语一", "卫生综合"],
    "护理": ["思想政治理论", "英语一", "护理综合"],
    "药学": ["思想政治理论", "英语一", "药学综合"],
    "中药学": ["思想政治理论", "英语一", "中药综合"],
    "中医": ["思想政治理论", "英语一", "中医综合"],
    "工商管理": ["管理类联考综合能力", "英语二"],
    "公共管理": ["管理类联考综合能力", "英语二"],
    "会计": ["管理类联考综合能力", "英语二"],
    "旅游管理": ["管理类联考综合能力", "英语二"],
    "图书情报": ["管理类联考综合能力", "英语二"],
    "工程管理": ["管理类联考综合能力", "英语二"],
    "项目管理": ["管理类联考综合能力", "英语二"],
    "工业工程": ["管理类联考综合能力", "英语二"],
    "物流工程": ["管理类联考综合能力", "英语二"],
    "音乐": ["思想政治理论", "英语二", "音乐理论", "专业技能"],
    "戏剧": ["思想政治理论", "英语二", "戏剧理论", "戏剧创作"],
    "电影": ["思想政治理论", "英语二", "电影理论", "电影创作"],
    "广播电视": ["思想政治理论", "英语二", "广播电视理论", "广播电视实务"],
    "舞蹈": ["思想政治理论", "英语二", "舞蹈理论", "舞蹈表演"],
    "美术": ["思想政治理论", "英语二", "美术史", "美术创作"],
    "艺术设计": ["思想政治理论", "英语二", "设计史", "设计基础"],
}


def get_connection():
    return pymysql.connect(**DB_CONFIG)


def get_exam_subjects(major_name, degree_type, major_category_name):
    """根据专业生成考试科目"""
    if degree_type == 'professional':
        # 专硕先查找专硕模板
        for key, subjects in EXAM_SUBJECTS_PRO.items():
            if key in major_name:
                return subjects
        # 未找到则使用默认
        return ["思想政治理论", "英语二", "数学二", "专业基础"]
    else:
        # 学硕
        for key, subjects in EXAM_SUBJECTS.items():
            if key in major_category_name or key in major_name:
                return subjects
        # 尝试从专业名称匹配
        for key, subjects in EXAM_SUBJECTS.items():
            if key in major_name:
                return subjects
        return ["思想政治理论", "英语一", "数学一", "专业基础综合"]


def generate_enrollment_for_school_major(school, major, year):
    """为单个学校-专业-年份生成招生数据"""
    # 基础参数
    is_985 = school['is_985']
    is_211 = school['is_211']
    school_rank = school.get('ranking') or 200
    degree_type = major['degree_type']
    major_name = major['major_name']
    major_category = major.get('major_category_name') or ''
    discipline = major.get('discipline_name') or ''

    # 根据学校层次调整参数
    school_factor = 1.0
    if is_985:
        school_factor = 1.5
    elif is_211:
        school_factor = 1.2

    # 专业热门度系数
    hot_disciplines = ['计算机科学与技术', '软件工程', '电子信息', '金融', '法学', '临床医学', '工商管理', '会计', '教育学']
    cold_disciplines = ['哲学', '考古学', '世界史', '林业', '农业', '水产', '畜牧学']

    hot_factor = 1.0
    if any(h in major_name or h in major_category for h in hot_disciplines):
        hot_factor = 1.8
    elif any(c in major_name or c in major_category for c in cold_disciplines):
        hot_factor = 0.5

    # 计划招生人数
    if degree_type == 'professional':
        if '工商管理' in major_name or 'MBA' in major_name:
            planned = random.randint(200, 600)
        elif '公共管理' in major_name or 'MPA' in major_name:
            planned = random.randint(150, 400)
        elif '会计' in major_name:
            planned = random.randint(50, 120)
        elif '法律' in major_name:
            planned = random.randint(80, 200)
        elif '临床医学' in major_name:
            planned = random.randint(80, 200)
        else:
            planned = random.randint(20, 80)
    else:
        # 学硕
        planned = random.randint(8, 60)
        if '计算机' in major_name or '软件' in major_name:
            planned = random.randint(30, 80)
        elif '临床医学' in major_name:
            planned = random.randint(40, 120)

    # 实际录取人数
    actual = int(planned * random.uniform(0.85, 1.0))

    # 报名人数
    base_applicants = planned * random.uniform(3, 12) * school_factor * hot_factor
    application_count = int(base_applicants)

    # 推免人数
    if is_985:
        recommended = int(planned * random.uniform(0.3, 0.7))
    elif is_211:
        recommended = int(planned * random.uniform(0.15, 0.4))
    else:
        recommended = int(planned * random.uniform(0.05, 0.2))
    recommended = min(recommended, planned - 2)

    # 复试比
    retest_ratio = round(random.uniform(1.2, 1.8), 2)

    # 学费
    if degree_type == 'professional':
        if '工商管理' in major_name or 'MBA' in major_name:
            if is_985:
                tuition = random.choice([258000, 288000, 328000, 368000, 398000])
            elif is_211:
                tuition = random.choice([88000, 128000, 168000, 198000, 238000])
            else:
                tuition = random.choice([48000, 68000, 88000, 108000, 128000])
        elif '公共管理' in major_name or 'MPA' in major_name:
            tuition = random.choice([48000, 68000, 88000, 108000, 128000, 158000])
        elif '会计' in major_name:
            tuition = random.choice([28000, 48000, 68000, 88000, 108000, 128000])
        elif '法律' in major_name:
            tuition = random.choice([12000, 15000, 20000, 28000, 38000])
        elif '金融' in major_name:
            tuition = random.choice([28000, 48000, 68000, 88000, 128000])
        elif '临床医学' in major_name or '口腔医学' in major_name:
            tuition = random.choice([10000, 12000, 15000, 20000])
        else:
            tuition = random.choice([8000, 10000, 12000, 15000, 20000])
    else:
        # 学硕
        if '临床医学' in major_name or '口腔医学' in major_name:
            tuition = random.choice([8000, 10000, 12000])
        elif '艺术' in discipline or '艺术' in major_category:
            tuition = random.choice([12000, 15000, 20000])
        else:
            tuition = 8000

    # 学制
    if degree_type == 'professional':
        if '工商管理' in major_name or '公共管理' in major_name:
            academic_system = random.choice(["2年", "2.5年"])
        elif '会计' in major_name:
            academic_system = random.choice(["2年", "3年"])
        elif '法律' in major_name:
            academic_system = random.choice(["3年"])
        elif '金融' in major_name:
            academic_system = random.choice(["2年", "2.5年"])
        else:
            academic_system = random.choice(["2年", "2.5年", "3年"])
    else:
        academic_system = random.choice(["3年"])

    # 考试科目
    exam_subjects = get_exam_subjects(major_name, degree_type, major_category)

    # 院系名称
    department = generate_department_name(school['school_name'], major_category, discipline)

    return {
        'exam_year': year,
        'degree_type': degree_type,
        'study_mode': 'full_time',
        'department_name': department,
        'planned_enrollment': planned,
        'actual_enrollment': actual,
        'recommended_exemption_count': recommended,
        'application_count': application_count,
        'retest_ratio': retest_ratio,
        'tuition_fee': tuition,
        'academic_system': academic_system,
        'exam_subjects': exam_subjects,
    }


def generate_department_name(school_name, major_category, discipline):
    """生成院系名称"""
    dept_map = {
        '哲学': '哲学系',
        '理论经济学': '经济学院',
        '应用经济学': '经济学院',
        '金融硕士': '金融学院',
        '法学': '法学院',
        '政治学': '政府管理学院',
        '社会学': '社会学系',
        '马克思主义理论': '马克思主义学院',
        '教育学': '教育学院',
        '心理学': '心理学院',
        '体育学': '体育学院',
        '中国语言文学': '文学院',
        '外国语言文学': '外国语学院',
        '新闻传播学': '新闻与传播学院',
        '翻译硕士': '外国语学院',
        '新闻与传播硕士': '新闻与传播学院',
        '历史学': '历史学院',
        '考古学': '历史学院',
        '中国史': '历史学院',
        '世界史': '历史学院',
        '数学': '数学学院',
        '物理学': '物理学院',
        '化学': '化学学院',
        '生物学': '生命科学学院',
        '统计学': '统计学院',
        '系统科学': '数学学院',
        '力学': '力学与工程学院',
        '机械工程': '机械工程学院',
        '光学工程': '光电学院',
        '仪器科学与技术': '仪器科学与工程学院',
        '材料科学与工程': '材料科学与工程学院',
        '冶金工程': '冶金工程学院',
        '动力工程及工程热物理': '能源与动力学院',
        '电气工程': '电气工程学院',
        '电子科学与技术': '电子科学与工程学院',
        '信息与通信工程': '信息与通信工程学院',
        '控制科学与工程': '自动化学院',
        '计算机科学与技术': '计算机学院',
        '建筑学': '建筑学院',
        '土木工程': '土木工程学院',
        '水利工程': '水利工程学院',
        '化学工程与技术': '化学工程学院',
        '交通运输工程': '交通运输学院',
        '船舶与海洋工程': '船舶与海洋工程学院',
        '航空宇航科学与技术': '航空航天学院',
        '兵器科学与技术': '机电工程学院',
        '核科学与技术': '核科学与技术学院',
        '农业工程': '农业工程学院',
        '林业工程': '林业工程学院',
        '环境科学与工程': '环境学院',
        '生物医学工程': '生物医学工程学院',
        '食品科学与工程': '食品科学与工程学院',
        '软件工程': '软件学院',
        '作物学': '农学院',
        '园艺学': '园艺学院',
        '农业资源与环境': '资源与环境学院',
        '植物保护': '植物保护学院',
        '畜牧学': '动物科技学院',
        '兽医学': '兽医学院',
        '林学': '林学院',
        '水产': '水产学院',
        '基础医学': '基础医学院',
        '临床医学': '临床医学院',
        '口腔医学': '口腔医学院',
        '公共卫生与预防医学': '公共卫生学院',
        '中医学': '中医学院',
        '中西医结合': '中西医结合学院',
        '药学': '药学院',
        '中药学': '中药学院',
        '护理学': '护理学院',
        '管理科学与工程': '管理学院',
        '工商管理': '管理学院',
        '工商管理硕士': '管理学院',
        '会计硕士': '管理学院',
        '农林经济管理': '农林经济管理学院',
        '公共管理': '公共管理学院',
        '公共管理硕士': '公共管理学院',
        '图书情报与档案管理': '信息管理学院',
        '图书情报硕士': '信息管理学院',
        '艺术学理论': '艺术学院',
        '音乐与舞蹈学': '音乐学院',
        '戏剧与影视学': '戏剧学院',
        '美术学': '美术学院',
        '设计学': '设计学院',
        '艺术硕士': '艺术学院',
    }

    if major_category in dept_map:
        return dept_map[major_category]

    # 根据学科门类兜底
    discipline_dept = {
        '哲学': '哲学系',
        '经济学': '经济学院',
        '法学': '法学院',
        '教育学': '教育学院',
        '文学': '文学院',
        '历史学': '历史学院',
        '理学': '理学院',
        '工学': '工程学院',
        '农学': '农学院',
        '医学': '医学院',
        '管理学': '管理学院',
        '艺术学': '艺术学院',
    }
    return discipline_dept.get(discipline, '研究生院')


def get_suitable_majors(school, all_majors):
    """根据学校类型匹配合适的专业"""
    school_type = school.get('school_type') or '综合'
    is_985 = school['is_985']
    is_211 = school['is_211']

    # 专业数量
    if is_985:
        target_count = random.randint(35, 65)
    elif is_211:
        target_count = random.randint(25, 50)
    else:
        target_count = random.randint(12, 35)

    # 按学校类型筛选
    type_discipline_map = {
        '理工': ['工学', '理学', '管理学'],
        '师范': ['教育学', '文学', '理学', '法学', '管理学', '艺术学'],
        '医药': ['医学', '理学'],
        '农林': ['农学', '理学', '工学'],
        '财经': ['经济学', '管理学'],
        '政法': ['法学', '管理学', '经济学'],
        '语言': ['文学', '法学', '教育学'],
        '艺术': ['艺术学', '文学'],
        '体育': ['教育学', '医学'],
        '民族': ['文学', '法学', '教育学', '管理学'],
        '综合': ['工学', '理学', '经济学', '管理学', '文学', '法学', '教育学', '医学', '艺术学', '历史学', '哲学', '农学'],
    }

    preferred_disciplines = type_discipline_map.get(school_type, type_discipline_map['综合'])

    # 优先选择匹配学科门类的专业
    matched = []
    for m in all_majors:
        disc = m.get('discipline_name') or ''
        if disc in preferred_disciplines:
            matched.append(m)

    # 如果匹配太少，补充其他
    if len(matched) < target_count:
        other = [m for m in all_majors if m not in matched]
        matched.extend(other[:target_count - len(matched)])

    # 随机选择目标数量
    if len(matched) > target_count:
        matched = random.sample(matched, target_count)

    return matched


def generate_all_enrollment_data(years=None, clear_existing=False):
    """生成所有学校的招生数据"""
    if years is None:
        years = [2023, 2024, 2025]

    conn = get_connection()
    try:
        cursor = conn.cursor()

        # 获取所有学校
        cursor.execute("""
            SELECT id, school_name, school_code, province, city,
                   school_type, is_985, is_211, is_double_first_class,
                   ranking
            FROM schools WHERE status = 'active'
            ORDER BY ranking IS NULL, ranking
        """)
        schools = cursor.fetchall()
        logger.info(f"共有 {len(schools)} 所学校")

        # 获取所有专业
        cursor.execute("""
            SELECT id, major_code, major_name, degree_type,
                   discipline_code, discipline_name, major_category_name
            FROM majors WHERE is_active = 1
        """)
        majors = cursor.fetchall()
        logger.info(f"共有 {len(majors)} 个专业")

        if clear_existing:
            cursor.execute("DELETE FROM enrollment_records")
            logger.info("已清空现有招生数据")

        # 统计已存在的记录
        cursor.execute("SELECT COUNT(*) as cnt FROM enrollment_records")
        existing_count = cursor.fetchone()['cnt']
        logger.info(f"已有招生记录: {existing_count} 条")

        total_inserted = 0
        total_skipped = 0

        for i, school in enumerate(schools):
            school_id = school['id']
            school_name = school['school_name']

            # 获取该校已有的专业关联
            cursor.execute("""
                SELECT major_id FROM school_majors
                WHERE school_id = %s AND is_active = 1
            """, (school_id,))
            linked_major_ids = {row['major_id'] for row in cursor.fetchall()}

            # 如果没有关联专业，自动匹配
            if not linked_major_ids:
                suitable_majors = get_suitable_majors(school, majors)
                # 建立关联
                for m in suitable_majors:
                    cursor.execute("""
                        INSERT IGNORE INTO school_majors (school_id, major_id, is_active)
                        VALUES (%s, %s, 1)
                    """, (school_id, m['id']))
                    linked_major_ids.add(m['id'])
            else:
                suitable_majors = [m for m in majors if m['id'] in linked_major_ids]

            school_inserted = 0

            for major in suitable_majors:
                major_id = major['id']

                for year in years:
                    # 检查是否已存在
                    cursor.execute("""
                        SELECT id FROM enrollment_records
                        WHERE school_id = %s AND major_id = %s AND exam_year = %s
                    """, (school_id, major_id, year))

                    if cursor.fetchone():
                        total_skipped += 1
                        continue

                    # 生成数据
                    data = generate_enrollment_for_school_major(school, major, year)
                    exam_subjects_json = json.dumps(data['exam_subjects'], ensure_ascii=False)

                    cursor.execute("""
                        INSERT INTO enrollment_records (
                            school_id, major_id, exam_year, degree_type, study_mode,
                            department_name, planned_enrollment, actual_enrollment,
                            recommended_exemption_count, application_count,
                            retest_ratio, tuition_fee, academic_system,
                            exam_subjects, data_source, source_updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        school_id, major_id, data['exam_year'], data['degree_type'], data['study_mode'],
                        data['department_name'], data['planned_enrollment'], data['actual_enrollment'],
                        data['recommended_exemption_count'], data['application_count'],
                        data['retest_ratio'], data['tuition_fee'], data['academic_system'],
                        exam_subjects_json, '系统生成', datetime.now()
                    ))

                    total_inserted += 1
                    school_inserted += 1

            if school_inserted > 0 and (i + 1) % 10 == 0:
                logger.info(f"已处理 {i + 1}/{len(schools)} 所学校, 新增 {total_inserted} 条记录")

        # 最后统计
        cursor.execute("SELECT COUNT(*) as cnt FROM enrollment_records")
        final_count = cursor.fetchone()['cnt']

        logger.info("=" * 60)
        logger.info(f"数据生成完成!")
        logger.info(f"  新增记录: {total_inserted} 条")
        logger.info(f"  跳过记录: {total_skipped} 条")
        logger.info(f"  最终总量: {final_count} 条")
        logger.info("=" * 60)

        # 各年份统计
        for year in years:
            cursor.execute("SELECT COUNT(*) as cnt FROM enrollment_records WHERE exam_year = %s", (year,))
            year_count = cursor.fetchone()['cnt']
            logger.info(f"  {year}年: {year_count} 条")

    finally:
        conn.close()


if __name__ == "__main__":
    import sys
    clear_flag = '--clear' in sys.argv
    generate_all_enrollment_data(years=[2023, 2024, 2025], clear_existing=clear_flag)
