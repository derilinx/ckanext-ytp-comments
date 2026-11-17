"""Create comment tables

Revision ID: 3a6c1d0e2f47
Revises:
Create Date: 2026-11-16 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3a6c1d0e2f47'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Sites that used the old plugin (which created the tables on startup)
    # already have these tables
    if sa.inspect(op.get_bind()).has_table("comment"):
        return

    op.create_table(
        "comment_thread",
        sa.Column("id", sa.UnicodeText, primary_key=True),
        sa.Column("url", sa.UnicodeText),
        sa.Column("creation_date", sa.DateTime),
        sa.Column("locked", sa.Boolean),
    )

    op.create_table(
        "comment",
        sa.Column("id", sa.UnicodeText, primary_key=True),
        sa.Column("parent_id", sa.UnicodeText, sa.ForeignKey("comment.id")),
        sa.Column(
            "thread_id", sa.UnicodeText, sa.ForeignKey("comment_thread.id"),
            nullable=True),
        sa.Column(
            "user_id", sa.UnicodeText, sa.ForeignKey("user.id"),
            nullable=False),
        sa.Column("subject", sa.UnicodeText),
        sa.Column("comment", sa.UnicodeText),
        sa.Column("creation_date", sa.DateTime),
        sa.Column("modified_date", sa.DateTime),
        sa.Column("approval_status", sa.UnicodeText),
        sa.Column("state", sa.UnicodeText),
    )

    op.create_table(
        "comment_blocked",
        sa.Column("id", sa.UnicodeText, primary_key=True),
        sa.Column("user_id", sa.UnicodeText, sa.ForeignKey("user.id")),
        sa.Column("blocked_by", sa.UnicodeText, sa.ForeignKey("user.id")),
        sa.Column("creation_date", sa.DateTime),
    )


def downgrade():
    op.drop_table("comment_blocked")
    op.drop_table("comment")
    op.drop_table("comment_thread")
