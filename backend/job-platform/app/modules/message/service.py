"""
Message and contact exchange business logic.
"""
from datetime import datetime, timezone
import re

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai_prompt.service import AiPromptService
from app.modules.company_certification.repository import CompanyCertificationRepository
from app.modules.job.repository import JobRepository
from app.modules.message.models import ContactExchange, Conversation, ConversationMessage
from app.modules.message.repository import MessageRepository
from app.modules.message.schemas import (
    ContactExchangeResponse,
    ContactExchangeReview,
    ContactExchangeStatsResponse,
    ContactInfoResponse,
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationOpenRequest,
    ConversationMessageResponse,
    ConversationResponse,
    MessageCreate,
    ReplySuggestionListResponse,
    ReplySuggestionResponse,
)
from app.modules.notification.service import NotificationService
from app.modules.seeker_profile.repository import SeekerProfileRepository
from app.modules.user.models import User
from app.utils.encryption import encryptor


MESSAGE_REPLY_SUGGESTION_SCENARIO = "message_reply_suggestion"

CONTACT_PATTERNS = [
    re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE),
    re.compile(r"(微信|VX|vx|V信|加V|加v|QQ)[:：]?\s*[A-Za-z0-9_\-]{5,}", re.IGNORECASE),
]


def _mask_contacts(content: str) -> tuple[str, bool]:
    masked = content
    hit = False
    for pattern in CONTACT_PATTERNS:
        masked, count = pattern.subn("[联系方式已屏蔽]", masked)
        hit = hit or count > 0
    return masked, hit


def _message_response(message: ConversationMessage) -> ConversationMessageResponse:
    return ConversationMessageResponse(
        id=message.id,
        conversation_id=message.conversation_id,
        sender_id=message.sender_id,
        sender_role=message.sender_role,
        content=message.content,
        original_content=message.original_content,
        moderation_status=message.moderation_status,
        created_at=message.created_at,
    )


