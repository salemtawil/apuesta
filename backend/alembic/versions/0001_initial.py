"""Initial MVP schema.

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-15
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
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
        "sports",
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        *id_timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("slug"),
    )
    op.create_table(
        "leagues",
        sa.Column("sport_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("country", sa.String(length=2), nullable=True),
        user_id(),
        *id_timestamps(),
        sa.ForeignKeyConstraint(["sport_id"], ["sports.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "sportsbooks",
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("country", sa.String(length=2), nullable=True),
        user_id(),
        *id_timestamps(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sportsbooks_user_id", "sportsbooks", ["user_id"])
    op.create_table(
        "bankrolls",
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("starting_balance", sa.Numeric(14, 2), nullable=False),
        sa.Column("current_balance", sa.Numeric(14, 2), nullable=False),
        sa.Column("unit_size", sa.Numeric(14, 2), nullable=False),
        sa.Column("max_stake_pct", sa.Numeric(6, 4), nullable=False),
        sa.Column("daily_stop_pct", sa.Numeric(6, 4), nullable=False),
        user_id(),
        *id_timestamps(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_bankrolls_user_id", "bankrolls", ["user_id"])
    op.create_table(
        "events",
        sa.Column("sport_id", sa.String(length=36), nullable=False),
        sa.Column("league_id", sa.String(length=36), nullable=True),
        sa.Column("league_name", sa.String(length=160), nullable=False),
        sa.Column("home_team", sa.String(length=160), nullable=True),
        sa.Column("away_team", sa.String(length=160), nullable=True),
        sa.Column("event_name", sa.String(length=220), nullable=False),
        sa.Column("starts_at", sa.String(length=40), nullable=False),
        sa.Column("timezone", sa.String(length=80), nullable=False),
        sa.Column("venue", sa.String(length=160), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        user_id(),
        *id_timestamps(),
        sa.ForeignKeyConstraint(["sport_id"], ["sports.id"]),
        sa.ForeignKeyConstraint(["league_id"], ["leagues.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_events_user_id", "events", ["user_id"])
    op.create_table(
        "bankroll_transactions",
        sa.Column("bankroll_id", sa.String(length=36), nullable=False),
        sa.Column("transaction_type", sa.String(length=40), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("balance_after", sa.Numeric(14, 2), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        user_id(),
        *id_timestamps(),
        sa.ForeignKeyConstraint(["bankroll_id"], ["bankrolls.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_bankroll_transactions_user_id", "bankroll_transactions", ["user_id"])
    op.create_table(
        "markets",
        sa.Column("event_id", sa.String(length=36), nullable=False),
        sa.Column("market_type", sa.String(length=80), nullable=False),
        sa.Column("period", sa.String(length=80), nullable=True),
        sa.Column("participant", sa.String(length=160), nullable=True),
        sa.Column("line", sa.Numeric(10, 3), nullable=True),
        sa.Column("scope", sa.String(length=80), nullable=True),
        sa.Column("settlement_rules", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        *id_timestamps(),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "market_selections",
        sa.Column("market_id", sa.String(length=36), nullable=False),
        sa.Column("selection_name", sa.String(length=160), nullable=False),
        sa.Column("participant", sa.String(length=160), nullable=True),
        *id_timestamps(),
        sa.ForeignKeyConstraint(["market_id"], ["markets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "odds_snapshots",
        sa.Column("sportsbook_id", sa.String(length=36), nullable=False),
        sa.Column("market_selection_id", sa.String(length=36), nullable=False),
        sa.Column("odds_format", sa.String(length=20), nullable=False),
        sa.Column("decimal_odds", sa.Numeric(10, 4), nullable=False),
        sa.Column("american_odds", sa.Integer(), nullable=True),
        sa.Column("implied_probability", sa.Numeric(10, 8), nullable=False),
        sa.Column("captured_at", sa.String(length=40), nullable=False),
        sa.Column("source", sa.String(length=40), nullable=False),
        sa.Column("is_closing_line", sa.Boolean(), nullable=False),
        sa.Column("raw_payload", sa.Text(), nullable=True),
        user_id(),
        *id_timestamps(),
        sa.ForeignKeyConstraint(["sportsbook_id"], ["sportsbooks.id"]),
        sa.ForeignKeyConstraint(["market_selection_id"], ["market_selections.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_odds_snapshots_user_id", "odds_snapshots", ["user_id"])
    op.create_table(
        "predictions",
        sa.Column("event_id", sa.String(length=36), nullable=False),
        sa.Column("market_selection_id", sa.String(length=36), nullable=False),
        sa.Column("source", sa.String(length=40), nullable=False),
        sa.Column("estimated_probability", sa.Numeric(10, 8), nullable=False),
        sa.Column("lower_bound", sa.Numeric(10, 8), nullable=True),
        sa.Column("upper_bound", sa.Numeric(10, 8), nullable=True),
        sa.Column("confidence_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("generated_at", sa.String(length=40), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        user_id(),
        *id_timestamps(),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"]),
        sa.ForeignKeyConstraint(["market_selection_id"], ["market_selections.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_predictions_user_id", "predictions", ["user_id"])
    op.create_table(
        "bets",
        sa.Column("bankroll_id", sa.String(length=36), nullable=False),
        sa.Column("sportsbook_id", sa.String(length=36), nullable=False),
        sa.Column("bet_type", sa.String(length=20), nullable=False),
        sa.Column("stake", sa.Numeric(14, 2), nullable=False),
        sa.Column("combined_decimal_odds", sa.Numeric(10, 4), nullable=False),
        sa.Column("potential_return", sa.Numeric(14, 2), nullable=False),
        sa.Column("actual_return", sa.Numeric(14, 2), nullable=True),
        sa.Column("profit_loss", sa.Numeric(14, 2), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=40), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        user_id(),
        *id_timestamps(),
        sa.ForeignKeyConstraint(["bankroll_id"], ["bankrolls.id"]),
        sa.ForeignKeyConstraint(["sportsbook_id"], ["sportsbooks.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_bets_user_id", "bets", ["user_id"])
    op.create_table(
        "imports",
        sa.Column("filename", sa.String(length=240), nullable=False),
        sa.Column("import_type", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("error_count", sa.Integer(), nullable=False),
        user_id(),
        *id_timestamps(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_imports_user_id", "imports", ["user_id"])
    op.create_table(
        "attachments",
        sa.Column("filename", sa.String(length=240), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("storage_path", sa.String(length=500), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        user_id(),
        *id_timestamps(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_attachments_user_id", "attachments", ["user_id"])
    op.create_table(
        "value_assessments",
        sa.Column("prediction_id", sa.String(length=36), nullable=False),
        sa.Column("odds_snapshot_id", sa.String(length=36), nullable=False),
        sa.Column("offered_decimal_odds", sa.Numeric(10, 4), nullable=False),
        sa.Column("fair_odds", sa.Numeric(10, 4), nullable=False),
        sa.Column("implied_probability", sa.Numeric(10, 8), nullable=False),
        sa.Column("edge", sa.Numeric(10, 8), nullable=False),
        sa.Column("expected_value", sa.Numeric(10, 8), nullable=False),
        sa.Column("full_kelly_fraction", sa.Numeric(10, 8), nullable=False),
        sa.Column("applied_kelly_fraction", sa.Numeric(10, 8), nullable=False),
        sa.Column("recommended_stake", sa.Numeric(14, 2), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("grade", sa.String(length=20), nullable=False),
        sa.Column("warnings", sa.Text(), nullable=True),
        user_id(),
        *id_timestamps(),
        sa.ForeignKeyConstraint(["prediction_id"], ["predictions.id"]),
        sa.ForeignKeyConstraint(["odds_snapshot_id"], ["odds_snapshots.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_value_assessments_user_id", "value_assessments", ["user_id"])
    op.create_table(
        "bet_legs",
        sa.Column("bet_id", sa.String(length=36), nullable=False),
        sa.Column("event_id", sa.String(length=36), nullable=False),
        sa.Column("market_selection_id", sa.String(length=36), nullable=False),
        sa.Column("odds_at_placement", sa.Numeric(10, 4), nullable=False),
        sa.Column("line_at_placement", sa.Numeric(10, 3), nullable=True),
        sa.Column("estimated_probability_at_placement", sa.Numeric(10, 8), nullable=True),
        sa.Column("fair_odds_at_placement", sa.Numeric(10, 4), nullable=True),
        sa.Column("ev_at_placement", sa.Numeric(10, 8), nullable=True),
        sa.Column("result", sa.String(length=40), nullable=False),
        sa.Column("closing_odds", sa.Numeric(10, 4), nullable=True),
        sa.Column("clv", sa.Numeric(10, 8), nullable=True),
        sa.Column("correlation_group", sa.String(length=80), nullable=True),
        *id_timestamps(),
        sa.ForeignKeyConstraint(["bet_id"], ["bets.id"]),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"]),
        sa.ForeignKeyConstraint(["market_selection_id"], ["market_selections.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "postmortems",
        sa.Column("bet_id", sa.String(length=36), nullable=False),
        sa.Column("analysis_quality", sa.String(length=80), nullable=False),
        sa.Column("result_quality", sa.String(length=80), nullable=True),
        sa.Column("process_followed", sa.Boolean(), nullable=False),
        sa.Column("primary_failure_reason", sa.String(length=120), nullable=True),
        sa.Column("secondary_failure_reason", sa.String(length=120), nullable=True),
        sa.Column("lessons", sa.Text(), nullable=True),
        sa.Column("generated_summary", sa.Text(), nullable=True),
        sa.Column("reviewed_by_user", sa.Boolean(), nullable=False),
        user_id(),
        *id_timestamps(),
        sa.ForeignKeyConstraint(["bet_id"], ["bets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_postmortems_user_id", "postmortems", ["user_id"])


def downgrade() -> None:
    for table in [
        "postmortems",
        "bet_legs",
        "value_assessments",
        "attachments",
        "imports",
        "bets",
        "predictions",
        "odds_snapshots",
        "market_selections",
        "markets",
        "bankroll_transactions",
        "events",
        "bankrolls",
        "sportsbooks",
        "leagues",
        "sports",
    ]:
        op.drop_table(table)
