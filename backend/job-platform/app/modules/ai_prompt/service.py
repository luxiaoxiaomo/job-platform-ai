"""
AI prompt configuration and job pre-review service.
"""
from datetime import datetime, timezone
from string import Template

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai_prompt.models import AiPromptConfig
from app.modules.ai_prompt.repository import AiPromptConfigRepository
from app.modules.ai_prompt.schemas import (
    AiPromptConfigCreate,
    AiPromptConfigListResponse,
    AiPromptConfigResponse,
    JobPreReviewFinding,
    JobPreReviewRequest,
    JobPreReviewResponse,
    PromptTestRequest,
)
from app.modules.user.models import User


JOB_CONTENT_REVIEW_SCENARIO = "job_content_review"

DEFAULT_JOB_REVIEW_SYSTEM_PROMPT = """你是招聘平台岗位内容审核助手。
请审核岗位发布内容是否合规、真实、完整、清晰。
重点检查歧视性要求、虚假夸大、违法违规、隐私和导流、信息完整性、内容一致性。
只输出符合约定 JSON schema 的结果，不输出解释性正文。"""

DEFAULT_JOB_REVIEW_USER_PROMPT_TEMPLATE = """请审核以下岗位：
岗位名称：$title
工作城市：$city
薪资范围：$salary_min-$salary_max K
经验要求：$experience
学历要求：$education
岗位职责：
$description
任职要求：
$requirement
福利待遇：
$benefits
标签：$tags"""

DEFAULT_JOB_REVIEW_OUTPUT_SCHEMA = """{
  "level": "pass | warning | block",
  "summary": "一句话结论",
  "findings": [
    {
      "category": "风险类别",
      "severity": "warning | block",
      "evidence": "命中的原文",
      "suggestion": "修改建议"
    }
  ],
  "rewrite_suggestions": {
    "description": "可选，优化后的职责",
    "requirement": "可选，优化后的要求"
  }
}"""


