"""
Message persistence helpers.
"""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.message.models import ContactExchange, Conversation, ConversationMessage


class MessageRepository:
    @staticmethod
    async def get_conversation_by_job_seeker(db: AsyncSession, job_id: int, seeker_id: int) -> Conversation | None:
        result = await db.execute(
            select(Conversation)
            .options(selectinload(Conversation.job), selectinload(Conversation.seeker), selectinload(Conversation.recruiter))
            .where(Conversation.job_id == job_id, Conversation.seeker_id == seeker_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_conversation_by_id(db: AsyncSession, conversation_id: int) -> Conversation | None:
        result = await db.execute(
            select(Conversation)
            .options(selectinload(Conversation.job), selectinload(Conversation.seeker), selectinload(Conversation.recruiter))
            .where(Conversation.id == conversation_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_conversation(db: AsyncSession, conversation: Conversation, *, commit: bool = True) -> Conversation:
        db.add(conversation)
        if commit:
            await db.commit()
            await db.refresh(conversation)
        else:
            await db.flush()
        return conversation

    @staticmethod
    async def list_for_user(
        db: AsyncSession,
        *,
        user_id: int,
        role: str,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Conversation], int]:
        filters = [Conversation.seeker_id == user_id] if role == "seeker" else [Conversation.recruiter_id == user_id]
        total_result = await db.execute(select(func.count()).select_from(Conversation).where(*filters))
        total = int(total_result.scalar_one())
        result = await db.execute(
            select(Conversation)
            .options(selectinload(Conversation.job), selectinload(Conversation.seeker), selectinload(Conversation.recruiter))
            .where(*filters)
            .order_by(Conversation.last_message_at.desc().nullslast(), Conversation.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    @staticmethod
    async def add_message(db: AsyncSession, message: ConversationMessage, *, commit: bool = True) -> ConversationMessage:
        db.add(message)
        if commit:
            await db.commit()
            await db.refresh(message)
        else:
            await db.flush()
        return message

    @staticmethod
    async def list_messages(db: AsyncSession, conversation_id: int) -> list[ConversationMessage]:
        result = await db.execute(
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation_id)
            .order_by(ConversationMessage.created_at.asc(), ConversationMessage.id.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_latest_message(db: AsyncSession, conversation_id: int) -> ConversationMessage | None:
        result = await db.execute(
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation_id)
            .order_by(ConversationMessage.created_at.desc(), ConversationMessage.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_application_for_conversation(db: AsyncSession, conversation: Conversation):
        from app.modules.application.models import JobApplication

        result = await db.execute(
            select(JobApplication).where(
                JobApplication.job_id == conversation.job_id,
                JobApplication.seeker_id == conversation.seeker_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_pending_exchange(db: AsyncSession, conversation_id: int) -> ContactExchange | None:
        result = await db.execute(
            select(ContactExchange)
            .where(ContactExchange.conversation_id == conversation_id, ContactExchange.status == "pending")
            .order_by(ContactExchange.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_latest_exchange(db: AsyncSession, conversation_id: int) -> ContactExchange | None:
        result = await db.execute(
            select(ContactExchange)
            .where(ContactExchange.conversation_id == conversation_id)
            .order_by(ContactExchange.created_at.desc(), ContactExchange.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_exchange_by_id(db: AsyncSession, exchange_id: int) -> ContactExchange | None:
        result = await db.execute(select(ContactExchange).where(ContactExchange.id == exchange_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create_exchange(db: AsyncSession, exchange: ContactExchange) -> ContactExchange:
        db.add(exchange)
        await db.commit()
        await db.refresh(exchange)
        return exchange

    @staticmethod
    async def update_exchange(db: AsyncSession, exchange: ContactExchange) -> ContactExchange:
        db.add(exchange)
        await db.commit()
        await db.refresh(exchange)
        return exchange

    @staticmethod
    async def count_exchanges_by_status(
        db: AsyncSession,
        *,
        recruiter_id: int | None = None,
    ) -> dict[str, int]:
        query = (
            select(ContactExchange.status, func.count(ContactExchange.id))
            .select_from(ContactExchange)
            .join(Conversation, Conversation.id == ContactExchange.conversation_id)
        )
        if recruiter_id is not None:
            query = query.where(Conversation.recruiter_id == recruiter_id)
        query = query.group_by(ContactExchange.status)

        result = await db.execute(query)
        counts = {"pending": 0, "accepted": 0, "declined": 0}
        for status, count in result.all():
            counts[status] = int(count)
        return counts
