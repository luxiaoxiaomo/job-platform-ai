"""initial_schema_with_phone_hash

Revision ID: 421bc078883c
Revises:
Create Date: 2026-06-06 10:11:25.352235

说明：
- 初始数据库表结构，包含phone_hash字段
- phone_hash用于确定性查询和唯一性检查
- phone_encrypted用于加密存储和展示
- 要求：新部署直接使用此迁移；旧数据需先迁移phone_hash后再升级
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '421bc078883c'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    创建users表，包含phone_hash字段

    注意：
    - 此迁移适用于全新部署
    - 如果表已存在且有数据，需要手动迁移phone_hash字段
    - 使用postgresql.ENUM确保ENUM类型只创建一次
    """
    # 创建users表（ENUM类型会自动创建）
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False, comment='用户ID'),
    sa.Column('phone_hash', sa.String(length=64), nullable=False, comment='手机号哈希（HMAC-SHA256，用于查询）'),
    sa.Column('phone_encrypted', sa.String(length=200), nullable=False, comment='加密的手机号（Fernet，用于展示）'),
    sa.Column('password_hash', sa.String(length=200), nullable=False, comment='密码哈希'),
    sa.Column('display_name', sa.String(length=50), nullable=False, comment='显示名称'),
    sa.Column('real_name_encrypted', sa.String(length=200), nullable=True, comment='加密的真实姓名'),
    sa.Column('role', postgresql.ENUM('seeker', 'recruiter', 'admin', name='user_role', create_type=True), nullable=False, comment='角色：seeker应聘者/recruiter招聘者/admin管理员'),
    sa.Column('avatar_url', sa.String(length=500), nullable=True, comment='头像URL'),
    sa.Column('status', postgresql.ENUM('active', 'inactive', 'banned', name='user_status', create_type=True), nullable=False, comment='状态：active活跃/inactive未激活/banned封禁'),
    sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
    sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),
    sa.PrimaryKeyConstraint('id', name='pk_users'),
    sa.UniqueConstraint('phone_hash', name='uq_users_phone_hash')
    )

    # 创建索引
    op.create_index('idx_users_phone_hash', 'users', ['phone_hash'], unique=False)
    op.create_index('idx_users_role', 'users', ['role'], unique=False)
    op.create_index('idx_users_status', 'users', ['status'], unique=False)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)


def downgrade() -> None:
    """
    删除users表及相关索引和ENUM类型
    """
    # 删除索引和表
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index('idx_users_status', table_name='users')
    op.drop_index('idx_users_role', table_name='users')
    op.drop_index('idx_users_phone_hash', table_name='users')
    op.drop_table('users')

    # 删除ENUM类型
    op.execute("DROP TYPE IF EXISTS user_role")
    op.execute("DROP TYPE IF EXISTS user_status")