def _config_to_response(config: AiPromptConfig) -> AiPromptConfigResponse:
    return AiPromptConfigResponse(
        id=config.id,
        scenario_key=config.scenario_key,
        name=config.name,
        version=config.version,
        system_prompt=config.system_prompt,
        user_prompt_template=config.user_prompt_template,
        output_schema=config.output_schema,
        is_active=config.is_active,
        created_by=config.created_by,
        published_by=config.published_by,
        published_at=config.published_at,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


def _default_config_response() -> AiPromptConfigResponse:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    return AiPromptConfigResponse(
        scenario_key=JOB_CONTENT_REVIEW_SCENARIO,
        name="岗位内容预审默认提示词",
        version=1,
        system_prompt=DEFAULT_JOB_REVIEW_SYSTEM_PROMPT,
        user_prompt_template=DEFAULT_JOB_REVIEW_USER_PROMPT_TEMPLATE,
        output_schema=DEFAULT_JOB_REVIEW_OUTPUT_SCHEMA,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


def render_job_review_prompt(template: str, job: JobPreReviewRequest) -> str:
    values = job.model_dump()
    values["salary_min"] = values.get("salary_min") or ""
    values["salary_max"] = values.get("salary_max") or ""
    values["benefits"] = values.get("benefits") or ""
    values["tags"] = "、".join(values.get("tags") or [])
    return Template(template).safe_substitute(values)


def run_local_job_review(job: JobPreReviewRequest, prompt_version: int, prompt_source: str) -> JobPreReviewResponse:
    text = "\n".join(
        str(value)
        for value in [
            job.title,
            job.city,
            job.experience,
            job.education,
            job.description,
            job.requirement,
            job.benefits,
            " ".join(job.tags),
        ]
        if value
    )

    rules = [
        ("歧视性用语", "block", ["仅限男性", "限男性", "男性优先", "仅限女性", "限女性", "女性优先", "不要女生", "不要男生"], "删除性别限制，改为与岗位能力直接相关的要求。"),
        ("年龄限制", "block", ["35岁以下", "30岁以下", "年龄不超过", "限35岁", "限30岁"], "删除年龄门槛，改为经验、技能、体力或排班等客观要求。"),
        ("夸大承诺", "warning", ["轻松月入", "稳赚", "保底年薪百万", "躺赚", "无需经验月入"], "避免无法验证的收益承诺，使用明确薪资范围和绩效规则。"),
        ("外部联系方式", "warning", ["微信", "加v", "加 V", "QQ", "电话联系", "手机号"], "建议使用平台内沟通或企业公开邮箱，避免绕开平台对接流程。"),
    ]

    findings: list[JobPreReviewFinding] = []
    for category, severity, patterns, suggestion in rules:
        hit = next((pattern for pattern in patterns if pattern in text), None)
        if hit:
            findings.append(
                JobPreReviewFinding(
                    category=category,
                    severity=severity,
                    evidence=hit,
                    suggestion=suggestion,
                )
            )

    if len((job.description or "").strip()) < 30:
        findings.append(
            JobPreReviewFinding(
                category="职责描述偏短",
                severity="warning",
                evidence="工作职责",
                suggestion="补充 3-5 条具体工作内容，便于求职者判断匹配度。",
            )
        )
    if len((job.requirement or "").strip()) < 30:
        findings.append(
            JobPreReviewFinding(
                category="任职要求偏短",
                severity="warning",
                evidence="任职要求",
                suggestion="补充技能、经验、协作方式等客观要求。",
            )
        )

    if any(item.severity == "block" for item in findings):
        level = "block"
        summary = "检测到严重违规风险，需修改后再提交人工审核。"
    elif findings:
        level = "warning"
        summary = "检测到可优化项，不阻断提交，但会随岗位进入人工审核记录。"
    else:
        level = "pass"
        summary = "未检测到明显违规风险，岗位将进入平台审核队列。"

    return JobPreReviewResponse(
        level=level,
        summary=summary,
        findings=findings,
        prompt_version=prompt_version,
        prompt_source=prompt_source,
    )


class AiPromptService:
    @staticmethod
    async def list_configs(db: AsyncSession, scenario_key: str) -> AiPromptConfigListResponse:
        items, total = await AiPromptConfigRepository.list_by_scenario(db, scenario_key)
        if total == 0 and scenario_key == JOB_CONTENT_REVIEW_SCENARIO:
            default = _default_config_response()
            return AiPromptConfigListResponse(items=[default], total=1)
        return AiPromptConfigListResponse(items=[_config_to_response(item) for item in items], total=total)

    @staticmethod
    async def get_active(db: AsyncSession, scenario_key: str) -> AiPromptConfigResponse:
        config = await AiPromptConfigRepository.get_active(db, scenario_key)
        if config is None:
            if scenario_key == JOB_CONTENT_REVIEW_SCENARIO:
                return _default_config_response()
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active prompt config")
        return _config_to_response(config)

    @staticmethod
    async def create_config(db: AsyncSession, admin: User, data: AiPromptConfigCreate) -> AiPromptConfigResponse:
        version = await AiPromptConfigRepository.next_version(db, data.scenario_key)
        config = AiPromptConfig(
            scenario_key=data.scenario_key,
            name=data.name,
            version=version,
            system_prompt=data.system_prompt,
            user_prompt_template=data.user_prompt_template,
            output_schema=data.output_schema,
            is_active=False,
            created_by=admin.id,
        )
        created = await AiPromptConfigRepository.create(db, config)
        return _config_to_response(created)

    @staticmethod
    async def publish_config(db: AsyncSession, admin: User, config_id: int) -> AiPromptConfigResponse:
        config = await AiPromptConfigRepository.get_by_id(db, config_id)
        if config is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt config not found")
        config.published_by = admin.id
        config.published_at = datetime.now(timezone.utc).replace(tzinfo=None)
        published = await AiPromptConfigRepository.publish(db, config)
        return _config_to_response(published)

    @staticmethod
    async def test_prompt(data: PromptTestRequest) -> JobPreReviewResponse:
        _ = render_job_review_prompt(data.user_prompt_template, data.job)
        return run_local_job_review(data.job, prompt_version=0, prompt_source="test_local_rules")

    @staticmethod
    async def pre_review_job(db: AsyncSession, job: JobPreReviewRequest) -> JobPreReviewResponse:
        active = await AiPromptService.get_active(db, JOB_CONTENT_REVIEW_SCENARIO)
        _ = render_job_review_prompt(active.user_prompt_template, job)
        source = "active_prompt" if active.id else "default_prompt"
        return run_local_job_review(job, prompt_version=active.version, prompt_source=source)
