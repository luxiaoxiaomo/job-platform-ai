"""
Rule-based salary suggestion for job posting.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.modules.job.schemas import JobSalarySuggestionRequest, JobSalarySuggestionResponse


@dataclass(frozen=True)
class SalaryBand:
    low: float
    high: float


BASE_BANDS = [
    (("后端", "服务端", "python", "java", "fastapi", "spring"), SalaryBand(18, 32), "后端开发"),
    (("前端", "react", "vue", "javascript", "typescript"), SalaryBand(15, 28), "前端开发"),
    (("算法", "机器学习", "大模型", "nlp", "ai"), SalaryBand(25, 45), "算法/AI"),
    (("数据", "bi", "分析师", "sql"), SalaryBand(16, 30), "数据分析"),
    (("产品", "产品经理"), SalaryBand(18, 35), "产品经理"),
    (("测试", "qa"), SalaryBand(12, 22), "测试工程师"),
    (("运维", "devops", "sre"), SalaryBand(15, 28), "运维/SRE"),
    (("设计", "ui", "ux"), SalaryBand(12, 24), "设计"),
    (("销售", "客户"), SalaryBand(8, 18), "销售"),
    (("运营", "增长"), SalaryBand(9, 18), "运营"),
]

CITY_FACTORS = [
    (("北京", "上海", "深圳"), 1.12, "一线城市"),
    (("杭州", "广州"), 1.06, "强二线/互联网集中城市"),
    (("南京", "苏州", "成都", "武汉", "西安"), 0.94, "新一线城市"),
    (("重庆", "天津", "青岛", "厦门"), 0.9, "重点城市"),
]

EXPERIENCE_FACTORS = [
    (("应届", "校招", "0年", "无经验"), 0.72, "应届/无经验"),
    (("1-3", "1年", "2年", "3年"), 0.9, "1-3年经验"),
    (("3-5", "4年", "5年"), 1.08, "3-5年经验"),
    (("5-10", "6年", "7年", "8年", "高级", "资深"), 1.28, "5年以上/高级"),
    (("10", "专家", "负责人", "架构"), 1.45, "专家/负责人"),
]

EDUCATION_FACTORS = [
    (("博士",), 1.18, "博士"),
    (("硕士", "研究生"), 1.08, "硕士"),
    (("本科",), 1.0, "本科"),
    (("大专", "专科"), 0.92, "大专"),
]

TAG_PREMIUMS = [
    (("大模型", "llm", "算法", "机器学习"), 1.15, "AI/算法技能溢价"),
    (("fastapi", "python", "java", "spring boot", "微服务"), 1.06, "主流后端技术栈"),
    (("react", "typescript", "前端工程化"), 1.05, "前端工程化技能"),
    (("kubernetes", "k8s", "devops", "sre"), 1.08, "稳定性/云原生技能"),
]

BENCHMARK_COMPANIES = {
    "后端开发": ["同城互联网企业", "SaaS 公司", "中型科技公司"],
    "前端开发": ["同城互联网企业", "B 端 SaaS 公司", "数字化服务商"],
    "算法/AI": ["AI 创业公司", "大模型应用团队", "互联网平台"],
    "产品经理": ["B 端软件公司", "互联网产品团队", "行业 SaaS 公司"],
    "default": ["同城招聘岗位", "同规模企业", "行业中位样本"],
}


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def _match_factor(text: str, candidates, default_factor: float, default_label: str) -> tuple[float, str]:
    for keywords, factor, label in candidates:
        if _contains_any(text, keywords):
            return factor, label
    return default_factor, default_label


def suggest_salary(data: JobSalarySuggestionRequest) -> JobSalarySuggestionResponse:
    text = " ".join([data.title, data.city, data.experience, data.education, " ".join(data.tags or [])])

    role_band = SalaryBand(12, 24)
    role_label = "通用岗位"
    for keywords, band, label in BASE_BANDS:
        if _contains_any(text, keywords):
            role_band = band
            role_label = label
            break

    city_factor, city_label = _match_factor(data.city, CITY_FACTORS, 0.82, "普通城市")
    exp_factor, exp_label = _match_factor(data.experience, EXPERIENCE_FACTORS, 0.96, "经验不限/未明确")
    edu_factor, edu_label = _match_factor(data.education, EDUCATION_FACTORS, 0.96, "学历不限/未明确")

    premium_factor = 1.0
    premium_labels = []
    for keywords, factor, label in TAG_PREMIUMS:
        if _contains_any(text, keywords):
            premium_factor *= factor
            premium_labels.append(label)

    multiplier = city_factor * exp_factor * edu_factor * premium_factor
    low = max(4, round(role_band.low * multiplier))
    high = max(low + 2, round(role_band.high * multiplier))
    market_median = round((low + high) / 2)
    benchmark_median = round(market_median * 1.06)

    confidence = 0.68
    if role_label != "通用岗位":
        confidence += 0.08
    if city_label != "普通城市":
        confidence += 0.05
    if exp_label != "经验不限/未明确":
        confidence += 0.05
    if premium_labels:
        confidence += 0.04
    confidence = min(confidence, 0.9)

    factors = [role_label, city_label, exp_label, edu_label, *premium_labels]
    return JobSalarySuggestionResponse(
        salary_min=low,
        salary_max=high,
        market_median=market_median,
        benchmark_median=benchmark_median,
        confidence=round(confidence, 2),
        basis=f"基于{role_label}、{city_label}、{exp_label}、{edu_label}和岗位标签的规则估算",
        benchmark_companies=BENCHMARK_COMPANIES.get(role_label, BENCHMARK_COMPANIES["default"]),
        factors=factors,
    )
