from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDTimestampMixin


class UserOwnedMixin:
    user_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)


class Sport(Base, UUIDTimestampMixin):
    __tablename__ = "sports"

    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)


class League(Base, UUIDTimestampMixin, UserOwnedMixin):
    __tablename__ = "leagues"

    sport_id: Mapped[str] = mapped_column(ForeignKey("sports.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    country: Mapped[str | None] = mapped_column(String(2))


class Sportsbook(Base, UUIDTimestampMixin, UserOwnedMixin):
    __tablename__ = "sportsbooks"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    country: Mapped[str | None] = mapped_column(String(2))


class Bankroll(Base, UUIDTimestampMixin, UserOwnedMixin):
    __tablename__ = "bankrolls"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    starting_balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    current_balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    unit_size: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    max_stake_pct: Mapped[Decimal] = mapped_column(Numeric(6, 4), default=Decimal("0.0150"), nullable=False)
    daily_stop_pct: Mapped[Decimal] = mapped_column(Numeric(6, 4), default=Decimal("0.0500"), nullable=False)


class BankrollTransaction(Base, UUIDTimestampMixin, UserOwnedMixin):
    __tablename__ = "bankroll_transactions"

    bankroll_id: Mapped[str] = mapped_column(ForeignKey("bankrolls.id"), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(40), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    balance_after: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    note: Mapped[str | None] = mapped_column(Text)


class Event(Base, UUIDTimestampMixin, UserOwnedMixin):
    __tablename__ = "events"

    sport_id: Mapped[str] = mapped_column(ForeignKey("sports.id"), nullable=False)
    league_id: Mapped[str | None] = mapped_column(ForeignKey("leagues.id"))
    league_name: Mapped[str] = mapped_column(String(160), nullable=False)
    home_team: Mapped[str | None] = mapped_column(String(160))
    away_team: Mapped[str | None] = mapped_column(String(160))
    event_name: Mapped[str] = mapped_column(String(220), nullable=False)
    starts_at: Mapped[str] = mapped_column(String(40), nullable=False)
    timezone: Mapped[str] = mapped_column(String(80), default="UTC", nullable=False)
    venue: Mapped[str | None] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(40), default="scheduled", nullable=False)

    markets: Mapped[list[Market]] = relationship(back_populates="event")


class Market(Base, UUIDTimestampMixin):
    __tablename__ = "markets"

    event_id: Mapped[str] = mapped_column(ForeignKey("events.id"), nullable=False)
    market_type: Mapped[str] = mapped_column(String(80), nullable=False)
    period: Mapped[str | None] = mapped_column(String(80))
    participant: Mapped[str | None] = mapped_column(String(160))
    line: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))
    scope: Mapped[str | None] = mapped_column(String(80))
    settlement_rules: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="open", nullable=False)

    event: Mapped[Event] = relationship(back_populates="markets")
    selections: Mapped[list[MarketSelection]] = relationship(back_populates="market")


class MarketSelection(Base, UUIDTimestampMixin):
    __tablename__ = "market_selections"

    market_id: Mapped[str] = mapped_column(ForeignKey("markets.id"), nullable=False)
    selection_name: Mapped[str] = mapped_column(String(160), nullable=False)
    participant: Mapped[str | None] = mapped_column(String(160))

    market: Mapped[Market] = relationship(back_populates="selections")


class OddsSnapshot(Base, UUIDTimestampMixin, UserOwnedMixin):
    __tablename__ = "odds_snapshots"

    sportsbook_id: Mapped[str] = mapped_column(ForeignKey("sportsbooks.id"), nullable=False)
    market_selection_id: Mapped[str] = mapped_column(ForeignKey("market_selections.id"), nullable=False)
    odds_format: Mapped[str] = mapped_column(String(20), default="decimal", nullable=False)
    decimal_odds: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    american_odds: Mapped[int | None] = mapped_column(Integer)
    implied_probability: Mapped[Decimal] = mapped_column(Numeric(10, 8), nullable=False)
    captured_at: Mapped[str] = mapped_column(String(40), nullable=False)
    source: Mapped[str] = mapped_column(String(40), default="manual", nullable=False)
    is_closing_line: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    raw_payload: Mapped[str | None] = mapped_column(Text)


