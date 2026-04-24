"""create goals and goal_contributions tables

Revision ID: 005
Revises: 004
Create Date: 2026-04-24

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "goals",
        sa.Column("id", sa.Integer(), primary_key=True, index=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(length=120), nullable=False, index=True),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="INR"),
        sa.Column("target_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False, index=True),
        sa.Column("target_date", sa.Date(), nullable=True, index=True),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1"), index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    op.create_table(
        "goal_contributions",
        sa.Column("id", sa.Integer(), primary_key=True, index=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("goal_id", sa.Integer(), sa.ForeignKey("goals.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("date", sa.Date(), nullable=False, index=True),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("goal_contributions")
    op.drop_table("goals")

