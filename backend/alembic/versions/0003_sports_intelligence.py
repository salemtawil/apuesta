"""Sports intelligence data.

Revision ID: 0003_sports_intelligence
Revises: 0002_import_rows
Create Date: 2026-07-17
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_sports_intelligence"
down_revision: str | None = "0002_import_rows"
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
        "team_stat_snapshots",
        sa.Column("sport_id", sa.String(length=36), nullable=False),
        sa.Column("team_name", sa.String(length=160), nullable=False),
        sa.Column("league_name", sa.String(length=160), nullable=False),
        sa.Column("season", sa.String(length=40), nullable=False),
        sa.Column("sample_label", sa.String(length=80), nullable=False),
        sa.Column("games_played", sa.Integer(), nullable=False),
        sa.Column("wins", sa.Integer(), nullable=False),
        sa.Column("losses", sa.Integer(), nullable=False),
        sa.Column("offensive_rating", sa.Numeric(10, 4), nullable=True),
        sa.Column("defensive_rating", sa.Numeric(10, 4), nullable=True),
        sa.Column("pace", sa.Numeric(10, 4), nullable=True),
        sa.Column("recent_form", sa.Numeric(6, 4), nullable=True),
        sa.Column("home_away_split", sa.String(length=40), nullable=True),
        sa.Column("rest_days", sa.Integer(), nullable=True),
        sa.Column("injury_impact", sa.Numeric(6, 4), nullable=True),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("captured_at", sa.String(length=40), nullable=False),
        sa.Column("raw_payload", sa.Text(), nullable=True),
        user_id(),
        *id_timestamps(),
        sa.ForeignKeyConstraint(["sport_id"], ["sports.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_team_stat_snapshots_user_id", "team_stat_snapshots", ["user_id"])

    op.create_table(
        "injury_reports",
        sa.Column("sport_id", sa.String(length=36), nullable=False),
        sa.Column("team_name", sa.String(length=160), nullable=False),
        sa.Column("player_name", sa.String(length=160), nullable=False),
        sa.Column("status", sa.String(length=80), nullable=False),
        sa.Column("impact_score", sa.Numeric(6, 4), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("captured_at", sa.String(length=40), nullable=False),
        user_id(),
        *id_timestamps(),
        sa.ForeignKeyConstraint(["sport_id"], ["sports.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_injury_reports_user_id", "injury_reports", ["user_id"])

    op.create_table(
        "market_movements",
        sa.Column("event_id", sa.String(length=36), nullable=False),
        sa.Column("sportsbook_id", sa.String(length=36), nullable=False),
        sa.Column("market_type", sa.String(length=80), nullable=False),
        sa.Column("opening_decimal_odds", sa.Numeric(10, 4), nullable=True),
        sa.Column("current_decimal_odds", sa.Numeric(10, 4), nullable=True),
        sa.Column("line_open", sa.Numeric(10, 3), nullable=True),
        sa.Column("line_current", sa.Numeric(10, 3), nullable=True),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("captured_at", sa.String(length=40), nullable=False),
        user_id(),
        *id_timestamps(),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"]),
        sa.ForeignKeyConstraint(["sportsbook_id"], ["sportsbooks.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_market_movements_user_id", "market_movements", ["user_id"])

    op.create_table(
        "game_analyses",
        sa.Column("event_id", sa.String(length=36), nullable=False),
        sa.Column("generated_at", sa.String(length=40), nullable=False),
        sa.Column("model_version", sa.String(length=40), nullable=False),
        sa.Column("estimated_home_probability", sa.Numeric(10, 8), nullable=False),
        sa.Column("estimated_away_probability", sa.Numeric(10, 8), nullable=False),
        sa.Column("fair_home_odds", sa.Numeric(10, 4), nullable=False),
        sa.Column("fair_away_odds", sa.Numeric(10, 4), nullable=False),
        sa.Column("confidence_score", sa.Numeric(6, 4), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("factors_json", sa.Text(), nullable=False),
        sa.Column("risks_json", sa.Text(), nullable=False),
        user_id(),
        *id_timestamps(),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_game_analyses_user_id", "game_analyses", ["user_id"])


def downgrade() -> None:
    op.drop_table("game_analyses")
    op.drop_table("market_movements")
    op.drop_table("injury_reports")
    op.drop_table("team_stat_snapshots")