class TeamStatSnapshot(Base, UUIDTimestampMixin, UserOwnedMixin):
    __tablename__ = "team_stat_snapshots"

    sport_id: Mapped[str] = mapped_column(ForeignKey("sports.id"), nullable=False)
    team_name: Mapped[str] = mapped_column(String(160), nullable=False)
    league_name: Mapped[str] = mapped_column(String(160), nullable=False)
    season: Mapped[str] = mapped_column(String(40), nullable=False)
    sample_label: Mapped[str] = mapped_column(String(80), default="season", nullable=False)
    games_played: Mapped[int] = mapped_column(Integer, nullable=False)
    wins: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    losses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    offensive_rating: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    defensive_rating: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    pace: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    recent_form: Mapped[Decimal | None] = mapped_column(Numeric(6, 4))
    home_away_split: Mapped[str | None] = mapped_column(String(40))
    rest_days: Mapped[int | None] = mapped_column(Integer)
    injury_impact: Mapped[Decimal | None] = mapped_column(Numeric(6, 4))
    source: Mapped[str] = mapped_column(String(80), default="manual", nullable=False)
    captured_at: Mapped[str] = mapped_column(String(40), nullable=False)
    raw_payload: Mapped[str | None] = mapped_column(Text)


class InjuryReport(Base, UUIDTimestampMixin, UserOwnedMixin):
    __tablename__ = "injury_reports"

    sport_id: Mapped[str] = mapped_column(ForeignKey("sports.id"), nullable=False)
    team_name: Mapped[str] = mapped_column(String(160), nullable=False)
    player_name: Mapped[str] = mapped_column(String(160), nullable=False)
    status: Mapped[str] = mapped_column(String(80), nullable=False)
    impact_score: Mapped[Decimal] = mapped_column(Numeric(6, 4), default=Decimal("0"), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(80), default="manual", nullable=False)
    captured_at: Mapped[str] = mapped_column(String(40), nullable=False)


class MarketMovement(Base, UUIDTimestampMixin, UserOwnedMixin):
    __tablename__ = "market_movements"

    event_id: Mapped[str] = mapped_column(ForeignKey("events.id"), nullable=False)
    sportsbook_id: Mapped[str] = mapped_column(ForeignKey("sportsbooks.id"), nullable=False)
    market_type: Mapped[str] = mapped_column(String(80), nullable=False)
    opening_decimal_odds: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    current_decimal_odds: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    line_open: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))
    line_current: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))
    source: Mapped[str] = mapped_column(String(80), default="manual", nullable=False)
    captured_at: Mapped[str] = mapped_column(String(40), nullable=False)


class GameAnalysis(Base, UUIDTimestampMixin, UserOwnedMixin):
    __tablename__ = "game_analyses"

    event_id: Mapped[str] = mapped_column(ForeignKey("events.id"), nullable=False)
    generated_at: Mapped[str] = mapped_column(String(40), nullable=False)
    model_version: Mapped[str] = mapped_column(String(40), nullable=False)
    estimated_home_probability: Mapped[Decimal] = mapped_column(Numeric(10, 8), nullable=False)
    estimated_away_probability: Mapped[Decimal] = mapped_column(Numeric(10, 8), nullable=False)
    fair_home_odds: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    fair_away_odds: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    factors_json: Mapped[str] = mapped_column(Text, nullable=False)
    risks_json: Mapped[str] = mapped_column(Text, nullable=False)


class DataProvider(Base, UUIDTimestampMixin, UserOwnedMixin):
    __tablename__ = "data_providers"

    provider_key: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    sport_slug: Mapped[str | None] = mapped_column(String(80))
    base_url: Mapped[str | None] = mapped_column(String(500))
    api_key_env: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(40), default="configured", nullable=False)
    last_sync_at: Mapped[str | None] = mapped_column(String(40))
    notes: Mapped[str | None] = mapped_column(Text)


