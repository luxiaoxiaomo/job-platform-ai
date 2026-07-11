from sqlalchemy import select
from sqlalchemy.orm import selectinload

from tests.test_api.test_company_certifications import create_admin_token, register_and_get_token

from app.modules.match.models import (
    INTELLIGENT_DECISION_STATUSES,
    INTELLIGENT_EVALUATION_STATUSES,
    INTELLIGENT_STRATEGY_STATUSES,
    IntelligentMatchingEvaluationModel,
    IntelligentMatchingStrategyModel,
    MatchRuleConfigModel,
    MatchRuleOperationAuditModel,
)


def _rule_config() -> MatchRuleConfigModel:
    return MatchRuleConfigModel(
        name="P4 baseline rule",
        strategy="rule_v1",
        scope="global",
        template_key="default",
        template_name="Default template",
        status="active",
        version=100,
        description="Baseline rule for intelligent strategy tests",
    )


async def test_intelligent_strategy_model_defaults_and_json_persistence(db_session):
    rule_config = _rule_config()
    db_session.add(rule_config)
    await db_session.flush()

    strategy = IntelligentMatchingStrategyModel(
        name="hybrid-default-v1",
        description="P4 MVP strategy",
        base_rule_config_id=rule_config.id,
    )
    db_session.add(strategy)
    await db_session.commit()

    result = await db_session.execute(
        select(IntelligentMatchingStrategyModel).where(IntelligentMatchingStrategyModel.name == "hybrid-default-v1")
    )
    saved = result.scalar_one()

    assert "draft" in INTELLIGENT_STRATEGY_STATUSES
    assert "evaluating" in INTELLIGENT_STRATEGY_STATUSES
    assert "testing" in INTELLIGENT_STRATEGY_STATUSES
    assert "active" in INTELLIGENT_STRATEGY_STATUSES
    assert "archived" in INTELLIGENT_STRATEGY_STATUSES
    assert saved.status == "draft"
    assert saved.fallback_policy == "rule_baseline"
    assert saved.base_rule_config_id == rule_config.id
    assert saved.vector_recall == {
        "enabled": False,
        "top_n": 100,
        "min_similarity": 0.62,
        "candidate_source": "job_resume_profile",
    }
    assert saved.hybrid_weights == {
        "rule_score": 0.7,
        "vector_score": 0.2,
        "profile_coverage_score": 0.1,
        "behavior_quality_score": 0,
    }
    assert saved.archived_at is None


async def test_intelligent_evaluation_model_persists_summary_fields(db_session):
    rule_config = _rule_config()
    db_session.add(rule_config)
    await db_session.flush()

    strategy = IntelligentMatchingStrategyModel(
        name="hybrid-eval-v1",
        base_rule_config_id=rule_config.id,
        status="evaluating",
        vector_recall={"enabled": True, "top_n": 120, "min_similarity": 0.7, "candidate_source": "job_resume_profile"},
        hybrid_weights={
            "rule_score": 0.65,
            "vector_score": 0.25,
            "profile_coverage_score": 0.1,
            "behavior_quality_score": 0,
        },
    )
    db_session.add(strategy)
    await db_session.flush()

    evaluation = IntelligentMatchingEvaluationModel(
        strategy_id=strategy.id,
        status="completed",
        sample_count=240,
        sample_source_distribution={
            "real_behavior": 180,
            "manual_review": 60,
            "seeded_demo": 0,
            "mock_only": 0,
        },
        baseline_metrics={"avg_score": 76.5, "low_score_rate": 0.18},
        hybrid_metrics={"avg_score": 79.2, "degrade_rate": 0.03},
        decision_status="eligible_for_gray",
        risk_notes=["monitor application proxy rate"],
    )
    db_session.add(evaluation)
    await db_session.commit()

    result = await db_session.execute(
        select(IntelligentMatchingStrategyModel)
        .options(selectinload(IntelligentMatchingStrategyModel.evaluations))
        .where(IntelligentMatchingStrategyModel.id == strategy.id)
    )
    saved_strategy = result.scalar_one()
    saved_evaluation = saved_strategy.evaluations[0]

    assert "completed" in INTELLIGENT_EVALUATION_STATUSES
    assert "eligible_for_gray" in INTELLIGENT_DECISION_STATUSES
    assert saved_evaluation.status == "completed"
    assert saved_evaluation.sample_count == 240
    assert saved_evaluation.sample_source_distribution["real_behavior"] == 180
    assert saved_evaluation.baseline_metrics["avg_score"] == 76.5
    assert saved_evaluation.hybrid_metrics["degrade_rate"] == 0.03
    assert saved_evaluation.decision_status == "eligible_for_gray"
    assert saved_evaluation.risk_notes == ["monitor application proxy rate"]

