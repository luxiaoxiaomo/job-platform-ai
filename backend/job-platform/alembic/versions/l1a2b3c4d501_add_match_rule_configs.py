"""add match rule configs

Revision ID: l1a2b3c4d501
Revises: k9f1a2b3c401
Create Date: 2026-06-17 10:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "l1a2b3c4d501"
down_revision: Union[str, None] = "k9f1a2b3c401"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _json_type():
    return sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")


DEFAULT_DIMENSIONS = [
    (
        "skill",
        "技能匹配",
        35,
        "岗位标签、岗位描述中的技能要求与简历技能做规则匹配",
        "命中岗位技能越多，分数越高；未识别岗位技能时按中性分处理",
        {"type": "keyword_match", "sources": ["job.tags", "job.description", "job.requirement", "resume.skills"]},
    ),
    (
        "experience",
        "经验年限",
        20,
        "简历工作年限与岗位经验要求做比较",
        "满足要求给高分，低于要求按差距扣分",
        {"type": "threshold_compare", "source": "resume.basic_info.work_years"},
    ),
    (
        "education",
        "学历匹配",
        15,
        "最高学历与岗位学历门槛做等级比较",
        "达到或超过岗位要求给高分，低于要求按等级差距扣分",
        {"type": "rank_compare", "source": "resume.basic_info.highest_education"},
    ),
    (
        "city",
        "城市匹配",
        10,
        "当前城市与岗位城市做文本匹配",
        "城市一致给高分，不一致扣分；缺失当前城市按中性分处理",
        {"type": "text_contains", "source": "resume.basic_info.current_city"},
    ),
    (
        "salary",
        "薪资匹配",
        10,
        "期望薪资与岗位薪资区间是否重叠",
        "区间重叠给高分，缺失信息按中性分处理",
        {"type": "range_overlap", "source": "resume.basic_info.expected_salary"},
    ),
    (
        "intention",
        "岗位意向",
        10,
        "求职目标岗位与当前岗位标题做关键词匹配",
        "标题和求职意向关键词重合越多，分数越高",
        {"type": "token_overlap", "source": "resume.basic_info.target_position"},
    ),
]


def upgrade() -> None:
    op.create_table(
        "match_rule_configs",
        sa.Column("id", sa.Integer(), nullable=False, comment="Match rule config ID"),
        sa.Column("name", sa.String(length=120), nullable=False, comment="Display name"),
        sa.Column("strategy", sa.String(length=50), nullable=False, server_default="rule_v1", comment="Matching strategy"),
        sa.Column("scope", sa.String(length=80), nullable=False, server_default="global", comment="Rule scope"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="draft", comment="draft/active/testing/archived"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1", comment="Version number"),
        sa.Column("description", sa.Text(), nullable=False, server_default="", comment="Rule description"),
        sa.Column("parent_version_id", sa.Integer(), nullable=True, comment="Parent version ID"),
        sa.Column("effective_from", sa.DateTime(), nullable=True, comment="Effective from"),
        sa.Column("effective_to", sa.DateTime(), nullable=True, comment="Effective to"),
        sa.Column("created_by", sa.Integer(), nullable=True, comment="Creator user ID"),
        sa.Column("updated_by", sa.Integer(), nullable=True, comment="Updater user ID"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), comment="Created at"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), comment="Updated at"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["parent_version_id"], ["match_rule_configs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scope", "version", name="uq_match_rule_configs_scope_version"),
    )
    op.create_index(op.f("ix_match_rule_configs_id"), "match_rule_configs", ["id"], unique=False)
    op.create_index("idx_match_rule_configs_parent_version_id", "match_rule_configs", ["parent_version_id"], unique=False)
    op.create_index("idx_match_rule_configs_scope_status", "match_rule_configs", ["scope", "status"], unique=False)

    op.create_table(
        "match_rule_dimensions",
        sa.Column("id", sa.Integer(), nullable=False, comment="Match rule dimension ID"),
        sa.Column("config_id", sa.Integer(), nullable=False, comment="Match rule config ID"),
        sa.Column("dimension_key", sa.String(length=50), nullable=False, comment="Dimension key"),
        sa.Column("label", sa.String(length=80), nullable=False, comment="Display label"),
        sa.Column("weight", sa.Float(), nullable=False, server_default="0", comment="Configured weight"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true(), comment="Whether dimension is enabled"),
        sa.Column("description", sa.Text(), nullable=False, server_default="", comment="Dimension description"),
        sa.Column("scoring_method", sa.Text(), nullable=False, server_default="", comment="Human-readable scoring method"),
        sa.Column("logic_json", _json_type(), nullable=True, comment="Structured rule logic"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0", comment="Display order"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), comment="Created at"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), comment="Updated at"),
        sa.ForeignKeyConstraint(["config_id"], ["match_rule_configs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("config_id", "dimension_key", name="uq_match_rule_dimensions_config_key"),
    )
    op.create_index(op.f("ix_match_rule_dimensions_id"), "match_rule_dimensions", ["id"], unique=False)
    op.create_index("idx_match_rule_dimensions_config_id", "match_rule_dimensions", ["config_id"], unique=False)
    op.create_index("idx_match_rule_dimensions_dimension_key", "match_rule_dimensions", ["dimension_key"], unique=False)

    config_table = sa.table(
        "match_rule_configs",
        sa.column("id", sa.Integer()),
        sa.column("name", sa.String()),
        sa.column("strategy", sa.String()),
        sa.column("scope", sa.String()),
        sa.column("status", sa.String()),
        sa.column("version", sa.Integer()),
        sa.column("description", sa.Text()),
    )
    dimension_table = sa.table(
        "match_rule_dimensions",
        sa.column("config_id", sa.Integer()),
        sa.column("dimension_key", sa.String()),
        sa.column("label", sa.String()),
        sa.column("weight", sa.Float()),
        sa.column("enabled", sa.Boolean()),
        sa.column("description", sa.Text()),
        sa.column("scoring_method", sa.Text()),
        sa.column("logic_json", _json_type()),
        sa.column("sort_order", sa.Integer()),
    )
    op.bulk_insert(
        config_table,
        [
            {
                "id": 1,
                "name": "默认人岗匹配规则 V1",
                "strategy": "rule_v1",
                "scope": "global",
                "status": "active",
                "version": 1,
                "description": "规则版 V1，基于技能、经验、学历、城市、薪资和岗位意向计算匹配度",
            }
        ],
    )
    op.bulk_insert(
        dimension_table,
        [
            {
                "config_id": 1,
                "dimension_key": key,
                "label": label,
                "weight": float(weight),
                "enabled": True,
                "description": description,
                "scoring_method": scoring_method,
                "logic_json": logic,
                "sort_order": index,
            }
            for index, (key, label, weight, description, scoring_method, logic) in enumerate(DEFAULT_DIMENSIONS, start=1)
        ],
    )
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            "SELECT setval(pg_get_serial_sequence('match_rule_configs', 'id'), "
            "COALESCE((SELECT MAX(id) FROM match_rule_configs), 1), true)"
        )


def downgrade() -> None:
    op.drop_index("idx_match_rule_dimensions_dimension_key", table_name="match_rule_dimensions")
    op.drop_index("idx_match_rule_dimensions_config_id", table_name="match_rule_dimensions")
    op.drop_index(op.f("ix_match_rule_dimensions_id"), table_name="match_rule_dimensions")
    op.drop_table("match_rule_dimensions")
    op.drop_index("idx_match_rule_configs_scope_status", table_name="match_rule_configs")
    op.drop_index("idx_match_rule_configs_parent_version_id", table_name="match_rule_configs")
    op.drop_index(op.f("ix_match_rule_configs_id"), table_name="match_rule_configs")
    op.drop_table("match_rule_configs")