class MessageService:
    @staticmethod
    def _ensure_conversation_member(conversation: Conversation, current_user: User) -> None:
        if current_user.id not in {conversation.seeker_id, conversation.recruiter_id}:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    @staticmethod
    @staticmethod
    def _lead_status_for(
        *,
        current_user: User,
        latest_message: ConversationMessage | None,
        latest_exchange: ContactExchange | None,
        application: object | None,
    ) -> tuple[str, str]:
        if latest_exchange is not None:
            if latest_exchange.status == "accepted":
                return "contact_exchanged", "已交换联系方式"
            if latest_exchange.status == "pending":
                if latest_exchange.requester_id == current_user.id:
                    return "contact_waiting", "等待对方同意"
                return "contact_needs_review", "等你确认"
            if latest_exchange.status == "declined":
                return "contact_declined", "已拒绝交换"

        if application is not None:
            return "applied", "已投递"
        if latest_message is not None:
            return "messaged", "已沟通"
        return "opened", "已打开会话"

    @staticmethod
    async def _conversation_response(
        db: AsyncSession,
        conversation: Conversation,
        current_user: User,
    ) -> ConversationResponse:
        latest_message = await MessageRepository.get_latest_message(db, conversation.id)
        latest_exchange = await MessageRepository.get_latest_exchange(db, conversation.id)
        application = await MessageRepository.get_application_for_conversation(db, conversation)
        lead_status, lead_status_label = MessageService._lead_status_for(
            current_user=current_user,
            latest_message=latest_message,
            latest_exchange=latest_exchange,
            application=application,
        )
        exchange_contacts = None
        if latest_exchange is not None and latest_exchange.status == "accepted":
            exchange_contacts = await MessageService._contact_infos(db, conversation)
        return ConversationResponse(
            id=conversation.id,
            job_id=conversation.job_id,
            job_title=conversation.job.title if conversation.job else None,
            seeker_id=conversation.seeker_id,
            seeker_display_name=conversation.seeker.display_name if conversation.seeker else None,
            recruiter_id=conversation.recruiter_id,
            recruiter_display_name=conversation.recruiter.display_name if conversation.recruiter else None,
            last_message_at=conversation.last_message_at,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            latest_message=_message_response(latest_message) if latest_message else None,
            contact_exchange=MessageService._exchange_response(latest_exchange, exchange_contacts) if latest_exchange else None,
            lead_status=lead_status,
            lead_status_label=lead_status_label,
            application_id=application.id if application else None,
            application_status=application.status if application else None,
        )

    @staticmethod
    def _exchange_response(
        exchange: ContactExchange,
        contacts: list[ContactInfoResponse] | None = None,
    ) -> ContactExchangeResponse:
        return ContactExchangeResponse(
            id=exchange.id,
            conversation_id=exchange.conversation_id,
            requester_id=exchange.requester_id,
            requester_role=exchange.requester_role,
            status=exchange.status,
            responder_id=exchange.responder_id,
            responded_at=exchange.responded_at,
            created_at=exchange.created_at,
            contacts=contacts,
        )

    @staticmethod
    async def list_my_conversations(
        db: AsyncSession,
        current_user: User,
        *,
        skip: int = 0,
        limit: int = 20,
    ) -> ConversationListResponse:
        if current_user.role not in {"seeker", "recruiter"}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only seekers and recruiters can use messages")
        items, total = await MessageRepository.list_for_user(
            db,
            user_id=current_user.id,
            role=current_user.role,
            skip=skip,
            limit=limit,
        )
        return ConversationListResponse(
            items=[await MessageService._conversation_response(db, item, current_user) for item in items],
            total=total,
            skip=skip,
            limit=limit,
        )

    @staticmethod
    async def get_contact_exchange_stats(
        db: AsyncSession,
        current_user: User,
    ) -> ContactExchangeStatsResponse:
        if current_user.role == "recruiter":
            counts = await MessageRepository.count_exchanges_by_status(db, recruiter_id=current_user.id)
        elif current_user.role == "admin":
            counts = await MessageRepository.count_exchanges_by_status(db)
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only recruiters and admins can view contact exchange stats",
            )

        return ContactExchangeStatsResponse(
            accepted_count=counts["accepted"],
            pending_count=counts["pending"],
            declined_count=counts["declined"],
            total_count=sum(counts.values()),
        )

    @staticmethod
    async def get_conversation(db: AsyncSession, current_user: User, conversation_id: int) -> ConversationDetailResponse:
        conversation = await MessageRepository.get_conversation_by_id(db, conversation_id)
        if conversation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
        MessageService._ensure_conversation_member(conversation, current_user)
        messages = await MessageRepository.list_messages(db, conversation.id)
        base = await MessageService._conversation_response(db, conversation, current_user)
        return ConversationDetailResponse(
            **base.model_dump(),
            messages=[_message_response(item) for item in messages],
        )

    @staticmethod
    async def send_message(db: AsyncSession, current_user: User, data: MessageCreate) -> ConversationDetailResponse:
        if current_user.role != "seeker":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only seekers can start job conversations")

        job = await JobRepository.get_by_id(db, data.job_id)
        if job is None or job.status != "active":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

        conversation = await MessageRepository.get_conversation_by_job_seeker(db, job.id, current_user.id)
        if conversation is None:
            conversation = Conversation(job_id=job.id, seeker_id=current_user.id, recruiter_id=job.recruiter_id)
            conversation = await MessageRepository.create_conversation(db, conversation, commit=False)
            conversation.job = job
            conversation.seeker = current_user
            conversation.recruiter = job.recruiter

        return await MessageService.reply(db, current_user, conversation.id, data.content)

    @staticmethod
    async def open_conversation(db: AsyncSession, current_user: User, data: ConversationOpenRequest) -> ConversationDetailResponse:
        if current_user.role != "seeker":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only seekers can open job conversations")

        job = await JobRepository.get_by_id(db, data.job_id)
        if job is None or job.status != "active":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

        conversation = await MessageRepository.get_conversation_by_job_seeker(db, job.id, current_user.id)
        if conversation is None:
            conversation = Conversation(job_id=job.id, seeker_id=current_user.id, recruiter_id=job.recruiter_id)
            conversation = await MessageRepository.create_conversation(db, conversation)
            conversation.job = job
            conversation.seeker = current_user
            conversation.recruiter = job.recruiter

        return await MessageService.get_conversation(db, current_user, conversation.id)

    @staticmethod
    async def reply(db: AsyncSession, current_user: User, conversation_id: int, content: str) -> ConversationDetailResponse:
        conversation = await MessageRepository.get_conversation_by_id(db, conversation_id)
        if conversation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
        MessageService._ensure_conversation_member(conversation, current_user)

        cleaned = content.strip()
        if not cleaned:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message content cannot be empty")
        if len(cleaned) > 1000:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message content is too long")

        masked, has_contact = _mask_contacts(cleaned)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        message = ConversationMessage(
            conversation_id=conversation.id,
            sender_id=current_user.id,
            sender_role=current_user.role,
            content=masked,
            original_content=cleaned if has_contact else None,
            moderation_status="masked" if has_contact else "pass",
            created_at=now,
        )
        conversation.last_message_at = now
        db.add(conversation)
        created = await MessageRepository.add_message(db, message, commit=False)
        await NotificationService.notify_message_received(
            db,
            conversation=conversation,
            sender=current_user,
            message=created,
            commit=False,
        )
        await db.commit()
        await db.refresh(created)
        return await MessageService.get_conversation(db, current_user, conversation.id)

    @staticmethod
    async def get_reply_suggestions(
        db: AsyncSession,
        current_user: User,
        conversation_id: int,
    ) -> ReplySuggestionListResponse:
        conversation = await MessageRepository.get_conversation_by_id(db, conversation_id)
        if conversation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
        MessageService._ensure_conversation_member(conversation, current_user)

        messages = await MessageRepository.list_messages(db, conversation.id)
        application = await MessageRepository.get_application_for_conversation(db, conversation)
        latest_exchange = await MessageRepository.get_latest_exchange(db, conversation.id)
        source = await MessageService._reply_suggestion_source(db)
        suggestions = MessageService._build_reply_suggestions(
            current_user=current_user,
            conversation=conversation,
            messages=messages,
            application=application,
            latest_exchange=latest_exchange,
            source=source,
        )
        return ReplySuggestionListResponse(
            conversation_id=conversation.id,
            scenario_key=MESSAGE_REPLY_SUGGESTION_SCENARIO,
            source=source,
            suggestions=suggestions,
        )

    @staticmethod
    async def _reply_suggestion_source(db: AsyncSession) -> str:
        try:
            active = await AiPromptService.get_active(db, MESSAGE_REPLY_SUGGESTION_SCENARIO)
        except HTTPException:
            return "template_fallback"
        return f"active_prompt_v{active.version}_template_fallback"

    @staticmethod
    def _build_reply_suggestions(
        *,
        current_user: User,
        conversation: Conversation,
        messages: list[ConversationMessage],
        application: object | None,
        latest_exchange: ContactExchange | None,
        source: str,
    ) -> list[ReplySuggestionResponse]:
        job_title = conversation.job.title if conversation.job else f"岗位 #{conversation.job_id}"
        peer_name = conversation.seeker.display_name if current_user.role == "recruiter" else conversation.recruiter.display_name
        peer_name = peer_name or "您好"
        latest_peer_message = next(
            (message for message in reversed(messages) if message.sender_id != current_user.id),
            None,
        )
        latest_peer_text = latest_peer_message.content if latest_peer_message else ""

        if current_user.role == "recruiter":
            texts = MessageService._recruiter_reply_texts(
                job_title=job_title,
                peer_name=peer_name,
                application=application,
                latest_exchange=latest_exchange,
                latest_peer_text=latest_peer_text,
            )
        else:
            texts = MessageService._seeker_reply_texts(
                job_title=job_title,
                peer_name=peer_name,
                application=application,
                latest_exchange=latest_exchange,
                latest_peer_text=latest_peer_text,
            )

        styles = ["稳妥", "推进", "补充信息"]
        return [
            ReplySuggestionResponse(style=styles[index], text=text, source=source)
            for index, text in enumerate(MessageService._dedupe_three(texts))
        ]

    @staticmethod
    def _recruiter_reply_texts(
        *,
        job_title: str,
        peer_name: str,
        application: object | None,
        latest_exchange: ContactExchange | None,
        latest_peer_text: str,
    ) -> list[str]:
        texts: list[str] = []
        if latest_exchange and latest_exchange.status == "pending":
            texts.append(f"{peer_name}，可以的，我这边同意通过平台交换联系方式，后续沟通会继续保留在平台记录里。")
        if application is not None:
            texts.append(f"{peer_name}，你的简历和投递我已经看到了。我会结合 {job_title} 的要求做进一步评估，有结果会尽快同步你。")
        if any(keyword in latest_peer_text for keyword in ["薪资", "工资", "待遇", "面试", "时间"]):
            texts.append(f"{peer_name}，关于 {job_title} 的细节我可以进一步说明。你方便的话，也可以补充一下期望薪资和可面试时间。")
        texts.extend(
            [
                f"{peer_name}，感谢关注 {job_title}。方便补充一下最近一段相关经历、到岗时间和期望工作城市吗？",
                f"{peer_name}，这边先确认下你的核心技能和项目经历，如果匹配度合适，我会推进下一步沟通。",
                f"{peer_name}，收到。我会先看岗位匹配情况，需要补充信息时再和你确认。",
            ]
        )
        return texts

    @staticmethod
    def _seeker_reply_texts(
        *,
        job_title: str,
        peer_name: str,
        application: object | None,
        latest_exchange: ContactExchange | None,
        latest_peer_text: str,
    ) -> list[str]:
        texts: list[str] = []
        if latest_exchange and latest_exchange.status == "pending":
            texts.append(f"{peer_name}，可以的，我愿意通过平台交换联系方式，也希望后续沟通继续保留平台记录。")
        if application is not None:
            texts.append(f"{peer_name}，我已投递 {job_title}，简历信息也已提交。如需补充项目经历或到岗时间，我可以继续说明。")
        if any(keyword in latest_peer_text for keyword in ["面试", "时间", "方便", "到岗"]):
            texts.append(f"{peer_name}，我这边可以配合沟通。请问预计面试形式、时间安排和需要提前准备的内容是什么？")
        texts.extend(
            [
                f"{peer_name}，您好，我对 {job_title} 比较感兴趣，想进一步了解岗位职责、团队情况和后续流程。",
                f"{peer_name}，我可以补充说明相关项目经历和技能栈，也请您看下当前简历是否符合岗位要求。",
                f"{peer_name}，收到。我会继续关注平台消息，如需补充材料可以直接告诉我。",
            ]
        )
        return texts

    @staticmethod
    def _dedupe_three(texts: list[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for text in texts:
            normalized = " ".join(text.strip().split())
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            result.append(normalized)
            if len(result) == 3:
                break
        return result

    @staticmethod
    async def request_contact_exchange(
        db: AsyncSession,
        current_user: User,
        conversation_id: int,
    ) -> ContactExchangeResponse:
        conversation = await MessageRepository.get_conversation_by_id(db, conversation_id)
        if conversation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
        MessageService._ensure_conversation_member(conversation, current_user)

        pending = await MessageRepository.get_pending_exchange(db, conversation.id)
        if pending is not None:
            return MessageService._exchange_response(pending)

        exchange = ContactExchange(
            conversation_id=conversation.id,
            requester_id=current_user.id,
            requester_role=current_user.role,
            status="pending",
        )
        created = await MessageRepository.create_exchange(db, exchange)
        return MessageService._exchange_response(created)

    @staticmethod
    async def review_contact_exchange(
        db: AsyncSession,
        current_user: User,
        exchange_id: int,
        data: ContactExchangeReview,
    ) -> ContactExchangeResponse:
        exchange = await MessageRepository.get_exchange_by_id(db, exchange_id)
        if exchange is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact exchange not found")
        conversation = await MessageRepository.get_conversation_by_id(db, exchange.conversation_id)
        if conversation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
        MessageService._ensure_conversation_member(conversation, current_user)
        if exchange.requester_id == current_user.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Requester cannot review own contact exchange")
        if exchange.status != "pending":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Contact exchange already reviewed")

        exchange.status = "accepted" if data.action == "accept" else "declined"
        exchange.responder_id = current_user.id
        exchange.responded_at = datetime.now(timezone.utc).replace(tzinfo=None)
        updated = await MessageRepository.update_exchange(db, exchange)
        contacts = await MessageService._contact_infos(db, conversation) if updated.status == "accepted" else None
        return MessageService._exchange_response(updated, contacts)

    @staticmethod
    async def _contact_infos(db: AsyncSession, conversation: Conversation) -> list[ContactInfoResponse]:
        certification = await CompanyCertificationRepository.get_by_recruiter_id(db, conversation.recruiter_id)
        certification = certification if certification and certification.status == "approved" else None
        seeker_profile = await SeekerProfileRepository.get_by_seeker_id(db, conversation.seeker_id)
        job = conversation.job

        seeker_display_name = conversation.seeker.display_name
        seeker_phone = None
        seeker_email = None
        seeker_wechat = None
        if seeker_profile is not None:
            if seeker_profile.name_public and seeker_profile.real_name:
                seeker_display_name = seeker_profile.real_name
            if seeker_profile.phone_public and conversation.seeker.phone_encrypted:
                seeker_phone = encryptor.decrypt(conversation.seeker.phone_encrypted)
            if seeker_profile.email_public:
                seeker_email = seeker_profile.email
            if seeker_profile.wechat_public:
                seeker_wechat = seeker_profile.wechat
        elif conversation.seeker.phone_encrypted:
            seeker_phone = encryptor.decrypt(conversation.seeker.phone_encrypted)

        recruiter_display_name = conversation.recruiter.display_name
        recruiter_company_name = None
        if job and job.company_display_mode == "anonymous":
            recruiter_display_name = "认证企业"
        elif job and job.company_display_mode == "company_name" and certification is not None:
            recruiter_display_name = certification.company_name
            recruiter_company_name = certification.company_name

        recruiter_phone = None
        recruiter_email = None
        recruiter_wechat = None
        if job and job.contact_phone_public and certification and certification.applicant_phone:
            recruiter_phone = certification.applicant_phone
        elif job and job.contact_phone_public and conversation.recruiter.phone_encrypted:
            recruiter_phone = encryptor.decrypt(conversation.recruiter.phone_encrypted)
        if job and job.contact_email_public and certification:
            recruiter_email = certification.work_email
        if job and job.contact_wechat_public and certification:
            recruiter_wechat = certification.applicant_wechat

        return [
            ContactInfoResponse(
                user_id=conversation.seeker_id,
                display_name=seeker_display_name,
                role="seeker",
                phone=seeker_phone,
                email=seeker_email,
                wechat=seeker_wechat,
            ),
            ContactInfoResponse(
                user_id=conversation.recruiter_id,
                display_name=recruiter_display_name,
                role="recruiter",
                phone=recruiter_phone,
                email=recruiter_email,
                wechat=recruiter_wechat,
                company_name=recruiter_company_name,
            ),
        ]