def _strategy_payload(base_rule_config_id: int, *, name: str = "hybrid-api-v1") -> dict:
    return {
        "name": name,
        "description": "API strategy",
        "base_rule_config_id": base_rule_config_id,
        "vector_recall": {
            "enabled": True,
            "top_n": 100,
            "min_similarity": 0.62,
            "candidate_source": "job_resume_profile",
        },
        "hybrid_weights": {
            "rule_score": 0.7,
            "vector_score": 0.2,
            "profile_coverage_score": 0.1,
            "behavior_quality_score": 0,
        },
        "fallback_policy": "rule_baseline",
    }


async def _persist_rule_config(db_session, *, version: int = 200) -> MatchRuleConfigModel:
    rule_config = MatchRuleConfigModel(
        name=f"P4 API baseline rule {version}",
        strategy="rule_v1",
        scope="global",
        template_key="default",
        template_name="Default template",
        status="active",
        version=version,
        description="Baseline rule for intelligent strategy API tests",
    )
    db_session.add(rule_config)
    await db_session.commit()
    return rule_config


async def test_admin_can_create_list_update_clone_strategy_and_write_audits(client, db_session):
    admin_token = await create_admin_token(client, db_session)
    rule_config = await _persist_rule_config(db_session)

    create_response = await client.post(
        "/api/v1/matches/intelligent/strategies",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=_strategy_payload(rule_config.id),
    )
    assert create_response.status_code == 200
    created = create_response.json()
    assert created["status"] == "draft"
    assert created["fallback_policy"] == "rule_baseline"
    assert created["base_rule_config_id"] == rule_config.id

    list_response = await client.get(
        "/api/v1/matches/intelligent/strategies",
        headers={"Authorization": f"Bearer {admin_token}"},
        params={"status": "draft"},
    )
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1

    detail_response = await client.get(
        f"/api/v1/matches/intelligent/strategies/{created['id']}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["name"] == "hybrid-api-v1"
    assert detail["base_rule_config_id"] == rule_config.id
    assert detail["vector_recall"]["enabled"] is True
    assert detail["hybrid_weights"]["rule_score"] == 0.7
    assert "base_rule" not in detail
    assert "evaluations" not in detail
    assert "experiments" not in detail
    assert "operation_audits" not in detail

    update_response = await client.patch(
        f"/api/v1/matches/intelligent/strategies/{created['id']}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "description": "Updated API strategy",
            "vector_recall": {
                "enabled": True,
                "top_n": 80,
                "min_similarity": 0.7,
                "candidate_source": "job_resume_profile",
            },
            "hybrid_weights": {
                "rule_score": 0.65,
                "vector_score": 0.25,
                "profile_coverage_score": 0.1,
                "behavior_quality_score": 0,
            },
        },
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["description"] == "Updated API strategy"
    assert updated["vector_recall"]["top_n"] == 80
    assert updated["hybrid_weights"]["vector_score"] == 0.25

    clone_response = await client.post(
        f"/api/v1/matches/intelligent/strategies/{created['id']}/clone",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "hybrid-api-v2", "reason": "adjust weights"},
    )
    assert clone_response.status_code == 200
    cloned = clone_response.json()
    assert cloned["id"] != created["id"]
    assert cloned["status"] == "draft"
    assert cloned["name"] == "hybrid-api-v2"

    audit_result = await db_session.execute(
        select(MatchRuleOperationAuditModel)
        .where(MatchRuleOperationAuditModel.resource_type == "intelligent_strategy")
        .order_by(MatchRuleOperationAuditModel.id.asc())
    )
    actions = [item.action for item in audit_result.scalars().all()]
    assert actions == [
        "create_intelligent_strategy",
        "update_intelligent_strategy",
        "clone_intelligent_strategy",
    ]


