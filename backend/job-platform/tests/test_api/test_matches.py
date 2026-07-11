"""
Rule-based job match API tests.
"""
from httpx import AsyncClient

from app.modules.application.models import JobApplication
from app.modules.base_data.models import StandardPosition
from app.modules.job.models import Job
from app.modules.match.config import MatchRuleConfigService
from app.modules.match.models import IntelligentMatchingStrategyModel, MatchRuleConfigModel, MatchRuleDimensionModel, MatchRuleExperimentModel, MatchRuleMatchAuditModel
from app.modules.match.service import MatchService
from app.modules.user.models import User
from tests.test_api.test_company_certifications import create_admin_token, register_and_get_token
from tests.test_api.test_jobs import approve_current_recruiter_certification
from tests.test_api.test_resumes import _build_docx_bytes


def people_soft_job_payload() -> dict:
    return {
        "title": "PeopleSoft 技术顾问",
        "city": "上海",
        "salary_min": 18,
        "salary_max": 28,
        "experience": "3年以上",
        "education": "本科",
        "description": "负责人力资源系统实施、二次开发和上线支持。",
        "requirement": "熟悉 PeopleSoft HCM、Oracle、SQL，有企业级项目交付经验。",
        "benefits": "五险一金、双休",
        "tags": ["PeopleSoft", "HCM", "Oracle", "SQL"],
    }


