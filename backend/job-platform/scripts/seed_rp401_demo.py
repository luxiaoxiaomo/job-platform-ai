"""Seed deterministic R-P4-01 Match Quality P1 demo data.

This script is local-only. It creates a repeatable data set that makes the
Match Quality page show usable samples, high-risk anomalies, tuning
suggestions, and treatment-likely-better experiment confidence.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
import sys

from sqlalchemy import delete, select

logging.getLogger("passlib").setLevel(logging.ERROR)

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EARLY_BLOCKED_ENVIRONMENTS = {"production", "prod"}


def _assert_not_explicit_production_environment() -> None:
    environment = (os.getenv("APP_ENV") or os.getenv("ENVIRONMENT") or "local-demo").strip().lower()
    if environment in EARLY_BLOCKED_ENVIRONMENTS:
        raise RuntimeError(
            "RP401 demo seed is LOCAL_DEMO_ONLY and uses NOT_PRODUCTION_CREDENTIALS; "
            "it must not run when APP_ENV/ENVIRONMENT is production."
        )


_assert_not_explicit_production_environment()

from app.core.security import hash_password  # noqa: E402
from app.db.session import AsyncSessionLocal  # noqa: E402
from app.modules.application.models import JobApplication  # noqa: E402
from app.modules.base_data.models import StandardPosition  # noqa: E402
from app.modules.job.models import Job, JobFavorite, JobVisit  # noqa: E402
from app.modules.match.models import MatchRuleExperimentModel, MatchRuleMatchAuditModel  # noqa: E402
from app.modules.match.service import MatchService  # noqa: E402
from app.modules.user.models import User  # noqa: E402
from app.utils.encryption import encryptor  # noqa: E402
from app.utils.phone_hash import hash_phone  # noqa: E402


ADMIN_PHONE = "13700137001"
ADMIN_PASSWORD = "Admin1234"
RECRUITER_PHONE = "13940100001"
RECRUITER_PASSWORD = "Recruiter123"
SEEKER_PASSWORD = "Test1234"
SOURCE = "rp401_demo"
CATEGORY = "RP401-Tech"
CITY_RISK = "RP401-Shanghai"
CITY_HEALTHY = "RP401-Beijing"
OUT = PROJECT_ROOT / "frontend" / "wechat-prototype" / "output" / "playwright" / "rp401-demo-seed.json"
RP401_DEMO_BOUNDARY = {
    "scope": "MATCH_QUALITY_ONLY",
    "credential_scope": "LOCAL_DEMO_ONLY",
    "credential_warning": "NOT_PRODUCTION_CREDENTIALS",
    "launch_evidence": "NOT_FULL_BUSINESS_LOOP_EVIDENCE",
}
BLOCKED_ENVIRONMENTS = {"production", "prod"}


def assert_demo_environment() -> None:
    """Reject explicit production environments without reading secret files."""
    environment = (os.getenv("APP_ENV") or os.getenv("ENVIRONMENT") or "local-demo").strip().lower()
    if environment in BLOCKED_ENVIRONMENTS:
        raise RuntimeError(
            "RP401 demo seed is LOCAL_DEMO_ONLY and uses NOT_PRODUCTION_CREDENTIALS; "
            "it must not run when APP_ENV/ENVIRONMENT is production."
        )


async def get_or_create_user(session, *, phone: str, role: str, display_name: str, password: str) -> User:
    result = await session.execute(select(User).where(User.phone_hash == hash_phone(phone)))
    user = result.scalar_one_or_none()
    if user:
        user.role = role
        user.display_name = display_name
        user.status = "active"
        user.password_hash = hash_password(password)
        return user
    user = User(
        phone_hash=hash_phone(phone),
        phone_encrypted=encryptor.encrypt(phone),
        password_hash=hash_password(password),
        display_name=display_name,
        role=role,
        status="active",
    )
    session.add(user)
    await session.flush()
    return user


async def cleanup_previous_demo(session) -> None:
    audit_result = await session.execute(select(MatchRuleMatchAuditModel).where(MatchRuleMatchAuditModel.source == SOURCE))
    audits = list(audit_result.scalars().all())
    job_ids = {audit.job_id for audit in audits}
    seeker_ids = {audit.seeker_id for audit in audits}

    await session.execute(delete(MatchRuleMatchAuditModel).where(MatchRuleMatchAuditModel.source == SOURCE))
    if job_ids:
        await session.execute(delete(JobApplication).where(JobApplication.job_id.in_(job_ids)))
        await session.execute(delete(JobFavorite).where(JobFavorite.job_id.in_(job_ids)))
        await session.execute(delete(JobVisit).where(JobVisit.job_id.in_(job_ids)))
        await session.execute(delete(Job).where(Job.id.in_(job_ids)))
    if seeker_ids:
        await session.execute(delete(User).where(User.id.in_(seeker_ids)))
    await session.execute(delete(MatchRuleExperimentModel).where(MatchRuleExperimentModel.name == "RP401 Demo Experiment"))
    await session.commit()


async def get_or_create_position(session) -> StandardPosition:
    result = await session.execute(select(StandardPosition).where(StandardPosition.name == "RP401 Quality Engineer"))
    position = result.scalar_one_or_none()
    if position:
        position.category = CATEGORY
        position.status = "active"
        return position
    position = StandardPosition(
        name="RP401 Quality Engineer",
        category=CATEGORY,
        aliases=["Quality Insight Engineer", "Match Quality Analyst"],
        description="Demo standard position for Match Quality P1 acceptance.",
        status="active",
    )
    session.add(position)
    await session.flush()
    return position


def job_payload(recruiter_id: int, position_id: int, *, city: str, title: str, tags: list[str]) -> Job:
    return Job(
        recruiter_id=recruiter_id,
        standard_position_id=position_id,
        title=title,
        city=city,
        salary_min=20,
        salary_max=35,
        experience="3 years",
        education="Bachelor",
        description="Deterministic RP401 demo job.",
        requirement="Python SQL PeopleSoft HCM delivery experience.",
        benefits="Demo benefits",
        tags=tags,
        status="active",
        published_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )


async def seed() -> dict:
    assert_demo_environment()
    async with AsyncSessionLocal() as session:
        await cleanup_previous_demo(session)
        admin = await get_or_create_user(
            session,
            phone=ADMIN_PHONE,
            role="admin",
            display_name="RP401 Demo Admin",
            password=ADMIN_PASSWORD,
        )
        recruiter = await get_or_create_user(
            session,
            phone=RECRUITER_PHONE,
            role="recruiter",
            display_name="RP401 Demo Recruiter",
            password=RECRUITER_PASSWORD,
        )
        position = await get_or_create_position(session)
        rule_config = await MatchService._ensure_default_rule_config(session)

        risk_job = job_payload(
            recruiter.id,
            position.id,
            city=CITY_RISK,
            title="RP401 Risk Segment Engineer",
            tags=["RP401-Risk", "PeopleSoft", "Backend"],
        )
        healthy_job = job_payload(
            recruiter.id,
            position.id,
            city=CITY_HEALTHY,
            title="RP401 Healthy Segment Engineer",
            tags=["RP401-Healthy", "Python", "Backend"],
        )
        session.add_all([risk_job, healthy_job])
        await session.flush()

        experiment = MatchRuleExperimentModel(
            name="RP401 Demo Experiment",
            description="Treatment is intentionally better for Match Quality P1 demo.",
            scope=rule_config.scope,
            template_key=rule_config.template_key,
            status="running",
            traffic_percent=50,
            control_config_id=rule_config.id,
            treatment_config_id=rule_config.id,
            audience={"demo": SOURCE},
            started_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        session.add(experiment)
        await session.flush()

        seeker_hash = hash_password(SEEKER_PASSWORD)
        seekers: list[User] = []
        for index in range(240):
            phone = f"138401{index:05d}"
            seekers.append(
                User(
                    phone_hash=hash_phone(phone),
                    phone_encrypted=encryptor.encrypt(phone),
                    password_hash=seeker_hash,
                    display_name=f"RP401 Demo Seeker {index:03d}",
                    role="seeker",
                    status="active",
                )
            )
        session.add_all(seekers)
        await session.flush()

        audits: list[MatchRuleMatchAuditModel] = []
        behaviors: list[object] = []
        for index, seeker in enumerate(seekers):
            is_risk = index < 120
            job = risk_job if is_risk else healthy_job
            bucket = "control" if is_risk else "treatment"
            level = "low" if is_risk and index < 40 else "high"
            score = 86 if is_risk else 82
            audits.append(
                MatchRuleMatchAuditModel(
                    job_id=job.id,
                    seeker_id=seeker.id,
                    rule_config_id=rule_config.id,
                    experiment_id=experiment.id,
                    experiment_bucket=bucket,
                    scope=rule_config.scope,
                    template_key=rule_config.template_key,
                    source=SOURCE,
                    overall_score=score,
                    level=level,
                    recommendation="demo",
                    dimension_scores=[
                        {"key": "skill", "score": 92 if is_risk else 84},
                        {"key": "city", "score": 80},
                        {"key": "salary", "score": 80},
                    ],
                )
            )
            if not is_risk:
                behaviors.extend(
                    [
                        JobVisit(job_id=job.id, recruiter_id=recruiter.id, seeker_id=seeker.id, source=SOURCE),
                        JobFavorite(job_id=job.id, seeker_id=seeker.id),
                        JobApplication(
                            job_id=job.id,
                            seeker_id=seeker.id,
                            recruiter_id=recruiter.id,
                            cover_message="RP401 deterministic demo application",
                        ),
                    ]
                )
        session.add_all(audits + behaviors)
        await session.commit()

        result = {
            "seeded_at": datetime.now(timezone.utc).isoformat(),
            "demo_boundary": RP401_DEMO_BOUNDARY,
            "admin": {"phone": ADMIN_PHONE, "password": ADMIN_PASSWORD},
            "recruiter": {"phone": RECRUITER_PHONE, "password": RECRUITER_PASSWORD},
            "seeker_password": SEEKER_PASSWORD,
            "rule_config_id": rule_config.id,
            "experiment_id": experiment.id,
            "position_category": CATEGORY,
            "standard_position_id": position.id,
            "risk_city": CITY_RISK,
            "healthy_city": CITY_HEALTHY,
            "risk_job_id": risk_job.id,
            "healthy_job_id": healthy_job.id,
            "match_count": len(audits),
            "expected": {
                "risk_city_application_rate": 0,
                "healthy_city_application_rate": 100,
                "experiment_confidence": "treatment_likely_better",
                "minimum_anomalies": 2,
                "minimum_suggestions": 1,
            },
        }
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        return result


if __name__ == "__main__":
    print(json.dumps(asyncio.run(seed()), ensure_ascii=False, indent=2))