class SyncJobRun(Base, UUIDTimestampMixin, UserOwnedMixin):
    __tablename__ = "sync_job_runs"

    provider_key: Mapped[str] = mapped_column(String(80), nullable=False)
    job_type: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    started_at: Mapped[str] = mapped_column(String(40), nullable=False)
    finished_at: Mapped[str | None] = mapped_column(String(40))
    records_upserted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)


class PredictionRecord(Base, UUIDTimestampMixin, UserOwnedMixin):
    __tablename__ = "prediction_records"

    event_id: Mapped[str] = mapped_column(ForeignKey("events.id"), nullable=False)
    analysis_id: Mapped[str | None] = mapped_column(ForeignKey("game_analyses.id"))
    market_type: Mapped[str] = mapped_column(String(80), nullable=False)
    selection_name: Mapped[str] = mapped_column(String(160), nullable=False)
    estimated_probability: Mapped[Decimal] = mapped_column(Numeric(10, 8), nullable=False)
    fair_odds: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    offered_odds: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    edge: Mapped[Decimal | None] = mapped_column(Numeric(10, 8))
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    result: Mapped[str | None] = mapped_column(String(40))
    closing_odds: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    clv: Mapped[Decimal | None] = mapped_column(Numeric(10, 8))
    evaluated_at: Mapped[str | None] = mapped_column(String(40))


class BacktestRun(Base, UUIDTimestampMixin, UserOwnedMixin):
    __tablename__ = "backtest_runs"

    model_version: Mapped[str] = mapped_column(String(40), nullable=False)
    started_at: Mapped[str] = mapped_column(String(40), nullable=False)
    finished_at: Mapped[str] = mapped_column(String(40), nullable=False)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False)
    brier_score: Mapped[Decimal] = mapped_column(Numeric(10, 8), nullable=False)
    calibration_error: Mapped[Decimal] = mapped_column(Numeric(10, 8), nullable=False)
    roi_if_flat_bet: Mapped[Decimal] = mapped_column(Numeric(10, 8), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    buckets_json: Mapped[str] = mapped_column(Text, nullable=False)


class Prediction(Base, UUIDTimestampMixin, UserOwnedMixin):
    __tablename__ = "predictions"

    event_id: Mapped[str] = mapped_column(ForeignKey("events.id"), nullable=False)
    market_selection_id: Mapped[str] = mapped_column(ForeignKey("market_selections.id"), nullable=False)
    source: Mapped[str] = mapped_column(String(40), default="manual", nullable=False)
    estimated_probability: Mapped[Decimal] = mapped_column(Numeric(10, 8), nullable=False)
    lower_bound: Mapped[Decimal | None] = mapped_column(Numeric(10, 8))
    upper_bound: Mapped[Decimal | None] = mapped_column(Numeric(10, 8))
    confidence_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    generated_at: Mapped[str] = mapped_column(String(40), nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text)


class ValueAssessment(Base, UUIDTimestampMixin, UserOwnedMixin):
    __tablename__ = "value_assessments"

    prediction_id: Mapped[str] = mapped_column(ForeignKey("predictions.id"), nullable=False)
    odds_snapshot_id: Mapped[str] = mapped_column(ForeignKey("odds_snapshots.id"), nullable=False)
    offered_decimal_odds: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    fair_odds: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    implied_probability: Mapped[Decimal] = mapped_column(Numeric(10, 8), nullable=False)
    edge: Mapped[Decimal] = mapped_column(Numeric(10, 8), nullable=False)
    expected_value: Mapped[Decimal] = mapped_column(Numeric(10, 8), nullable=False)
    full_kelly_fraction: Mapped[Decimal] = mapped_column(Numeric(10, 8), nullable=False)
    applied_kelly_fraction: Mapped[Decimal] = mapped_column(Numeric(10, 8), nullable=False)
    recommended_stake: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    grade: Mapped[str] = mapped_column(String(20), nullable=False)
    warnings: Mapped[str | None] = mapped_column(Text)


class Bet(Base, UUIDTimestampMixin, UserOwnedMixin):
    __tablename__ = "bets"

    bankroll_id: Mapped[str] = mapped_column(ForeignKey("bankrolls.id"), nullable=False)
    sportsbook_id: Mapped[str] = mapped_column(ForeignKey("sportsbooks.id"), nullable=False)
    bet_type: Mapped[str] = mapped_column(String(20), nullable=False)
    stake: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    combined_decimal_odds: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    potential_return: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    actual_return: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    profit_loss: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    status: Mapped[str] = mapped_column(String(40), default="open", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(40), default="manual", nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    legs: Mapped[list[BetLeg]] = relationship(back_populates="bet")


class BetLeg(Base, UUIDTimestampMixin):
    __tablename__ = "bet_legs"

    bet_id: Mapped[str] = mapped_column(ForeignKey("bets.id"), nullable=False)
    event_id: Mapped[str] = mapped_column(ForeignKey("events.id"), nullable=False)
    market_selection_id: Mapped[str] = mapped_column(ForeignKey("market_selections.id"), nullable=False)
    odds_at_placement: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    line_at_placement: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))
    estimated_probability_at_placement: Mapped[Decimal | None] = mapped_column(Numeric(10, 8))
    fair_odds_at_placement: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    ev_at_placement: Mapped[Decimal | None] = mapped_column(Numeric(10, 8))
    result: Mapped[str] = mapped_column(String(40), default="pending", nullable=False)
    closing_odds: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    clv: Mapped[Decimal | None] = mapped_column(Numeric(10, 8))
    correlation_group: Mapped[str | None] = mapped_column(String(80))

    bet: Mapped[Bet] = relationship(back_populates="legs")