async def test_intelligent_strategy_api_rejects_non_admin_users(client, db_session, test_user_data, test_recruiter_data):
    rule_config = await _persist_rule_config(db_session, version=201)
    seeker_token = await register_and_get_token(client, test_user_data)
    recruiter_token = await register_and_get_token(client, test_recruiter_data)

    for token in (seeker_token, recruiter_token):
        response = await client.post(
            "/api/v1/matches/intelligent/strategies",
            headers={"Authorization": f"Bearer {token}"},
            json=_strategy_payload(rule_config.id, name=f"blocked-{token[:6]}"),
        )
        assert response.status_code == 403


async def test_intelligent_strategy_api_validation_errors(client, db_session):
    admin_token = await create_admin_token(client, db_session)
    rule_config = await _persist_rule_config(db_session, version=202)

    invalid_weights = _strategy_payload(rule_config.id, name="invalid-weights")
    invalid_weights["hybrid_weights"] = {
        "rule_score": 0.5,
        "vector_score": 0.2,
        "profile_coverage_score": 0.1,
        "behavior_quality_score": 0,
    }
    response = await client.post(
        "/api/v1/matches/intelligent/strategies",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=invalid_weights,
    )
    assert response.status_code == 422

    missing_base_rule = _strategy_payload(999999, name="missing-base-rule")
    response = await client.post(
        "/api/v1/matches/intelligent/strategies",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=missing_base_rule,
    )
    assert response.status_code == 404

    create_response = await client.post(
        "/api/v1/matches/intelligent/strategies",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=_strategy_payload(rule_config.id, name="duplicate-name"),
    )
    assert create_response.status_code == 200
    duplicate_response = await client.post(
        "/api/v1/matches/intelligent/strategies",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=_strategy_payload(rule_config.id, name="duplicate-name"),
    )
    assert duplicate_response.status_code == 400

    invalid_fallback = _strategy_payload(rule_config.id, name="invalid-fallback")
    invalid_fallback["fallback_policy"] = "llm_only"
    response = await client.post(
        "/api/v1/matches/intelligent/strategies",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=invalid_fallback,
    )
    assert response.status_code == 422


async def test_intelligent_strategy_api_rejects_archived_base_rule_on_create_and_update(client, db_session):
    admin_token = await create_admin_token(client, db_session)
    active_rule = await _persist_rule_config(db_session, version=206)
    archived_rule = await _persist_rule_config(db_session, version=207)
    archived_rule.status = "archived"
    await db_session.commit()

    create_response = await client.post(
        "/api/v1/matches/intelligent/strategies",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=_strategy_payload(archived_rule.id, name="archived-base-create"),
    )
    assert create_response.status_code == 409
    assert create_response.json()["detail"] == "base_rule_config_archived"

    valid_response = await client.post(
        "/api/v1/matches/intelligent/strategies",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=_strategy_payload(active_rule.id, name="archived-base-update"),
    )
    assert valid_response.status_code == 200

    update_response = await client.patch(
        f"/api/v1/matches/intelligent/strategies/{valid_response.json()['id']}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"base_rule_config_id": archived_rule.id},
    )
    assert update_response.status_code == 409
    assert update_response.json()["detail"] == "base_rule_config_archived"


