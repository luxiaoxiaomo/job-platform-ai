from types import SimpleNamespace

from app.modules.job.models import Job
from app.modules.match.vector import LocalProfileTextVectorProvider


def _detail(*, skills: list[str], target_position: str = "PeopleSoft Consultant"):
    return SimpleNamespace(
        basic_info=SimpleNamespace(
            target_position=target_position,
            highest_education="Bachelor",
            current_city="Shanghai",
        ),
        skills=[SimpleNamespace(skill_name=item, category=None, skill_level=None) for item in skills],
        work_experiences=[],
        projects=[],
    )


def test_local_profile_text_provider_scores_matching_profile_terms():
    provider = LocalProfileTextVectorProvider()
    job = Job(
        title="PeopleSoft HCM Consultant",
        description="Implement enterprise HR systems",
        requirement="PeopleSoft HCM Oracle SQL delivery experience",
        education="Bachelor",
        experience="3 years",
        tags=["PeopleSoft", "HCM", "Oracle", "SQL"],
    )

    result = provider.score(
        job=job,
        detail=_detail(skills=["PeopleSoft", "HCM", "SQL"]),
        config={"min_similarity": 0.5},
    )

    assert result.degrade_reason is None
    assert result.recall_source == "rule_and_vector"
    assert result.semantic_score is not None
    assert result.semantic_score >= 50
    assert result.vector_index_version == "local-profile-text-v1"


def test_local_profile_text_provider_degrades_low_similarity():
    provider = LocalProfileTextVectorProvider()
    job = Job(
        title="PeopleSoft HCM Consultant",
        description="Implement enterprise HR systems",
        requirement="PeopleSoft HCM Oracle SQL delivery experience",
        education="Bachelor",
        experience="3 years",
        tags=["PeopleSoft", "HCM", "Oracle", "SQL"],
    )

    result = provider.score(
        job=job,
        detail=_detail(skills=["Photoshop", "Illustrator"], target_position="Designer"),
        config={"min_similarity": 0.5},
    )

    assert result.semantic_score is None
    assert result.recall_source == "rule_only"
    assert result.degrade_reason == "vector_low_similarity"