"""udhar khata - contacts and loans

Revision ID: 002_udhar_khata
Revises: 001_initial
Create Date: 2026-04-13

"""

from alembic import op
import sqlalchemy as sa


revision = "002_udhar_khata"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "contacts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("notes", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_contacts_id"), "contacts", ["id"], unique=False)
    op.create_index(op.f("ix_contacts_user_id"), "contacts", ["user_id"], unique=False)
    op.create_index(op.f("ix_contacts_is_active"), "contacts", ["is_active"], unique=False)

    op.create_table(
        "loans",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("contact_id", sa.Integer(), nullable=False),
        sa.Column("direction", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("title", sa.String(120), nullable=True),
        sa.Column("currency", sa.String(10), nullable=False, server_default="USD"),
        sa.Column("interest_rate", sa.Numeric(7, 4), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"], ondelete="RESTRICT"),
    )
    op.create_index(op.f("ix_loans_id"), "loans", ["id"], unique=False)
    op.create_index(op.f("ix_loans_user_id"), "loans", ["user_id"], unique=False)
    op.create_index(op.f("ix_loans_contact_id"), "loans", ["contact_id"], unique=False)
    op.create_index(op.f("ix_loans_direction"), "loans", ["direction"], unique=False)
    op.create_index(op.f("ix_loans_status"), "loans", ["status"], unique=False)
    op.create_index(op.f("ix_loans_start_date"), "loans", ["start_date"], unique=False)
    op.create_index(op.f("ix_loans_due_date"), "loans", ["due_date"], unique=False)

    op.create_table(
        "loan_entries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("loan_id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("note", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["loan_id"], ["loans.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_loan_entries_id"), "loan_entries", ["id"], unique=False)
    op.create_index(op.f("ix_loan_entries_user_id"), "loan_entries", ["user_id"], unique=False)
    op.create_index(op.f("ix_loan_entries_loan_id"), "loan_entries", ["loan_id"], unique=False)
    op.create_index(op.f("ix_loan_entries_kind"), "loan_entries", ["kind"], unique=False)
    op.create_index(op.f("ix_loan_entries_occurred_at"), "loan_entries", ["occurred_at"], unique=False)


def downgrade() -> None:
    op.drop_table("loan_entries")
    op.drop_table("loans")
    op.drop_table("contacts")

