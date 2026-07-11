"""
Base模型
"""
from sqlalchemy.orm import declarative_base

Base = declarative_base()


def import_all_models() -> None:
    """Register all ORM models in Base.metadata."""

    from app.modules.ai_prompt.models import AiPromptConfig  # noqa: F401
    from app.modules.application.models import JobApplication, JobApplicationTimeline  # noqa: F401
    from app.modules.base_data.models import BaseDataOperationLog, StandardPosition, TagLibraryItem  # noqa: F401
    from app.modules.company_certification.models import CompanyCertification  # noqa: F401
    from app.modules.job.models import Job, JobFavorite, JobSubscription, JobVisit  # noqa: F401
    from app.modules.match.models import (  # noqa: F401
        IntelligentMatchingEvaluationModel,
        IntelligentMatchingStrategyModel,
        MatchRuleConfigModel,
        MatchRuleDimensionModel,
        MatchRuleExperimentModel,
        MatchRuleMatchAuditModel,
        MatchRuleOperationAuditModel,
    )
    from app.modules.message.models import ContactExchange, Conversation, ConversationMessage  # noqa: F401
    from app.modules.notification.models import Notification, NotificationPushTask  # noqa: F401
    from app.modules.resume.models import ResumeChunk, ResumeExtractedText, ResumeParseRun, ResumeUpload, SeekerResume  # noqa: F401
    from app.modules.seeker_profile.models import SeekerProfile  # noqa: F401
    from app.modules.user.models import User  # noqa: F401
