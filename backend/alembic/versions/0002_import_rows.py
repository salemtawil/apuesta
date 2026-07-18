"""Add import rows.

Revision ID: 0002_import_rows
Revises: 0001_initial
Create Date: 2026-07-16
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_import_rows"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "import_rows",
        sa.Column("import_id", sa.String(length=36), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("sport", sa.String(length=80), nullable=True),
        sa.Column("league", sa.String(length=160), nullable=True),
        sa.Column("event", sa.String(length=220), nullable=True),
        sa.Column("home_team", sa.String(length=160), nullable=True),
        sa.Column("away_team", sa.String(length=160), nullable=True),
        sa.Column("starts_at", sa.String(length=40), nullable=True),
        sa.Column("market_type", sa.String(length=80), nullable=True),
        sa.Column("selection", sa.String(length=160), nullable=True),
        sa.Column("line", sa.Numeric(10, 3), nullable=True),
        sa.Column("odds", sa.Numeric(10, 4), nullable=True),
        sa.Column("odds_format", sa.String(length=20), nullable=True),
        sa.Column("sportsbook", sa.String(length=120), nullable=True),
        sa.Column("captured_at", sa.String(length=40), nullable=True),
        sa.Column("raw_payload", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_event_id", sa.String(length=36), nullable=True),
        sa.Column("created_market_id", sa.String(length=36), nullable=True),
        sa.Column("created_odds_snapshot_id", sa.String(length=36), nullable=True),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["import_id"], ["imports.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_import_rows_user_id", "import_rows", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_import_rows_user_id", table_name="import_rows")
    op.drop_table("import_rows")
