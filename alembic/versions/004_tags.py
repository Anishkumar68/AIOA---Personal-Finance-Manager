"""create tags table and transaction_tags association

Revision ID: 004
Revises: 003
Create Date: 2026-04-14

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create tags table
    op.create_table(
        'tags',
        sa.Column('id', sa.Integer(), primary_key=True, index=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(50), nullable=False, index=True),
        sa.Column('color', sa.String(7), nullable=True),  # hex color #RRGGBB
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Create many-to-many association table
    op.create_table(
        'transaction_tags',
        sa.Column('transaction_id', sa.Integer(), sa.ForeignKey('transactions.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('tag_id', sa.Integer(), sa.ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True),
    )


def downgrade() -> None:
    op.drop_table('transaction_tags')
    op.drop_table('tags')
