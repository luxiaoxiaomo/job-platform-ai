"""add wechat notification readiness

Revision ID: s8b0d3e4f607
Revises: r7a9c0d2e506
Create Date: 2026-06-19 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "s8b0d3e4f607"
down_revision: Union[str, None] = "r7a9c0d2e506"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("wechat_openid", sa.String(length=128), nullable=True, comment="微信OpenID（服务号/小程序维度）"))
    op.add_column("users", sa.Column("wechat_unionid", sa.String(length=128), nullable=True, comment="微信UnionID"))
    op.add_column("users", sa.Column("wechat_app_id", sa.String(length=64), nullable=True, comment="微信应用ID"))
    op.add_column("users", sa.Column("wechat_bound_at", sa.DateTime(), nullable=True, comment="微信绑定时间"))
    op.create_unique_constraint("uq_users_wechat_app_openid", "users", ["wechat_app_id", "wechat_openid"])
    op.create_index("idx_user_wechat_openid", "users", ["wechat_openid"])

    op.add_column(
        "notification_push_tasks",
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0", comment="External provider attempt count"),
    )


def downgrade() -> None:
    op.drop_column("notification_push_tasks", "attempt_count")

    op.drop_index("idx_user_wechat_openid", table_name="users")
    op.drop_constraint("uq_users_wechat_app_openid", "users", type_="unique")
    op.drop_column("users", "wechat_bound_at")
    op.drop_column("users", "wechat_app_id")
    op.drop_column("users", "wechat_unionid")
    op.drop_column("users", "wechat_openid")
