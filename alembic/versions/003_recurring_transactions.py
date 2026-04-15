"""create recurring transactions table

Revision ID: 003
Revises: 002
Create Date: 2026-04-14

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'recurring_transactions',
        sa.Column('id', sa.Integer(), primary_key=True, index=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('account_id', sa.Integer(), sa.ForeignKey('accounts.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('category_id', sa.Integer(), sa.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('frequency', sa.String(50), nullable=False),
        sa.Column('interval', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('next_occurrence', sa.Date(), nullable=False, index=True),
        sa.Column('note', sa.String(500), nullable=True),
        sa.Column('reference', sa.String(100), nullable=True),
        sa.Column('transfer_account_id', sa.Integer(), sa.ForeignKey('accounts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_processed', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('recurring_transactions')