async def create_active_people_soft_job(
    client: AsyncClient,
    db_session,
    recruiter_data: dict,
) -> int:
    recruiter_token = await register_and_get_token(client, recruiter_data)
    admin_token = await approve_current_recruiter_certification(client, db_session, recruiter_token)
    create_response = await client.post(
        "/api/v1/jobs/me",
        json=people_soft_job_payload(),
        headers={"Authorization": f"Bearer {recruiter_token}"},
    )
    job_id = create_response.json()["id"]
    await client.post(
        f"/api/v1/jobs/admin/{job_id}/review",
        json={"action": "approve"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    return job_id


async def create_confirmed_resume_profile(
    client: AsyncClient,
    token: str,
    *,
    tag_ids: list[int] | None = None,
    return_profile: bool = False,
):
    upload_response = await client.post(
        "/api/v1/resumes/me/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={
            "file": (
                "resume.docx",
                _build_docx_bytes("姓名：曾振宇\nPeopleSoft HCM SQL\n本科\n4年经验\n上海\n期望薪资20-25K"),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert upload_response.status_code == 200
    parse_run_id = upload_response.json()["parse_run"]["id"]

    structured_json = {
        "basic": {
            "name": "曾振宇",
            "gender": "男",
            "highest_education": "本科",
            "work_years": 4,
            "current_city": "上海",
            "target_position": "PeopleSoft 技术顾问",
            "expected_salary": "20-25K",
            "confidence_score": 0.95,
        },
        "skills": [
            {"skill_name": "PeopleSoft", "confidence_score": 0.95},
            {"skill_name": "HCM", "confidence_score": 0.9},
            {"skill_name": "SQL", "confidence_score": 0.9},
        ],
    }
    confirm_response = await client.put(
        "/api/v1/resumes/me/structured/confirm",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "parse_run_id": parse_run_id,
            "structured_json": structured_json,
            "tag_ids": tag_ids,
            "min_confidence": 0,
        },
    )
    assert confirm_response.status_code == 200
    if return_profile:
        return confirm_response.json()["profile"]
    return parse_run_id


async def login_default_admin_token(client: AsyncClient) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={"phone": "13700137001", "password": "Admin1234"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


async def seed_quality_insight_sample(db_session, *, experiment: bool = False) -> dict:
    rule_config = await MatchService._ensure_default_rule_config(db_session)
    standard_position = StandardPosition(
        name="Quality Insight Engineer",
        category="Tech",
        status="active",
    )
    control_job = Job(
        recruiter_id=1,
        title="Backend Engineer",
        city="Shanghai",
        salary_min=20,
        salary_max=30,
        experience="3 years",
        education="Bachelor",
        description="Backend platform",
        requirement="Python SQL",
        benefits="standard",
        tags=["PeopleSoft", "Backend"],
        status="active",
        standard_position=standard_position,
    )
    treatment_job = Job(
        recruiter_id=1,
        title="Product Engineer",
        city="Beijing",
        salary_min=18,
        salary_max=28,
        experience="3 years",
        education="Bachelor",
        description="Product platform",
        requirement="Python Product",
        benefits="standard",
        tags=["Product"],
        status="active",
        standard_position=standard_position,
    )
    db_session.add_all([control_job, treatment_job])
    await db_session.flush()

    experiment_model = None
    if experiment:
        experiment_model = MatchRuleExperimentModel(
            name="Quality insight experiment",
            description="Treatment should be better by application rate",
            scope=rule_config.scope,
            template_key=rule_config.template_key,
            status="running",
            traffic_percent=50,
            control_config_id=rule_config.id,
            treatment_config_id=rule_config.id,
            audience={},
        )
        db_session.add(experiment_model)
        await db_session.flush()

    users = [
        User(
            phone_hash=f"quality_hash_{index}",
            phone_encrypted=f"quality_phone_{index}",
            password_hash="x",
            display_name=f"Quality User {index}",
            role="seeker",
            status="active",
        )
        for index in range(240)
    ]
    db_session.add_all(users)
    await db_session.flush()

    audits = []
    applications = []
    for index, user in enumerate(users):
        is_control = index < 120
        job = control_job if is_control else treatment_job
        bucket = "control" if is_control else "treatment"
        level = "high" if is_control else "medium"
        if is_control and index < 40:
            level = "low"
        audits.append(
            MatchRuleMatchAuditModel(
                job_id=job.id,
                seeker_id=user.id,
                rule_config_id=rule_config.id,
                experiment_id=experiment_model.id if experiment_model else None,
                experiment_bucket=bucket if experiment_model else None,
                scope=rule_config.scope,
                template_key=rule_config.template_key,
                source="quality_insight_test",
                overall_score=88 if is_control else 72,
                level=level,
                recommendation="test",
                dimension_scores=[{"key": "skill", "score": 90 if is_control else 70}],
            )
        )
        if not is_control:
            applications.append(
                JobApplication(
                    job_id=job.id,
                    seeker_id=user.id,
                    recruiter_id=1,
                    cover_message="interested",
                )
            )
    db_session.add_all(audits + applications)
    await db_session.commit()
    return {
        "rule_config_id": rule_config.id,
        "experiment_id": experiment_model.id if experiment_model else None,
        "control_job_id": control_job.id,
        "treatment_job_id": treatment_job.id,
        "standard_position_id": standard_position.id,
    }


async def create_testing_rule_version(
    client: AsyncClient,
    admin_token: str,
    source_config: dict,
    *,
    name: str = "R-P3-09 testing rule",
) -> dict:
    response = await client.post(
        f"/api/v1/matches/rule-configs/{source_config['id']}/versions",
        json={
            "name": name,
            "description": "Testing rule version for release governance",
            "status": "testing",
            "scope": source_config["scope"],
            "template_key": source_config["template_key"],
            "template_name": source_config["template_name"],
            "dimensions": [
                {
                    "key": item["key"],
                    "label": item["label"],
                    "weight": 42 if item["key"] == "skill" else item["configured_weight"],
                    "enabled": item["enabled"],
                    "description": item["description"],
                    "scoring_method": item["scoring_method"],
                    "logic": item["logic"],
                    "sort_order": item["sort_order"],
                }
                for item in source_config["dimensions"]
            ],
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    return response.json()["config"]


class TestMatches:
    async def test_seeker_can_get_default_rule_config(
        self,
        client: AsyncClient,
        test_user_data,
    ):
        seeker_token = await register_and_get_token(client, test_user_data)

        response = await client.get(
            "/api/v1/matches/rule-configs/default",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"]
        assert data["scope"] == "global"
        assert data["status"] == "active"
        assert data["configured_total_weight"] == 100
        assert data["effective_total_weight"] == 100
        assert [item["key"] for item in data["dimensions"]] == [
            "skill",
            "experience",
            "education",
            "city",
            "salary",
            "intention",
        ]

    async def test_admin_can_list_and_get_rule_configs(
        self,
        client: AsyncClient,
        db_session,
    ):
        admin_token = await create_admin_token(client, db_session)

        list_response = await client.get(
            "/api/v1/matches/rule-configs",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert list_response.status_code == 200
        list_data = list_response.json()
        assert list_data["total"] >= 1
        assert list_data["skip"] == 0
        assert list_data["limit"] == 20
        first_rule = list_data["items"][0]
        assert first_rule["scope"] == "global"
        assert first_rule["status"] == "active"
        assert first_rule["dimensions"][0]["key"] == "skill"

        detail_response = await client.get(
            f"/api/v1/matches/rule-configs/{first_rule['id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert detail_response.status_code == 200
        assert detail_response.json()["id"] == first_rule["id"]

        history_response = await client.get(
            f"/api/v1/matches/rule-configs/{first_rule['id']}/history",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert history_response.status_code == 200
        assert history_response.json()["total"] >= 1

    async def test_seeker_cannot_list_rule_configs(
        self,
        client: AsyncClient,
        test_user_data,
    ):
        seeker_token = await register_and_get_token(client, test_user_data)

        response = await client.get(
            "/api/v1/matches/rule-configs",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )

        assert response.status_code == 403

    async def test_seeker_can_get_rule_based_job_match(
        self,
        client: AsyncClient,
        db_session,
        test_user_data,
        test_recruiter_data,
    ):
        job_id = await create_active_people_soft_job(client, db_session, test_recruiter_data)
        seeker_token = await register_and_get_token(client, test_user_data)
        parse_run_id = await create_confirmed_resume_profile(client, seeker_token)

        response = await client.get(
            f"/api/v1/matches/jobs/{job_id}/me",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["job"]["id"] == job_id
        assert data["overall_score"] >= 80
        assert data["level"] == "high"
        assert data["recommendation"] == "建议投递"
        assert data["weights"] == {
            "skill": 35,
            "experience": 20,
            "education": 15,
            "city": 10,
            "salary": 10,
            "intention": 10,
        }
        assert data["configured_weights"] == data["weights"]
        assert data["effective_weights"] == data["weights"]
        assert data["rule_config"]["scope"] == "global"
        assert data["rule_config"]["status"] == "active"
        skill_dimension = next(item for item in data["dimensions"] if item["key"] == "skill")
        assert skill_dimension["score"] >= 80
        assert skill_dimension["configured_weight"] == 35
        assert skill_dimension["effective_weight"] == 35
        assert skill_dimension["weighted_score"] == round(skill_dimension["score"] * 35 / 100, 2)
        assert skill_dimension["scoring_method"]
        assert "PeopleSoft" in " ".join(skill_dimension["matched"])
        assert data["overall_score"] == round(sum(item["weighted_score"] for item in data["dimensions"]))
        assert data["source"]["strategy"] == "rule_v1"
        assert data["source"]["profile_parse_run_id"] == parse_run_id

    async def test_active_intelligent_strategy_runs_hybrid_without_vector_dependency(
        self,
        client: AsyncClient,
        db_session,
        test_user_data,
        test_recruiter_data,
    ):
        job_id = await create_active_people_soft_job(client, db_session, test_recruiter_data)
        admin_token = await login_default_admin_token(client)
        seeker_token = await register_and_get_token(client, test_user_data)
        await create_confirmed_resume_profile(client, seeker_token)

        favorite_response = await client.post(
            f"/api/v1/jobs/seeker/favorites/{job_id}",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert favorite_response.status_code == 201

        list_response = await client.get(
            "/api/v1/matches/rule-configs",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        rule_config_id = list_response.json()["items"][0]["id"]
        strategy = IntelligentMatchingStrategyModel(
            name="runtime-hybrid-no-vector",
            status="active",
            base_rule_config_id=rule_config_id,
            vector_recall={
                "enabled": False,
                "top_n": 100,
                "min_similarity": 0.62,
                "candidate_source": "job_resume_profile",
            },
            hybrid_weights={
                "rule_score": 0.9,
                "vector_score": 0,
                "profile_coverage_score": 0.05,
                "behavior_quality_score": 0.05,
            },
        )
        db_session.add(strategy)
        await db_session.commit()

        match_response = await client.get(
            f"/api/v1/matches/jobs/{job_id}/me",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )

        assert match_response.status_code == 200
        match_data = match_response.json()
        assert match_data["source"]["strategy"] == "intelligent_hybrid_v1"
        assert match_data["source"]["intelligent_strategy_id"] == strategy.id
        assert match_data["source"]["match_source"] == "hybrid"
        assert match_data["source"]["recall_source"] == "rule_only"
        assert match_data["source"]["degrade_reason"] is None

        detail_response = await client.get(
            f"/api/v1/matches/audits/{match_data['source']['audit_id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert detail_response.status_code == 200
        intelligent_snapshot = next(
            item for item in detail_response.json()["dimension_scores"] if item["key"] == "intelligent_scoring"
        )
        assert intelligent_snapshot["score"] == match_data["overall_score"]
        assert intelligent_snapshot["match_source"] == "hybrid"
        assert intelligent_snapshot["score_components"]["profile_coverage_score"] == 100
        assert intelligent_snapshot["score_components"]["behavior_quality_score"] == 85

    async def test_active_intelligent_strategy_degrades_when_vector_is_unavailable(
        self,
        client: AsyncClient,
        db_session,
        test_user_data,
        test_recruiter_data,
    ):
        job_id = await create_active_people_soft_job(client, db_session, test_recruiter_data)
        admin_token = await login_default_admin_token(client)
        seeker_token = await register_and_get_token(client, test_user_data)
        await create_confirmed_resume_profile(client, seeker_token)

        list_response = await client.get(
            "/api/v1/matches/rule-configs",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        rule_config_id = list_response.json()["items"][0]["id"]
        strategy = IntelligentMatchingStrategyModel(
            name="runtime-hybrid-vector-unavailable",
            status="active",
            base_rule_config_id=rule_config_id,
            vector_recall={
                "enabled": True,
                "top_n": 100,
                "min_similarity": 0.62,
                "candidate_source": "job_resume_profile",
            },
            hybrid_weights={
                "rule_score": 0.7,
                "vector_score": 0.2,
                "profile_coverage_score": 0.1,
                "behavior_quality_score": 0,
            },
        )
        db_session.add(strategy)
        await db_session.commit()

        match_response = await client.get(
            f"/api/v1/matches/jobs/{job_id}/me",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )

        assert match_response.status_code == 200
        match_data = match_response.json()
        assert match_data["source"]["strategy"] == "intelligent_hybrid_v1"
        assert match_data["source"]["intelligent_strategy_id"] == strategy.id
        assert match_data["source"]["match_source"] == "rule_baseline"
        assert match_data["source"]["recall_source"] == "rule_only"
        assert match_data["source"]["degrade_reason"] == "vector_store_unavailable"

        detail_response = await client.get(
            f"/api/v1/matches/audits/{match_data['source']['audit_id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert detail_response.status_code == 200
        intelligent_snapshot = next(
            item for item in detail_response.json()["dimension_scores"] if item["key"] == "intelligent_scoring"
        )
        assert intelligent_snapshot["score"] == match_data["overall_score"]
        assert intelligent_snapshot["match_source"] == "rule_baseline"
        assert intelligent_snapshot["degrade_reason"] == "vector_store_unavailable"

    async def test_active_intelligent_strategy_uses_local_vector_provider(
        self,
        client: AsyncClient,
        db_session,
        test_user_data,
        test_recruiter_data,
    ):
        job_id = await create_active_people_soft_job(client, db_session, test_recruiter_data)
        admin_token = await login_default_admin_token(client)
        seeker_token = await register_and_get_token(client, test_user_data)
        await create_confirmed_resume_profile(client, seeker_token)

        list_response = await client.get(
            "/api/v1/matches/rule-configs",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        rule_config_id = list_response.json()["items"][0]["id"]
        strategy = IntelligentMatchingStrategyModel(
            name="runtime-hybrid-local-vector",
            status="active",
            base_rule_config_id=rule_config_id,
            vector_recall={
                "enabled": True,
                "provider": "local_profile_text",
                "top_n": 100,
                "min_similarity": 0.5,
                "candidate_source": "job_resume_profile",
            },
            hybrid_weights={
                "rule_score": 0.7,
                "vector_score": 0.2,
                "profile_coverage_score": 0.1,
                "behavior_quality_score": 0,
            },
        )
        db_session.add(strategy)
        await db_session.commit()

        match_response = await client.get(
            f"/api/v1/matches/jobs/{job_id}/me",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )

        assert match_response.status_code == 200
        match_data = match_response.json()
        assert match_data["source"]["strategy"] == "intelligent_hybrid_v1"
        assert match_data["source"]["intelligent_strategy_id"] == strategy.id
        assert match_data["source"]["match_source"] == "hybrid"
        assert match_data["source"]["recall_source"] == "rule_and_vector"
        assert match_data["source"]["degrade_reason"] is None

        detail_response = await client.get(
            f"/api/v1/matches/audits/{match_data['source']['audit_id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert detail_response.status_code == 200
        intelligent_snapshot = next(
            item for item in detail_response.json()["dimension_scores"] if item["key"] == "intelligent_scoring"
        )
        assert intelligent_snapshot["match_source"] == "hybrid"
        assert intelligent_snapshot["recall_source"] == "rule_and_vector"
        assert intelligent_snapshot["degrade_reason"] is None
        assert intelligent_snapshot["score_components"]["semantic_score"] is not None
        assert intelligent_snapshot["vector_metadata"]["provider"] == "local_profile_text"
        assert intelligent_snapshot["vector_metadata"]["vector_index_version"] == "local-profile-text-v1"

    async def test_recruiter_can_get_application_match(
        self,
        client: AsyncClient,
        db_session,
        test_user_data,
        test_recruiter_data,
    ):
        recruiter_token = await register_and_get_token(client, test_recruiter_data)
        admin_token = await approve_current_recruiter_certification(client, db_session, recruiter_token)
        create_response = await client.post(
            "/api/v1/jobs/me",
            json=people_soft_job_payload(),
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        job_id = create_response.json()["id"]
        await client.post(
            f"/api/v1/jobs/admin/{job_id}/review",
            json={"action": "approve"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        seeker_token = await register_and_get_token(client, test_user_data)
        parse_run_id = await create_confirmed_resume_profile(client, seeker_token)
        apply_response = await client.post(
            "/api/v1/applications",
            json={"job_id": job_id, "cover_message": "I would like to apply."},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert apply_response.status_code == 201
        application_id = apply_response.json()["id"]

        response = await client.get(
            f"/api/v1/matches/applications/{application_id}",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["job"]["id"] == job_id
        assert data["overall_score"] >= 80
        assert data["source"]["profile_parse_run_id"] == parse_run_id
        assert len(data["dimensions"]) >= 1

        profile_response = await client.get(
            f"/api/v1/resumes/recruiter/applications/{application_id}/structured-profile",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert profile_response.status_code == 200
        profile_data = profile_response.json()
        assert profile_data["profile"]["parse_run_id"] == parse_run_id
        assert profile_data["basic_info"]["work_years"] == 4
        assert any(item["skill_name"] == "PeopleSoft" for item in profile_data["skills"])

    async def test_match_rule_config_falls_back_when_db_config_invalid(
        self,
        db_session,
    ):
        invalid_config = MatchRuleConfigModel(
            name="Invalid config",
            strategy="rule_v1",
            scope="global",
            status="active",
            version=99,
            description="Invalid zero-weight config",
        )
        invalid_config.dimensions.append(
            MatchRuleDimensionModel(
                dimension_key="skill",
                label="技能匹配",
                weight=0,
                enabled=True,
                description="invalid",
                scoring_method="invalid",
                logic_json={},
                sort_order=1,
            )
        )
        db_session.add(invalid_config)
        await db_session.commit()

        config = await MatchService._get_active_rule_config(db_session)

        assert config.id == "default_rule_v1"
        assert config.configured_total_weight == 100

    async def test_rule_config_normalizes_enabled_dimension_weights(self):
        config = MatchRuleConfigService.build_config(
            [
                {"key": "skill", "label": "技能匹配", "weight": 35, "enabled": True},
                {"key": "city", "label": "城市匹配", "weight": 10, "enabled": False},
                {"key": "salary", "label": "薪资匹配", "weight": 10, "enabled": True},
            ]
        )

        assert config.configured_total_weight == 45
        assert config.effective_total_weight == 100
        assert config.effective_weights == {
            "skill": 77.78,
            "salary": 22.22,
        }
        city_dimension = next(item for item in config.dimensions if item.key == "city")
        assert city_dimension.effective_weight == 0

    async def test_match_response_allows_fractional_effective_weights(
        self,
        client: AsyncClient,
        db_session,
        test_user_data,
        test_recruiter_data,
    ):
        fractional_config = MatchRuleConfigModel(
            name="Fractional config",
            strategy="rule_v1",
            scope="global",
            status="active",
            version=98,
            description="Disable one dimension to force normalized fractional weights",
        )
        for index, item in enumerate(
            [
                ("skill", "技能匹配", 35, True),
                ("city", "城市匹配", 10, False),
                ("salary", "薪资匹配", 10, True),
            ],
            start=1,
        ):
            key, label, weight, enabled = item
            fractional_config.dimensions.append(
                MatchRuleDimensionModel(
                    dimension_key=key,
                    label=label,
                    weight=weight,
                    enabled=enabled,
                    description=label,
                    scoring_method=label,
                    logic_json={},
                    sort_order=index,
                )
            )
        db_session.add(fractional_config)
        await db_session.commit()

        job_id = await create_active_people_soft_job(client, db_session, test_recruiter_data)
        seeker_token = await register_and_get_token(client, test_user_data)
        await create_confirmed_resume_profile(client, seeker_token)

        response = await client.get(
            f"/api/v1/matches/jobs/{job_id}/me",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["weights"]["skill"] == 77.78
        skill_dimension = next(item for item in data["dimensions"] if item["key"] == "skill")
        assert skill_dimension["weight"] == 77.78

    async def test_admin_can_create_new_rule_config_version(
        self,
        client: AsyncClient,
        db_session,
    ):
        admin_token = await create_admin_token(client, db_session)
        list_response = await client.get(
            "/api/v1/matches/rule-configs",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert list_response.status_code == 200
        source_config = list_response.json()["items"][0]

        payload = {
            "name": "默认人岗匹配规则 V2",
            "description": "R-P3-05 编辑保存生成的新版本",
            "status": "active",
            "scope": source_config["scope"],
            "dimensions": [
                {
                    "key": item["key"],
                    "label": item["label"],
                    "weight": 40 if item["key"] == "skill" else 15 if item["key"] == "experience" else item["configured_weight"],
                    "enabled": False if item["key"] == "city" else item["enabled"],
                    "description": item["description"],
                    "scoring_method": item["scoring_method"],
                    "logic": item["logic"],
                    "sort_order": item["sort_order"],
                }
                for item in source_config["dimensions"]
            ],
        }

        create_response = await client.post(
            f"/api/v1/matches/rule-configs/{source_config['id']}/versions",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert create_response.status_code == 200
        data = create_response.json()["config"]
        assert data["name"] == payload["name"]
        assert data["version"] == source_config["version"] + 1
        assert data["parent_version_id"] == source_config["id"]
        assert data["status"] == "active"
        assert data["updated_by"] is not None
        city_dimension = next(item for item in data["dimensions"] if item["key"] == "city")
        assert city_dimension["enabled"] is False
        assert city_dimension["effective_weight"] == 0
        skill_dimension = next(item for item in data["dimensions"] if item["key"] == "skill")
        assert skill_dimension["configured_weight"] == 40

        latest_default_response = await client.get(
            "/api/v1/matches/rule-configs/default",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert latest_default_response.status_code == 200
        latest_default = latest_default_response.json()
        assert latest_default["id"] == data["id"]
        assert latest_default["version"] == data["version"]

        history_response = await client.get(
            f"/api/v1/matches/rule-configs/{data['id']}/history",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert history_response.status_code == 200
        assert history_response.json()["total"] >= 2

    async def test_admin_cannot_create_rule_version_with_duplicate_dimension_key(
        self,
        client: AsyncClient,
        db_session,
    ):
        admin_token = await create_admin_token(client, db_session)
        list_response = await client.get(
            "/api/v1/matches/rule-configs",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        source_config = list_response.json()["items"][0]
        first_dimension = source_config["dimensions"][0]

        payload = {
            "name": "重复维度测试",
            "description": "duplicate keys",
            "status": "draft",
            "scope": source_config["scope"],
            "dimensions": [
                {
                    "key": first_dimension["key"],
                    "label": first_dimension["label"],
                    "weight": first_dimension["configured_weight"],
                    "enabled": True,
                    "description": first_dimension["description"],
                    "scoring_method": first_dimension["scoring_method"],
                    "logic": first_dimension["logic"],
                    "sort_order": 1,
                },
                {
                    "key": first_dimension["key"],
                    "label": first_dimension["label"],
                    "weight": first_dimension["configured_weight"],
                    "enabled": True,
                    "description": first_dimension["description"],
                    "scoring_method": first_dimension["scoring_method"],
                    "logic": first_dimension["logic"],
                    "sort_order": 2,
                },
            ],
        }

        response = await client.post(
            f"/api/v1/matches/rule-configs/{source_config['id']}/versions",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "duplicate_dimension_key"

    async def test_admin_can_create_and_filter_rule_template(
        self,
        client: AsyncClient,
        db_session,
    ):
        admin_token = await create_admin_token(client, db_session)
        list_response = await client.get(
            "/api/v1/matches/rule-configs",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        source_config = list_response.json()["items"][0]

        payload = {
            "name": "Tech job rule template V1",
            "description": "Template for tech jobs",
            "template_key": "tech_jobs",
            "template_name": "Tech jobs",
            "status": "active",
            "scope": "job_category:tech",
            "dimensions": [
                {
                    "key": item["key"],
                    "label": item["label"],
                    "weight": 45 if item["key"] == "skill" else item["configured_weight"],
                    "enabled": item["enabled"],
                    "description": item["description"],
                    "scoring_method": item["scoring_method"],
                    "logic": item["logic"],
                    "sort_order": item["sort_order"],
                }
                for item in source_config["dimensions"]
            ],
        }

        create_response = await client.post(
            "/api/v1/matches/rule-configs/templates",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert create_response.status_code == 200
        created = create_response.json()["config"]
        assert created["template_key"] == "tech_jobs"
        assert created["template_name"] == "Tech jobs"
        assert created["scope"] == "job_category:tech"
        assert created["version"] == 1

        filter_response = await client.get(
            "/api/v1/matches/rule-configs?template_key=tech_jobs",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert filter_response.status_code == 200
        filtered = filter_response.json()
        assert filtered["total"] == 1
        assert filtered["items"][0]["id"] == created["id"]

    async def test_admin_can_compare_rule_versions(
        self,
        client: AsyncClient,
        db_session,
    ):
        admin_token = await create_admin_token(client, db_session)
        list_response = await client.get(
            "/api/v1/matches/rule-configs",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        source_config = list_response.json()["items"][0]
        payload = {
            "name": "Compare target V2",
            "description": "Changed weights for comparison",
            "status": "draft",
            "scope": source_config["scope"],
            "template_key": source_config["template_key"],
            "template_name": source_config["template_name"],
            "dimensions": [
                {
                    "key": item["key"],
                    "label": item["label"],
                    "weight": 40 if item["key"] == "skill" else item["configured_weight"],
                    "enabled": False if item["key"] == "city" else item["enabled"],
                    "description": item["description"],
                    "scoring_method": item["scoring_method"],
                    "logic": item["logic"],
                    "sort_order": item["sort_order"],
                }
                for item in source_config["dimensions"]
            ],
        }
        create_response = await client.post(
            f"/api/v1/matches/rule-configs/{source_config['id']}/versions",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        target_config = create_response.json()["config"]

        compare_response = await client.get(
            f"/api/v1/matches/rule-configs/{source_config['id']}/compare/{target_config['id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert compare_response.status_code == 200
        data = compare_response.json()
        assert data["base"]["id"] == source_config["id"]
        assert data["target"]["id"] == target_config["id"]
        assert data["summary"]["changed"] >= 2
        skill_diff = next(item for item in data["dimensions"] if item["key"] == "skill")
        assert skill_diff["change_type"] == "changed"
        assert skill_diff["base_weight"] == source_config["dimensions"][0]["configured_weight"]
        assert skill_diff["target_weight"] == 40
        assert skill_diff["weight_delta"] == 5
        city_diff = next(item for item in data["dimensions"] if item["key"] == "city")
        assert city_diff["enabled_changed"] is True

    async def test_admin_can_rollback_rule_version_by_creating_new_active_version(
        self,
        client: AsyncClient,
        db_session,
    ):
        admin_token = await create_admin_token(client, db_session)
        list_response = await client.get(
            "/api/v1/matches/rule-configs",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        source_config = list_response.json()["items"][0]
        payload = {
            "name": "Rollback source V2",
            "description": "Version to rollback from",
            "status": "active",
            "scope": source_config["scope"],
            "template_key": source_config["template_key"],
            "template_name": source_config["template_name"],
            "dimensions": [
                {
                    "key": item["key"],
                    "label": item["label"],
                    "weight": 40 if item["key"] == "skill" else item["configured_weight"],
                    "enabled": item["enabled"],
                    "description": item["description"],
                    "scoring_method": item["scoring_method"],
                    "logic": item["logic"],
                    "sort_order": item["sort_order"],
                }
                for item in source_config["dimensions"]
            ],
        }
        create_response = await client.post(
            f"/api/v1/matches/rule-configs/{source_config['id']}/versions",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        current_config = create_response.json()["config"]

        rollback_response = await client.post(
            f"/api/v1/matches/rule-configs/{current_config['id']}/rollback",
            json={"target_config_id": source_config["id"], "status": "active", "name": "Rollback to V1"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert rollback_response.status_code == 200
        rolled_back = rollback_response.json()["config"]
        assert rolled_back["name"] == "Rollback to V1"
        assert rolled_back["version"] == current_config["version"] + 1
        assert rolled_back["parent_version_id"] == current_config["id"]
        assert rolled_back["status"] == "active"
        skill_dimension = next(item for item in rolled_back["dimensions"] if item["key"] == "skill")
        source_skill = next(item for item in source_config["dimensions"] if item["key"] == "skill")
        assert skill_dimension["configured_weight"] == source_skill["configured_weight"]

        current_detail = await client.get(
            f"/api/v1/matches/rule-configs/{current_config['id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert current_detail.json()["status"] == "archived"

        latest_default_response = await client.get(
            "/api/v1/matches/rule-configs/default",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert latest_default_response.json()["id"] == rolled_back["id"]

    async def test_admin_can_create_rule_experiment_entry(
        self,
        client: AsyncClient,
        db_session,
    ):
        admin_token = await create_admin_token(client, db_session)
        list_response = await client.get(
            "/api/v1/matches/rule-configs",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        control_config = list_response.json()["items"][0]
        payload = {
            "name": "Rule AB test",
            "description": "Gray entry for rule experiment",
            "scope": control_config["scope"],
            "template_key": control_config["template_key"],
            "status": "draft",
            "traffic_percent": 25,
            "control_config_id": control_config["id"],
            "treatment_config_id": control_config["id"],
            "audience": {"city": "Shanghai"},
        }

        create_response = await client.post(
            "/api/v1/matches/rule-experiments",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert create_response.status_code == 200
        created = create_response.json()
        assert created["id"]
        assert created["template_key"] == control_config["template_key"]
        assert created["traffic_percent"] == 25
        assert created["audience"] == {"city": "Shanghai"}

        list_experiments_response = await client.get(
            "/api/v1/matches/rule-experiments",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert list_experiments_response.status_code == 200
        assert list_experiments_response.json()["total"] >= 1

    async def test_running_rule_experiment_routes_match_to_treatment_and_records_audit(
        self,
        client: AsyncClient,
        db_session,
        test_user_data,
        test_recruiter_data,
    ):
        job_id = await create_active_people_soft_job(client, db_session, test_recruiter_data)
        admin_token = await login_default_admin_token(client)
        seeker_token = await register_and_get_token(client, test_user_data)
        parse_run_id = await create_confirmed_resume_profile(client, seeker_token)

        list_response = await client.get(
            "/api/v1/matches/rule-configs",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        control_config = list_response.json()["items"][0]
        version_payload = {
            "name": "R-P3-07 treatment rule",
            "description": "Treatment rule for running experiment",
            "status": "testing",
            "scope": control_config["scope"],
            "template_key": control_config["template_key"],
            "template_name": control_config["template_name"],
            "dimensions": [
                {
                    "key": item["key"],
                    "label": item["label"],
                    "weight": 50 if item["key"] == "skill" else item["configured_weight"],
                    "enabled": item["enabled"],
                    "description": item["description"],
                    "scoring_method": item["scoring_method"],
                    "logic": item["logic"],
                    "sort_order": item["sort_order"],
                }
                for item in control_config["dimensions"]
            ],
        }
        version_response = await client.post(
            f"/api/v1/matches/rule-configs/{control_config['id']}/versions",
            json=version_payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        treatment_config = version_response.json()["config"]
        experiment_response = await client.post(
            "/api/v1/matches/rule-experiments",
            json={
                "name": "R-P3-07 treatment routing",
                "description": "100 percent treatment",
                "scope": control_config["scope"],
                "template_key": control_config["template_key"],
                "status": "running",
                "traffic_percent": 100,
                "control_config_id": control_config["id"],
                "treatment_config_id": treatment_config["id"],
                "audience": {},
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        experiment = experiment_response.json()

        match_response = await client.get(
            f"/api/v1/matches/jobs/{job_id}/me",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )

        assert match_response.status_code == 200
        match_data = match_response.json()
        assert match_data["rule_config"]["id"] == treatment_config["id"]
        assert match_data["source"]["rule_config_id"] == treatment_config["id"]
        assert match_data["source"]["experiment_id"] == experiment["id"]
        assert match_data["source"]["experiment_bucket"] == "treatment"
        assert match_data["source"]["audit_id"]
        assert match_data["source"]["profile_parse_run_id"] == parse_run_id

        audits_response = await client.get(
            f"/api/v1/matches/audits?experiment_id={experiment['id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert audits_response.status_code == 200
        audits = audits_response.json()
        assert audits["total"] == 1
        audit = audits["items"][0]
        assert audit["job_id"] == job_id
        assert audit["seeker_id"]
        assert audit["rule_config_id"] == treatment_config["id"]
        assert audit["experiment_id"] == experiment["id"]
        assert audit["experiment_bucket"] == "treatment"
        assert audit["overall_score"] == match_data["overall_score"]

        treatment_filter_response = await client.get(
            f"/api/v1/matches/audits?experiment_id={experiment['id']}&experiment_bucket=treatment",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert treatment_filter_response.status_code == 200
        assert treatment_filter_response.json()["total"] == 1

        control_filter_response = await client.get(
            f"/api/v1/matches/audits?experiment_id={experiment['id']}&experiment_bucket=control",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert control_filter_response.status_code == 200
        assert control_filter_response.json()["total"] == 0

        detail_response = await client.get(
            f"/api/v1/matches/audits/{audit['id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert detail_response.status_code == 200
        detail = detail_response.json()
        assert detail["id"] == audit["id"]
        assert detail["job"]["id"] == job_id
        assert detail["job"]["title"]
        assert detail["seeker"]["id"] == audit["seeker_id"]
        assert detail["rule_config"]["id"] == treatment_config["id"]
        assert detail["experiment"]["id"] == experiment["id"]
        skill_snapshot = next(item for item in detail["dimension_scores"] if item["key"] == "skill")
        assert skill_snapshot["label"]
        assert isinstance(skill_snapshot["matched"], list)
        assert isinstance(skill_snapshot["missing"], list)
        assert skill_snapshot["explanation"]

        effects_response = await client.get(
            f"/api/v1/matches/rule-experiments/{experiment['id']}/effects",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert effects_response.status_code == 200
        effects = effects_response.json()
        assert effects["experiment_id"] == experiment["id"]
        assert effects["buckets"]["treatment"]["match_count"] == 1
        assert effects["buckets"]["treatment"]["avg_score"] == match_data["overall_score"]
        assert effects["buckets"]["control"]["match_count"] == 0

    async def test_admin_can_filter_match_audits_by_seeker_rule_and_time_range(
        self,
        client: AsyncClient,
        db_session,
        test_user_data,
        test_recruiter_data,
    ):
        job_id = await create_active_people_soft_job(client, db_session, test_recruiter_data)
        admin_token = await login_default_admin_token(client)
        seeker_token = await register_and_get_token(client, test_user_data)
        await create_confirmed_resume_profile(client, seeker_token)

        match_response = await client.get(
            f"/api/v1/matches/jobs/{job_id}/me",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert match_response.status_code == 200
        match_data = match_response.json()
        audit_id = match_data["source"]["audit_id"]

        detail_response = await client.get(
            f"/api/v1/matches/audits/{audit_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert detail_response.status_code == 200
        detail = detail_response.json()

        filtered_response = await client.get(
            "/api/v1/matches/audits"
            f"?job_id={job_id}"
            f"&seeker_id={detail['seeker_id']}"
            f"&rule_config_id={detail['rule_config_id']}"
            "&created_from=2000-01-01T00:00:00"
            "&created_to=2999-01-01T00:00:00",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert filtered_response.status_code == 200
        filtered = filtered_response.json()
        assert filtered["total"] == 1
        assert filtered["items"][0]["id"] == audit_id
        assert filtered["items"][0]["job"]["id"] == job_id
        assert filtered["items"][0]["seeker"]["id"] == detail["seeker_id"]

        out_of_range_response = await client.get(
            "/api/v1/matches/audits?created_from=2999-01-01T00:00:00",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert out_of_range_response.status_code == 200
        assert out_of_range_response.json()["total"] == 0

    async def test_admin_can_get_match_quality_summary_by_rule_and_time_range(
        self,
        client: AsyncClient,
        db_session,
        test_user_data,
        test_recruiter_data,
    ):
        job_id = await create_active_people_soft_job(client, db_session, test_recruiter_data)
        admin_token = await login_default_admin_token(client)
        seeker_token = await register_and_get_token(client, test_user_data)
        await create_confirmed_resume_profile(client, seeker_token)

        visit_response = await client.get(
            f"/api/v1/jobs/public/{job_id}",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert visit_response.status_code == 200

        match_response = await client.get(
            f"/api/v1/matches/jobs/{job_id}/me",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert match_response.status_code == 200
        match_data = match_response.json()
        rule_config_id = match_data["source"]["rule_config_id"]

        favorite_response = await client.post(
            f"/api/v1/jobs/seeker/favorites/{job_id}",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert favorite_response.status_code == 201

        apply_response = await client.post(
            "/api/v1/applications",
            json={"job_id": job_id, "cover_message": "I would like to apply."},
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert apply_response.status_code == 201

        response = await client.get(
            "/api/v1/matches/quality/summary"
            f"?rule_config_id={rule_config_id}"
            "&created_from=2000-01-01T00:00:00"
            "&created_to=2999-01-01T00:00:00",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["filters"]["rule_config_id"] == rule_config_id
        assert data["summary"]["match_count"] == 1
        assert data["summary"]["avg_score"] == match_data["overall_score"]
        assert data["summary"]["high_count"] == 1
        assert data["summary"]["favorite_count"] == 1
        assert data["summary"]["application_count"] == 1
        assert data["summary"]["visit_count"] == 1
        assert data["summary"]["favorite_rate"] == 100
        assert data["summary"]["application_rate"] == 100
        assert data["summary"]["visit_rate"] == 100
        assert data["rule_versions"][0]["rule_config_id"] == rule_config_id
        assert data["rule_versions"][0]["match_count"] == 1
        assert data["rule_versions"][0]["application_count"] == 1
        assert data["time_buckets"][0]["date"]
        assert data["time_buckets"][0]["match_count"] == 1

        out_of_range_response = await client.get(
            "/api/v1/matches/quality/summary?created_from=2999-01-01T00:00:00",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert out_of_range_response.status_code == 200
        assert out_of_range_response.json()["summary"]["match_count"] == 0

    async def test_admin_can_get_match_quality_p1_segments_anomalies_and_suggestions(
        self,
        client: AsyncClient,
        db_session,
    ):
        admin_token = await create_admin_token(client, db_session)
        seeded = await seed_quality_insight_sample(db_session)

        response = await client.get(
            "/api/v1/matches/quality/summary"
            f"?rule_config_id={seeded['rule_config_id']}"
            "&segment_type=city"
            "&city=Shanghai",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["filters"]["city"] == "Shanghai"
        assert data["filters"]["segment_type"] == "city"
        assert data["summary"]["match_count"] == 120
        assert data["summary"]["sample_status"] == "usable"
        assert data["summary"]["low_score_rate"] == 33.33
        assert data["segments"][0]["segment_type"] == "city"
        assert data["segments"][0]["segment_key"] == "Shanghai"
        assert data["segments"][0]["sample_status"] == "usable"
        assert data["segments"][0]["risk_level"] in {"low", "medium", "high"}

        all_response = await client.get(
            f"/api/v1/matches/quality/summary?rule_config_id={seeded['rule_config_id']}&segment_type=city",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert all_response.status_code == 200
        all_data = all_response.json()
        shanghai = next(item for item in all_data["segments"] if item["segment_key"] == "Shanghai")
        assert shanghai["application_rate_delta"] == -50
        assert shanghai["risk_level"] == "high"
        assert any(item["type"] == "low_application_rate" for item in all_data["anomalies"])
        assert any(item["guardrail"].startswith("Draft suggestion only") for item in all_data["tuning_suggestions"])

    async def test_admin_can_get_match_quality_p1_experiment_confidence(
        self,
        client: AsyncClient,
        db_session,
    ):
        admin_token = await create_admin_token(client, db_session)
        seeded = await seed_quality_insight_sample(db_session, experiment=True)

        response = await client.get(
            f"/api/v1/matches/quality/summary?experiment_id={seeded['experiment_id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        confidence = data["experiment_confidence"]
        assert confidence["experiment_id"] == seeded["experiment_id"]
        assert confidence["control_match_count"] == 120
        assert confidence["treatment_match_count"] == 120
        assert confidence["sample_status"] == "usable"
        assert confidence["application_rate_delta"] == 100
        assert confidence["confidence_status"] == "treatment_likely_better"

    async def test_admin_can_get_match_quality_summary_by_experiment_bucket(
        self,
        client: AsyncClient,
        db_session,
        test_user_data,
        test_recruiter_data,
    ):
        job_id = await create_active_people_soft_job(client, db_session, test_recruiter_data)
        admin_token = await login_default_admin_token(client)
        seeker_token = await register_and_get_token(client, test_user_data)
        await create_confirmed_resume_profile(client, seeker_token)

        list_response = await client.get(
            "/api/v1/matches/rule-configs",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        control_config = list_response.json()["items"][0]
        treatment_config = await create_testing_rule_version(
            client,
            admin_token,
            control_config,
            name="R-P3-10 quality treatment rule",
        )
        experiment_response = await client.post(
            "/api/v1/matches/rule-experiments",
            json={
                "name": "R-P3-10 quality experiment",
                "description": "Quality dashboard bucket aggregation",
                "scope": control_config["scope"],
                "template_key": control_config["template_key"],
                "status": "running",
                "traffic_percent": 100,
                "control_config_id": control_config["id"],
                "treatment_config_id": treatment_config["id"],
                "audience": {},
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert experiment_response.status_code == 200
        experiment = experiment_response.json()

        match_response = await client.get(
            f"/api/v1/matches/jobs/{job_id}/me",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )
        assert match_response.status_code == 200
        match_data = match_response.json()
        assert match_data["source"]["experiment_bucket"] == "treatment"

        response = await client.get(
            f"/api/v1/matches/quality/summary?experiment_id={experiment['id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["filters"]["experiment_id"] == experiment["id"]
        assert data["summary"]["match_count"] == 1
        assert data["experiment_buckets"]["treatment"]["match_count"] == 1
        assert data["experiment_buckets"]["treatment"]["avg_score"] == match_data["overall_score"]
        assert data["experiment_buckets"]["control"]["match_count"] == 0

    async def test_running_rule_experiment_can_route_to_control_bucket(
        self,
        client: AsyncClient,
        db_session,
        test_user_data,
        test_recruiter_data,
    ):
        job_id = await create_active_people_soft_job(client, db_session, test_recruiter_data)
        admin_token = await login_default_admin_token(client)
        seeker_token = await register_and_get_token(client, test_user_data)
        await create_confirmed_resume_profile(client, seeker_token)

        list_response = await client.get(
            "/api/v1/matches/rule-configs",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        control_config = list_response.json()["items"][0]
        version_payload = {
            "name": "R-P3-07 control split treatment rule",
            "description": "Treatment rule not selected at zero traffic",
            "status": "testing",
            "scope": control_config["scope"],
            "template_key": control_config["template_key"],
            "template_name": control_config["template_name"],
            "dimensions": [
                {
                    "key": item["key"],
                    "label": item["label"],
                    "weight": 50 if item["key"] == "skill" else item["configured_weight"],
                    "enabled": item["enabled"],
                    "description": item["description"],
                    "scoring_method": item["scoring_method"],
                    "logic": item["logic"],
                    "sort_order": item["sort_order"],
                }
                for item in control_config["dimensions"]
            ],
        }
        version_response = await client.post(
            f"/api/v1/matches/rule-configs/{control_config['id']}/versions",
            json=version_payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        treatment_config = version_response.json()["config"]
        experiment_response = await client.post(
            "/api/v1/matches/rule-experiments",
            json={
                "name": "R-P3-07 control routing",
                "description": "0 percent treatment",
                "scope": control_config["scope"],
                "template_key": control_config["template_key"],
                "status": "running",
                "traffic_percent": 0,
                "control_config_id": control_config["id"],
                "treatment_config_id": treatment_config["id"],
                "audience": {},
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        experiment = experiment_response.json()

        match_response = await client.get(
            f"/api/v1/matches/jobs/{job_id}/me",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )

        assert match_response.status_code == 200
        match_data = match_response.json()
        assert match_data["rule_config"]["id"] == control_config["id"]
        assert match_data["source"]["rule_config_id"] == control_config["id"]
        assert match_data["source"]["experiment_id"] == experiment["id"]
        assert match_data["source"]["experiment_bucket"] == "control"

    async def test_admin_can_check_and_publish_testing_rule_config(
        self,
        client: AsyncClient,
        db_session,
    ):
        admin_token = await create_admin_token(client, db_session)
        list_response = await client.get(
            "/api/v1/matches/rule-configs",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        source_config = list_response.json()["items"][0]
        testing_config = await create_testing_rule_version(client, admin_token, source_config)

        check_response = await client.get(
            f"/api/v1/matches/rule-configs/{testing_config['id']}/release-check",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert check_response.status_code == 200
        release_check = check_response.json()
        assert release_check["rule_config_id"] == testing_config["id"]
        assert release_check["can_publish"] is True
        assert release_check["blockers"] == []
        assert release_check["current_active_config_id"] == source_config["id"]

        publish_response = await client.post(
            f"/api/v1/matches/rule-configs/{testing_config['id']}/publish",
            json={"reason": "R-P3-09 release acceptance", "confirm_warnings": True},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert publish_response.status_code == 200
        published = publish_response.json()["config"]
        assert published["id"] == testing_config["id"]
        assert published["status"] == "active"
        assert source_config["id"] in publish_response.json()["archived_config_ids"]

        old_config_response = await client.get(
            f"/api/v1/matches/rule-configs/{source_config['id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert old_config_response.json()["status"] == "archived"

        audits_response = await client.get(
            f"/api/v1/matches/rule-operation-audits?resource_id={testing_config['id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert audits_response.status_code == 200
        audits = audits_response.json()
        assert audits["total"] >= 1
        assert audits["items"][0]["action"] == "publish_rule"
        assert audits["items"][0]["resource_type"] == "rule_config"

    async def test_running_rule_experiment_blocks_rule_publish_and_records_audit(
        self,
        client: AsyncClient,
        db_session,
    ):
        admin_token = await create_admin_token(client, db_session)
        list_response = await client.get(
            "/api/v1/matches/rule-configs",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        control_config = list_response.json()["items"][0]
        testing_config = await create_testing_rule_version(
            client,
            admin_token,
            control_config,
            name="R-P3-09 blocked testing rule",
        )
        experiment_response = await client.post(
            "/api/v1/matches/rule-experiments",
            json={
                "name": "R-P3-09 publish blocker",
                "description": "Running experiment should block publish",
                "scope": control_config["scope"],
                "template_key": control_config["template_key"],
                "status": "running",
                "traffic_percent": 50,
                "control_config_id": control_config["id"],
                "treatment_config_id": testing_config["id"],
                "audience": {},
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert experiment_response.status_code == 200

        check_response = await client.get(
            f"/api/v1/matches/rule-configs/{testing_config['id']}/release-check",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert check_response.status_code == 200
        release_check = check_response.json()
        assert release_check["can_publish"] is False
        assert release_check["blockers"][0]["code"] == "running_experiment_conflict"

        publish_response = await client.post(
            f"/api/v1/matches/rule-configs/{testing_config['id']}/publish",
            json={"reason": "Should be blocked", "confirm_warnings": True},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert publish_response.status_code == 400
        assert publish_response.json()["detail"]["code"] == "match_rule_publish_blocked"

        audits_response = await client.get(
            f"/api/v1/matches/rule-operation-audits?resource_id={testing_config['id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert audits_response.status_code == 200
        assert audits_response.json()["items"][0]["action"] == "block_publish"

    async def test_admin_can_pause_resume_and_end_rule_experiment(
        self,
        client: AsyncClient,
        db_session,
    ):
        admin_token = await create_admin_token(client, db_session)
        list_response = await client.get(
            "/api/v1/matches/rule-configs",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        control_config = list_response.json()["items"][0]
        treatment_config = await create_testing_rule_version(
            client,
            admin_token,
            control_config,
            name="R-P3-09 experiment treatment rule",
        )
        experiment_response = await client.post(
            "/api/v1/matches/rule-experiments",
            json={
                "name": "R-P3-09 status workflow",
                "description": "Experiment status governance",
                "scope": control_config["scope"],
                "template_key": control_config["template_key"],
                "status": "running",
                "traffic_percent": 50,
                "control_config_id": control_config["id"],
                "treatment_config_id": treatment_config["id"],
                "audience": {},
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert experiment_response.status_code == 200
        experiment = experiment_response.json()

        pause_response = await client.post(
            f"/api/v1/matches/rule-experiments/{experiment['id']}/status",
            json={"status": "paused", "reason": "Pause before release"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert pause_response.status_code == 200
        assert pause_response.json()["experiment"]["status"] == "paused"

        resume_response = await client.post(
            f"/api/v1/matches/rule-experiments/{experiment['id']}/status",
            json={"status": "running", "reason": "Resume controlled experiment"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resume_response.status_code == 200
        assert resume_response.json()["experiment"]["status"] == "running"

        end_response = await client.post(
            f"/api/v1/matches/rule-experiments/{experiment['id']}/status",
            json={"status": "ended", "reason": "End experiment"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert end_response.status_code == 200
        assert end_response.json()["experiment"]["status"] == "ended"
        assert end_response.json()["experiment"]["ended_at"] is not None

        reopen_response = await client.post(
            f"/api/v1/matches/rule-experiments/{experiment['id']}/status",
            json={"status": "running", "reason": "Cannot reopen ended experiment"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert reopen_response.status_code == 400
        assert reopen_response.json()["detail"] == "experiment_already_ended"

        audits_response = await client.get(
            f"/api/v1/matches/rule-operation-audits?resource_id={experiment['id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        actions = [item["action"] for item in audits_response.json()["items"]]
        assert actions[:3] == ["end_experiment", "resume_experiment", "pause_experiment"]

    async def test_job_specific_rule_scope_is_selected_before_global_default(
        self,
        client: AsyncClient,
        db_session,
        test_user_data,
        test_recruiter_data,
    ):
        job_id = await create_active_people_soft_job(client, db_session, test_recruiter_data)
        admin_token = await login_default_admin_token(client)
        seeker_token = await register_and_get_token(client, test_user_data)
        await create_confirmed_resume_profile(client, seeker_token)

        list_response = await client.get(
            "/api/v1/matches/rule-configs",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        source_config = list_response.json()["items"][0]
        job_scope = f"job_id:{job_id}"
        template_response = await client.post(
            "/api/v1/matches/rule-configs/templates",
            json={
                "name": "R-P3-07 job scoped rule",
                "description": "Job-specific rule should win over global",
                "template_key": "default",
                "template_name": "Default template",
                "status": "active",
                "scope": job_scope,
                "dimensions": [
                    {
                        "key": item["key"],
                        "label": item["label"],
                        "weight": item["configured_weight"],
                        "enabled": False if item["key"] == "city" else item["enabled"],
                        "description": item["description"],
                        "scoring_method": item["scoring_method"],
                        "logic": item["logic"],
                        "sort_order": item["sort_order"],
                    }
                    for item in source_config["dimensions"]
                ],
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert template_response.status_code == 200
        scoped_config = template_response.json()["config"]

        match_response = await client.get(
            f"/api/v1/matches/jobs/{job_id}/me",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )

        assert match_response.status_code == 200
        match_data = match_response.json()
        assert match_data["rule_config"]["id"] == scoped_config["id"]
        assert match_data["rule_config"]["scope"] == job_scope
        assert match_data["source"]["rule_config_id"] == scoped_config["id"]
        assert match_data["source"]["experiment_id"] is None
        assert match_data["source"]["experiment_bucket"] is None

    async def test_match_requires_resume_profile(
        self,
        client: AsyncClient,
        db_session,
        test_user_data,
        test_recruiter_data,
    ):
        job_id = await create_active_people_soft_job(client, db_session, test_recruiter_data)
        seeker_token = await register_and_get_token(client, test_user_data)

        response = await client.get(
            f"/api/v1/matches/jobs/{job_id}/me",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )

        assert response.status_code == 422
        assert response.json()["detail"] == "profile_required"

    async def test_match_hides_inactive_jobs(
        self,
        client: AsyncClient,
        db_session,
        test_user_data,
        test_recruiter_data,
    ):
        recruiter_token = await register_and_get_token(client, test_recruiter_data)
        await approve_current_recruiter_certification(client, db_session, recruiter_token)
        create_response = await client.post(
            "/api/v1/jobs/me",
            json=people_soft_job_payload(),
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        seeker_token = await register_and_get_token(client, test_user_data)

        response = await client.get(
            f"/api/v1/matches/jobs/{create_response.json()['id']}/me",
            headers={"Authorization": f"Bearer {seeker_token}"},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "job_not_found"
