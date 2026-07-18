"""Prediction pipeline, sync jobs and backtesting.

Revision ID: 0004_prediction_pipeline
Revises: 0003_sports_intelligence
Create Date: 2026-07-17
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004_prediction_pipeline"
down_revision: str | None = "0003_sports_intelligence"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def id_timestamps() -> list[sa.Column]:
    return [
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def user_id() -> sa.Column:
    return sa.Column("user_id", sa.String(length=36), nullable=False)


def upgrade() -> None:
    op.create_table(
        "data_providers",
        sa.Column("provider_key", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("sport_slug", sa.String(length=80), nullable=True),
        sa.Column("base_url", sa.String(length=500), nullable=True),
        sa.Column("api_key_env", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("last_sync_at", sa.String(length=40), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        user_id(),
        *id_timestamps(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_data_providers_user_id", "data_providers", ["user_id"])

    op.create_table(
        "sync_job_runs",
        sa.Column("provider_key", sa.String(length=80), nullable=False),
        sa.Column("job_type", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("started_at", sa.String(length=40), nullable=False),
        sa.Column("finished_at", sa.String(length=40), nullable=True),
        sa.Column("records_upserted", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        user_id(),
        *id_timestamps(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sync_job_runs_user_id", "sync_job_runs", ["user_id"])

    op.create_table(
        "prediction_records",
        sa.Column("event_id", sa.String(length=36), nullable=False),
        sa.Column("analysis_id", sa.String(length=36), nullable=True),
        sa.Column("market_type", sa.String(length=80), nullable=False),
        sa.Column("selection_name", sa.String(length=160), nullable=False),
        sa.Column("estimated_probability", sa.Numeric(10, 8), nullable=False),
        sa.Column("fair_odds", sa.Numeric(10, 4), nullable=False),
        sa.Column("offered_odds", sa.Numeric(10, 4), nullable=True),
        sa.Column("edge", sa.Numeric(10, 8), nullable=True),
        sa.Column("confidence_score", sa.Numeric(6, 4), nullable=False),
        sa.Column("result", sa.String(length=40), nullable=True),
        sa.Column("closing_odds", sa.Numeric(10, 4), nullable=True),
        sa.Column("clv", sa.Numeric(10, 8), nullable=True),
        sa.Column("evaluated_at", sa.String(length=40), nullable=True),
        user_id(),
        *id_timestamps(),
        sa.ForeignKeyConstraint(["analysis_id"], ["game_analyses.id"]),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_prediction_records_user_id", "prediction_records", ["user_id"])

    op.create_table(
        "backtest_runs",
        sa.Column("model_version", sa.String(length=40), nullable=False),
        sa.Column("started_at", sa.String(length=40), nullable=False),
        sa.Column("finished_at", sa.String(length=40), nullable=False),
        sa.Column("sample_size", sa.Integer(), nullable=False),
        sa.Column("brier_score", sa.Numeric(10, 8), nullable=False),
        sa.Column("calibration_error", sa.Numeric(10, 8), nullable=False),
        sa.Column("roi_if_flat_bet", sa.Numeric(10, 8), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("buckets_json", sa.Text(), nullable=False),
        user_id(),
        *id_timestamps(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_backtest_runs_user_id", "backtest_runs", ["user_id"])


def downgrade() -> None:
    op.drop_table("backtest_runs")
    op.drop_table("prediction_records")
    op.drop_table("sync_job_runs")
    op.drop_table("data_providers")
