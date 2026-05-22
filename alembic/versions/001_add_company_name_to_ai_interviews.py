"""add company_name to ai_interviews

Revision ID: 001
Revises: None
Create Date: 2026-05-20
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ai_interviews",
        sa.Column("company_name", sa.String(100), nullable=True, comment="目标公司名称"),
    )


def downgrade() -> None:
    op.drop_column("ai_interviews", "company_name")
