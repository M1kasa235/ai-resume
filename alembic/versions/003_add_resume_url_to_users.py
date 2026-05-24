"""add resume_url to users

Revision ID: 003
Revises: 002
Create Date: 2026-05-24
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("resume_url", sa.String(length=255), nullable=True, comment="简历URL"),
    )

    # 兼容历史数据：此前简历路径复用 avatar_url 字段。
    op.execute(
        """
        UPDATE users
        SET resume_url = avatar_url
        WHERE resume_url IS NULL
          AND avatar_url LIKE '/uploads/resumes/%'
        """
    )


def downgrade() -> None:
    # 降级前回填，避免 resume_url 数据丢失。
    op.execute(
        """
        UPDATE users
        SET avatar_url = resume_url
        WHERE resume_url IS NOT NULL
          AND (avatar_url IS NULL OR avatar_url = '')
        """
    )
    op.drop_column("users", "resume_url")
