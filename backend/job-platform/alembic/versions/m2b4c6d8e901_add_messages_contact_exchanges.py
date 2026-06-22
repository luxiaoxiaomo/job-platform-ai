"""Add conversations and contact exchanges.

Revision ID: m2b4c6d8e901
Revises: l1a2b3c4d501
Create Date: 2026-06-17 16:20:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "m2b4c6d8e901"
down_revision: Union[str, None] = "l1a2b3c4d501"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer(), nullable=False, comment="Conversation ID"),
        sa.Column("job_id", sa.Integer(), nullable=False, comment="Job ID"),
        sa.Column("seeker_id", sa.Integer(), nullable=False, comment="Seeker user ID"),
        sa.Column("recruiter_id", sa.Integer(), nullable=False, comment="Recruiter user ID"),
        sa.Column("last_message_at", sa.DateTime(), nullable=True, comment="Last message time"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"), comment="Created at"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"), comment="Updated at"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recruiter_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["seeker_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id", "seeker_id", name="uq_conversations_job_seeker"),
    )
    op.create_index(op.f("ix_conversations_id"), "conversations", ["id"], unique=False)
    op.create_index("idx_conversations_job_id", "conversations", ["job_id"], unique=False)
    op.create_index("idx_conversations_seeker_id", "conversations", ["seeker_id"], unique=False)
    op.create_index("idx_conversations_recruiter_id", "conversations", ["recruiter_id"], unique=False)
    op.create_index("idx_conversations_last_message_at", "conversations", ["last_message_at"], unique=False)

    op.create_table(
        "conversation_messages",
        sa.Column("id", sa.Integer(), nullable=False, comment="Message ID"),
        sa.Column("conversation_id", sa.Integer(), nullable=False, comment="Conversation ID"),
        sa.Column("sender_id", sa.Integer(), nullable=False, comment="Sender user ID"),
        sa.Column("sender_role", sa.String(length=30), nullable=False, comment="seeker/recruiter"),
        sa.Column("content", sa.Text(), nullable=False, comment="Sanitized message content"),
        sa.Column("original_content", sa.Text(), nullable=True, comment="Original message content when sanitized"),
        sa.Column("moderation_status", sa.String(length=30), nullable=False, server_default="pass", comment="pass/masked"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"), comment="Created at"),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sender_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_conversation_messages_id"), "conversation_messages", ["id"], unique=False)
    op.create_index("idx_conversation_messages_conversation_id", "conversation_messages", ["conversation_id"], unique=False)
    op.create_index("idx_conversation_messages_sender_id", "conversation_messages", ["sender_id"], unique=False)
    op.create_index("idx_conversation_messages_created_at", "conversation_messages", ["created_at"], unique=False)

    op.create_table(
        "contact_exchanges",
        sa.Column("id", sa.Integer(), nullable=False, comment="Contact exchange ID"),
        sa.Column("conversation_id", sa.Integer(), nullable=False, comment="Conversation ID"),
        sa.Column("requester_id", sa.Integer(), nullable=False, comment="Requester user ID"),
        sa.Column("requester_role", sa.String(length=30), nullable=False, comment="seeker/recruiter"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="pending", comment="pending/accepted/declined"),
        sa.Column("responder_id", sa.Integer(), nullable=True, comment="Responder user ID"),
        sa.Column("responded_at", sa.DateTime(), nullable=True, comment="Responded at"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"), comment="Created at"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"), comment="Updated at"),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["responder_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_contact_exchanges_id"), "contact_exchanges", ["id"], unique=False)
    op.create_index("idx_contact_exchanges_conversation_id", "contact_exchanges", ["conversation_id"], unique=False)
    op.create_index("idx_contact_exchanges_status", "contact_exchanges", ["status"], unique=False)
    op.create_index("idx_contact_exchanges_requester_id", "contact_exchanges", ["requester_id"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_contact_exchanges_requester_id", table_name="contact_exchanges")
    op.drop_index("idx_contact_exchanges_status", table_name="contact_exchanges")
    op.drop_index("idx_contact_exchanges_conversation_id", table_name="contact_exchanges")
    op.drop_index(op.f("ix_contact_exchanges_id"), table_name="contact_exchanges")
    op.drop_table("contact_exchanges")

    op.drop_index("idx_conversation_messages_created_at", table_name="conversation_messages")
    op.drop_index("idx_conversation_messages_sender_id", table_name="conversation_messages")
    op.drop_index("idx_conversation_messages_conversation_id", table_name="conversation_messages")
    op.drop_index(op.f("ix_conversation_messages_id"), table_name="conversation_messages")
    op.drop_table("conversation_messages")

    op.drop_index("idx_conversations_last_message_at", table_name="conversations")
    op.drop_index("idx_conversations_recruiter_id", table_name="conversations")
    op.drop_index("idx_conversations_seeker_id", table_name="conversations")
    op.drop_index("idx_conversations_job_id", table_name="conversations")
    op.drop_index(op.f("ix_conversations_id"), table_name="conversations")
    op.drop_table("conversations")
