"""Pure baseline seeker-job scoring."""

import re
from typing import Any

from app.modules.job.models import Job
from app.modules.match.config import MatchRuleDimensionConfig
from app.modules.match.schemas import MatchDimensionResponse


KNOWN_SKILLS = [
    "PeopleSoft",
    "HCM",
    "ERP",
    "Oracle",
    "SAP",
    "Python",
    "Java",
    "JavaScript",
    "TypeScript",
    "React",
    "Vue",
    "Node.js",
    "SQL",
    "MySQL",
    "PostgreSQL",
    "Excel",
    "PMP",
]
EDUCATION_RANKS = {
    "不限": 0,
    "中专": 1,
    "高中": 1,
    "大专": 2,
    "专科": 2,
    "本科": 3,
    "硕士": 4,
    "研究生": 4,
    "博士": 5,
}


class BaselineMatchScorer:
    """Deterministic baseline scoring with no database side effects."""

    @staticmethod
    def dimension(key, score, *, matched=None, missing=None, explanation):
        return MatchDimensionResponse(
            key=key,
            label=key,
            score=max(0, min(100, round(score))),
            weight=0,
            configured_weight=0,
            effective_weight=0,
            weighted_score=0,
            matched=matched or [],
            missing=missing or [],
            explanation=explanation,
            description="",
            scoring_method="",
            logic={},
        )

    @staticmethod
    def apply_dimension_config(dimension, config: MatchRuleDimensionConfig):
        weighted_score = round(dimension.score * config.effective_weight / 100, 2)
        return dimension.model_copy(
            update={
                "label": config.label,
                "weight": int(config.effective_weight)
                if float(config.effective_weight).is_integer()
                else config.effective_weight,
                "configured_weight": config.configured_weight,
                "effective_weight": config.effective_weight,
                "weighted_score": int(weighted_score)
                if weighted_score.is_integer()
                else weighted_score,
                "description": config.description,
                "scoring_method": config.scoring_method,
                "logic": config.logic,
            }
        )

    @classmethod
    def score_skill(cls, job: Job, resume_skills: list[Any]) -> MatchDimensionResponse:
        candidate_skills = cls.normalize_terms(
            [skill.skill_name for skill in resume_skills]
        )
        job_skills = cls.job_skill_terms(job)
        if not job_skills:
            return cls.dimension(
                "skill",
                70 if candidate_skills else 50,
                explanation="岗位暂未识别出明确技能要求，技能维度按中性分处理。",
            )
        candidate_keys = {item.lower() for item in candidate_skills}
        matched = [skill for skill in job_skills if skill.lower() in candidate_keys]
        missing = [skill for skill in job_skills if skill not in matched]
        score = (
            35 if not candidate_skills else 40 + (len(matched) / len(job_skills)) * 60
        )
        return cls.dimension(
            "skill",
            score,
            matched=[f"技能命中 {item}" for item in matched],
            missing=[f"岗位要求 {item}，简历中未识别到" for item in missing[:5]],
            explanation="根据岗位标签、任职要求和简历技能做规则匹配。",
        )

    @classmethod
    def score_experience(
        cls, job: Job, work_years: float | None
    ) -> MatchDimensionResponse:
        required_years = cls.parse_required_years(job.experience)
        if required_years is None:
            return cls.dimension(
                "experience",
                80,
                matched=["岗位不限经验"],
                explanation="岗位未设置明确年限要求。",
            )
        if work_years is None:
            return cls.dimension(
                "experience",
                50,
                missing=[f"岗位要求约 {required_years:g} 年经验，简历未识别到工作年限"],
                explanation="简历缺少工作年限，经验维度按保守分处理。",
            )
        if work_years >= required_years:
            score, matched, missing = (
                100,
                [f"工作年限 {work_years:g} 年，满足岗位要求 {required_years:g} 年"],
                [],
            )
        else:
            gap = required_years - work_years
            score, matched, missing = (
                (75 if gap <= 1 else 55 if gap <= 3 else 35),
                [],
                [f"工作年限 {work_years:g} 年，低于岗位要求 {required_years:g} 年"],
            )
        return cls.dimension(
            "experience",
            score,
            matched=matched,
            missing=missing,
            explanation="根据岗位经验要求和简历工作年限计算。",
        )

    @classmethod
    def score_education(
        cls, job: Job, candidate_education: str | None
    ) -> MatchDimensionResponse:
        required_rank = cls.education_rank(job.education)
        if required_rank == 0:
            return cls.dimension(
                "education",
                80,
                matched=["岗位不限学历"],
                explanation="岗位未设置明确学历门槛。",
            )
        candidate_rank = cls.education_rank(candidate_education)
        if candidate_rank == 0:
            return cls.dimension(
                "education",
                50,
                missing=[f"岗位要求 {job.education}，简历未识别到最高学历"],
                explanation="简历缺少最高学历，学历维度按保守分处理。",
            )
        if candidate_rank >= required_rank:
            return cls.dimension(
                "education",
                100,
                matched=[
                    f"最高学历 {candidate_education}，满足岗位要求 {job.education}"
                ],
                explanation="候选人学历满足或高于岗位要求。",
            )
        return cls.dimension(
            "education",
            70 if required_rank - candidate_rank == 1 else 45,
            missing=[f"最高学历 {candidate_education}，低于岗位要求 {job.education}"],
            explanation="候选人学历低于岗位要求。",
        )

    @classmethod
    def score_city(cls, job: Job, current_city: str | None) -> MatchDimensionResponse:
        if not current_city:
            return cls.dimension(
                "city",
                50,
                missing=[f"岗位城市为 {job.city}，简历未填写当前城市"],
                explanation="简历缺少当前城市，城市维度按保守分处理。",
            )
        if cls.contains_same_term(current_city, job.city):
            return cls.dimension(
                "city",
                100,
                matched=[f"当前城市与岗位城市一致：{job.city}"],
                explanation="当前城市与岗位城市一致。",
            )
        return cls.dimension(
            "city",
            40,
            missing=[f"当前城市 {current_city} 与岗位城市 {job.city} 不一致"],
            explanation="当前城市和岗位城市不一致。",
        )

    @classmethod
    def score_salary(
        cls, job: Job, expected_salary: str | None
    ) -> MatchDimensionResponse:
        expected_range = cls.parse_salary_range(expected_salary)
        if expected_range is None:
            return cls.dimension(
                "salary",
                60,
                missing=["简历未填写期望薪资"],
                explanation="缺少期望薪资，薪资维度按中性分处理。",
            )
        expected_min, expected_max = expected_range
        if expected_min <= job.salary_max and expected_max >= job.salary_min:
            return cls.dimension(
                "salary",
                100,
                matched=[
                    f"期望薪资 {expected_min:g}-{expected_max:g}K 与岗位 {job.salary_min}-{job.salary_max}K 有重叠"
                ],
                explanation="期望薪资与岗位薪资区间有重叠。",
            )
        return cls.dimension(
            "salary",
            50,
            missing=[
                f"期望薪资 {expected_min:g}-{expected_max:g}K 与岗位 {job.salary_min}-{job.salary_max}K 不重叠"
            ],
            explanation="期望薪资与岗位薪资区间不重叠。",
        )

    @classmethod
    def score_intention(
        cls, job: Job, target_position: str | None
    ) -> MatchDimensionResponse:
        if not target_position:
            return cls.dimension(
                "intention",
                50,
                missing=["简历未填写目标岗位"],
                explanation="缺少目标岗位，岗位意向维度按保守分处理。",
            )
        overlap = cls.tokenize(job.title) & cls.tokenize(target_position)
        score = (
            100
            if cls.contains_same_term(job.title, target_position) or len(overlap) >= 2
            else 75
            if overlap
            else 30
        )
        return cls.dimension(
            "intention",
            score,
            matched=[f"岗位意向命中 {item}" for item in sorted(overlap)],
            missing=[]
            if overlap
            else [f"目标岗位 {target_position} 与岗位 {job.title} 相关度较低"],
            explanation="根据岗位标题和求职目标的关键词重合度计算。",
        )

    @staticmethod
    def overall_score(dimensions):
        return round(sum(item.weighted_score for item in dimensions))

    @staticmethod
    def level_and_recommendation(score):
        return (
            ("high", "建议投递")
            if score >= 80
            else ("medium", "可尝试投递")
            if score >= 60
            else ("low", "谨慎投递")
        )

    @staticmethod
    def summary(score, highlights, gaps):
        if score >= 80:
            return "你的画像与该岗位匹配度较高，建议优先投递。"
        if score >= 60:
            return "你的画像与该岗位有一定匹配度，可结合缺口项判断是否投递。"
        return (
            "当前画像与该岗位存在明显缺口，建议补充相关经历后再投递。"
            if gaps
            else "当前信息不足，建议先完善简历画像后再查看匹配结果。"
        )

    @staticmethod
    def build_highlights(dimensions):
        return [
            item
            for dimension in dimensions
            if dimension.score >= 80
            for item in dimension.matched[:2]
        ][:6]

    @staticmethod
    def build_gaps(dimensions):
        return [
            item
            for dimension in dimensions
            if dimension.score < 80
            for item in dimension.missing[:2]
        ][:6]

    @classmethod
    def job_skill_terms(cls, job):
        terms = [str(tag) for tag in job.tags] if isinstance(job.tags, list) else []
        source_text = " ".join(
            [job.title or "", job.description or "", job.requirement or ""]
        )
        terms.extend(
            skill
            for skill in KNOWN_SKILLS
            if re.search(
                rf"(?<![A-Za-z0-9]){re.escape(skill)}(?![A-Za-z0-9])",
                source_text,
                flags=re.IGNORECASE,
            )
        )
        return cls.normalize_terms(terms)

    @staticmethod
    def normalize_terms(values):
        cleaned = []
        for value in values:
            item = str(value).strip()
            if item and item.lower() not in {existing.lower() for existing in cleaned}:
                cleaned.append(item)
        return cleaned

    @staticmethod
    def parse_required_years(value):
        if not value or "不限" in value:
            return None
        match = re.search(r"(\d+(?:\.\d+)?)\s*(?:年|年以上|\+)", value)
        return float(match.group(1)) if match else None

    @staticmethod
    def education_rank(value):
        return next(
            (
                rank
                for label, rank in EDUCATION_RANKS.items()
                if value and label in value
            ),
            0,
        )

    @staticmethod
    def parse_salary_range(value):
        numbers = [float(item) for item in re.findall(r"\d+(?:\.\d+)?", value or "")]
        return (
            None
            if not numbers
            else (numbers[0], numbers[0])
            if len(numbers) == 1
            else (min(numbers[:2]), max(numbers[:2]))
        )

    @staticmethod
    def contains_same_term(left, right):
        if not left or not right:
            return False
        left_text, right_text = left.strip().lower(), right.strip().lower()
        return left_text in right_text or right_text in left_text

    @staticmethod
    def tokenize(value):
        if not value:
            return set()
        return set(re.findall(r"[A-Za-z][A-Za-z0-9+#.]*", value.lower())) | set(
            re.findall(r"[\u4e00-\u9fa5]{2,}", value)
        )
