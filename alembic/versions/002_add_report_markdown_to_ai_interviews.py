"""add report_markdown to ai_interviews

Revision ID: 002
Revises: 001
Create Date: 2026-05-21
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ai_interviews",
        sa.Column("report_markdown", sa.Text, nullable=True, comment="完整Markdown评估报告"),
    )


def downgrade() -> None:
    op.drop_column("ai_interviews", "report_markdown")