class ImportBatch(Base, UUIDTimestampMixin, UserOwnedMixin):
    __tablename__ = "imports"

    filename: Mapped[str] = mapped_column(String(240), nullable=False)
    import_type: Mapped[str] = mapped_column(String(40), default="csv", nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="validated", nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class ImportRow(Base, UUIDTimestampMixin, UserOwnedMixin):
    __tablename__ = "import_rows"

    import_id: Mapped[str] = mapped_column(ForeignKey("imports.id"), nullable=False)
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="pending_review", nullable=False)
    sport: Mapped[str | None] = mapped_column(String(80))
    league: Mapped[str | None] = mapped_column(String(160))
    event: Mapped[str | None] = mapped_column(String(220))
    home_team: Mapped[str | None] = mapped_column(String(160))
    away_team: Mapped[str | None] = mapped_column(String(160))
    starts_at: Mapped[str | None] = mapped_column(String(40))
    market_type: Mapped[str | None] = mapped_column(String(80))
    selection: Mapped[str | None] = mapped_column(String(160))
    line: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))
    odds: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    odds_format: Mapped[str | None] = mapped_column(String(20))
    sportsbook: Mapped[str | None] = mapped_column(String(120))
    captured_at: Mapped[str | None] = mapped_column(String(40))
    raw_payload: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_event_id: Mapped[str | None] = mapped_column(String(36))
    created_market_id: Mapped[str | None] = mapped_column(String(36))
    created_odds_snapshot_id: Mapped[str | None] = mapped_column(String(36))


class Attachment(Base, UUIDTimestampMixin, UserOwnedMixin):
    __tablename__ = "attachments"

    filename: Mapped[str] = mapped_column(String(240), nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="received", nullable=False)


class Postmortem(Base, UUIDTimestampMixin, UserOwnedMixin):
    __tablename__ = "postmortems"

    bet_id: Mapped[str] = mapped_column(ForeignKey("bets.id"), nullable=False)
    analysis_quality: Mapped[str] = mapped_column(String(80), nullable=False)
    result_quality: Mapped[str | None] = mapped_column(String(80))
    process_followed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    primary_failure_reason: Mapped[str | None] = mapped_column(String(120))
    secondary_failure_reason: Mapped[str | None] = mapped_column(String(120))
    lessons: Mapped[str | None] = mapped_column(Text)
    generated_summary: Mapped[str | None] = mapped_column(Text)
    reviewed_by_user: Mapped[bool] = mapped_column(default=False, nullable=False)