async def test_intelligent_strategy_api_rejects_in_place_edit_for_testing_strategy(client, db_session):
    admin_token = await create_admin_token(client, db_session)
    rule_config = await _persist_rule_config(db_session, version=203)
    strategy = IntelligentMatchingStrategyModel(
        name="testing-strategy",
        status="testing",
        base_rule_config_id=rule_config.id,
    )
    db_session.add(strategy)
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/matches/intelligent/strategies/{strategy.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"description": "should fail"},
    )
    assert response.status_code == 409

async def test_admin_can_run_and_get_intelligent_evaluation_report_and_write_audit(client, db_session):
    admin_token = await create_admin_token(client, db_session)
    rule_config = await _persist_rule_config(db_session, version=204)
    strategy = IntelligentMatchingStrategyModel(
        name="evaluation-ready-strategy",
        status="evaluating",
        base_rule_config_id=rule_config.id,
    )
    db_session.add(strategy)
    await db_session.commit()

    run_response = await client.post(
        f"/api/v1/matches/intelligent/strategies/{strategy.id}/evaluations",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "sample_set_id": 10,
            "sample_source_policy": "allow_real_and_manual_only",
            "sample_source_distribution": {
                "real_behavior": 180,
                "manual_review": 60,
                "seeded_demo": 0,
                "mock_only": 0,
            },
            "notes": "P4 MVP baseline comparison",
        },
    )
    assert run_response.status_code == 200
    created = run_response.json()
    assert created["status"] == "completed"
    assert created["sample_count"] == 240
    assert created["sample_source_distribution"]["real_behavior"] == 180
    assert created["baseline"]["avg_score"] == 76.5
    assert created["baseline"]["low_score_rate"] == 0.18
    assert created["hybrid"]["avg_score"] == 79.2
    assert created["hybrid"]["vector_recall_coverage"] == 0.84
    assert created["hybrid"]["degrade_rate"] == 0.03
    assert created["decision_status"] == "eligible_for_gray"
    assert created["risk_notes"] == []

    detail_response = await client.get(
        f"/api/v1/matches/intelligent/evaluations/{created['evaluation_id']}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail == created

    audit_result = await db_session.execute(
        select(MatchRuleOperationAuditModel)
        .where(MatchRuleOperationAuditModel.resource_type == "intelligent_evaluation")
        .order_by(MatchRuleOperationAuditModel.id.asc())
    )
    audit = audit_result.scalar_one()
    assert audit.action == "run_intelligent_evaluation"
    assert audit.resource_id == created["evaluation_id"]
    assert audit.metadata_json["strategy_id"] == strategy.id
    assert audit.metadata_json["sample_set_id"] == 10
    assert audit.after_snapshot["decision_status"] == "eligible_for_gray"


async def test_intelligent_evaluation_demo_or_mock_samples_cannot_produce_online_decision(client, db_session):
    admin_token = await create_admin_token(client, db_session)
    rule_config = await _persist_rule_config(db_session, version=205)
    strategy = IntelligentMatchingStrategyModel(
        name="demo-evaluation-strategy",
        status="evaluating",
        base_rule_config_id=rule_config.id,
    )
    db_session.add(strategy)
    await db_session.commit()

    response = await client.post(
        f"/api/v1/matches/intelligent/strategies/{strategy.id}/evaluations",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "sample_set_id": 11,
            "sample_source_policy": "allow_real_and_manual_only",
            "sample_source_distribution": {
                "real_behavior": 0,
                "manual_review": 0,
                "seeded_demo": 12,
                "mock_only": 8,
            },
            "notes": "demo-only dry run",
        },
    )
    assert response.status_code == 200
    created = response.json()
    assert created["sample_count"] == 20
    assert created["decision_status"] == "demo_only"
    assert "demo_or_mock_samples_cannot_support_online_decision" in created["risk_notes"]
