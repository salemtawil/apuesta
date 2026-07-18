from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field


class SportRead(BaseModel):
    id: str
    name: str
    slug: str

    model_config = {"from_attributes": True}


class SportsbookCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    country: str | None = Field(default=None, max_length=2)


class SportsbookRead(SportsbookCreate):
    id: str

    model_config = {"from_attributes": True}


class BankrollCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    starting_balance: Decimal = Field(gt=0)
    unit_size: Decimal | None = Field(default=None, gt=0)
    max_stake_pct: Decimal = Field(default=Decimal("0.0150"), gt=0, le=1)
    daily_stop_pct: Decimal = Field(default=Decimal("0.0500"), gt=0, le=1)


class BankrollRead(BaseModel):
    id: str
    name: str
    currency: str
    starting_balance: Decimal
    current_balance: Decimal
    unit_size: Decimal
    max_stake_pct: Decimal
    daily_stop_pct: Decimal

    model_config = {"from_attributes": True}


class BankrollTransactionCreate(BaseModel):
    bankroll_id: str
    transaction_type: str = Field(pattern="^(deposit|withdrawal|adjustment)$")
    amount: Decimal
    note: str | None = None


class BankrollTransactionRead(BaseModel):
    id: str
    bankroll_id: str
    transaction_type: str
    amount: Decimal
    balance_after: Decimal
    note: str | None

    model_config = {"from_attributes": True}


class SportsbookExposure(BaseModel):
    sportsbook_id: str
    sportsbook_name: str
    open_bets: int
    settled_bets: int
    open_exposure: Decimal
    total_staked: Decimal
    profit_loss: Decimal
    roi: Decimal


class RiskAlert(BaseModel):
    severity: str
    code: str
    message: str


class BankrollControlRead(BaseModel):
    bankrolls: list[BankrollRead]
    transactions: list[BankrollTransactionRead]
    exposures: list[SportsbookExposure]
    alerts: list[RiskAlert]


class EventCreate(BaseModel):
    sport_id: str
    league_name: str = Field(min_length=1, max_length=160)
    home_team: str | None = Field(default=None, max_length=160)
    away_team: str | None = Field(default=None, max_length=160)
    event_name: str = Field(min_length=1, max_length=220)
    starts_at: str
    timezone: str = "UTC"
    venue: str | None = None


class EventRead(EventCreate):
    id: str
    status: str

    model_config = {"from_attributes": True}


class MarketCreate(BaseModel):
    event_id: str
    market_type: str = Field(min_length=1, max_length=80)
    selection_name: str = Field(min_length=1, max_length=160)
    period: str | None = None
    participant: str | None = None
    line: Decimal | None = None
    scope: str | None = None
    settlement_rules: str | None = None


class MarketSelectionRead(BaseModel):
    id: str
    market_id: str
    selection_name: str
    participant: str | None

    model_config = {"from_attributes": True}


class MarketRead(BaseModel):
    id: str
    event_id: str
    market_type: str
    period: str | None
    participant: str | None
    line: Decimal | None
    status: str
    selection: MarketSelectionRead


class OddsCreate(BaseModel):
    sportsbook_id: str
    market_selection_id: str
    decimal_odds: Decimal = Field(gt=1)
    odds_format: str = "decimal"
    captured_at: str
    source: str = "manual"
    is_closing_line: bool = False
    raw_payload: str | None = None


class OddsRead(BaseModel):
    id: str
    sportsbook_id: str
    market_selection_id: str
    decimal_odds: Decimal
    american_odds: int | None
    implied_probability: Decimal
    captured_at: str
    source: str
    is_closing_line: bool

    model_config = {"from_attributes": True}


class TeamStatCreate(BaseModel):
    sport_id: str
    team_name: str = Field(min_length=1, max_length=160)
    league_name: str = Field(min_length=1, max_length=160)
    season: str = Field(min_length=1, max_length=40)
    sample_label: str = "season"
    games_played: int = Field(ge=0)
    wins: int = Field(default=0, ge=0)
    losses: int = Field(default=0, ge=0)
    offensive_rating: Decimal | None = None
    defensive_rating: Decimal | None = None
    pace: Decimal | None = None
    recent_form: Decimal | None = Field(default=None, ge=0, le=1)
    home_away_split: str | None = None
    rest_days: int | None = Field(default=None, ge=0)
    injury_impact: Decimal | None = Field(default=None, ge=0, le=1)
    source: str = "manual"
    captured_at: str
    raw_payload: str | None = None


class TeamStatRead(TeamStatCreate):
    id: str

    model_config = {"from_attributes": True}


class InjuryReportCreate(BaseModel):
    sport_id: str
    team_name: str
    player_name: str
    status: str
    impact_score: Decimal = Field(default=Decimal("0"), ge=0, le=1)
    notes: str | None = None
    source: str = "manual"
    captured_at: str


class InjuryReportRead(InjuryReportCreate):
    id: str

    model_config = {"from_attributes": True}


class MarketMovementCreate(BaseModel):
    event_id: str
    sportsbook_id: str
    market_type: str
    opening_decimal_odds: Decimal | None = Field(default=None, gt=1)
    current_decimal_odds: Decimal | None = Field(default=None, gt=1)
    line_open: Decimal | None = None
    line_current: Decimal | None = None
    source: str = "manual"
    captured_at: str


class MarketMovementRead(MarketMovementCreate):
    id: str

    model_config = {"from_attributes": True}


class GameAnalysisRequest(BaseModel):
    event_id: str
    home_team_stat_id: str | None = None
    away_team_stat_id: str | None = None
    offered_home_odds: Decimal | None = Field(default=None, gt=1)
    offered_away_odds: Decimal | None = Field(default=None, gt=1)


class GameFactor(BaseModel):
    label: str
    direction: str
    impact: Decimal
    detail: str


class GameAnalysisRead(BaseModel):
    id: str
    event_id: str
    generated_at: str
    model_version: str
    estimated_home_probability: Decimal
    estimated_away_probability: Decimal
    fair_home_odds: Decimal
    fair_away_odds: Decimal
    confidence_score: Decimal
    summary: str
    factors: list[GameFactor]
    risks: list[str]
    home_edge: Decimal | None = None
    away_edge: Decimal | None = None


class DataProviderCreate(BaseModel):
    provider_key: str
    name: str
    sport_slug: str | None = None
    base_url: str | None = None
    api_key_env: str | None = None
    status: str = "configured"
    notes: str | None = None


class DataProviderRead(DataProviderCreate):
    id: str
    last_sync_at: str | None

    model_config = {"from_attributes": True}


class SyncJobRunRead(BaseModel):
    id: str
    provider_key: str
    job_type: str
    status: str
    started_at: str
    finished_at: str | None
    records_upserted: int
    error_message: str | None

    model_config = {"from_attributes": True}


class TheOddsSyncRequest(BaseModel):
    sport_keys: list[str] = Field(default_factory=lambda: ["baseball_mlb"])
    regions: str = "us"
    markets: list[str] = Field(default_factory=lambda: ["h2h", "spreads", "totals"])


class TheOddsEventMarketsRequest(BaseModel):
    event_id: str
    sport_key: str | None = None
    provider_event_id: str | None = None
    league_name: str | None = None
    home_team: str | None = None
    away_team: str | None = None
    event_name: str | None = None
    starts_at: str | None = None
    regions: str = "us"
    markets: list[str] = Field(default_factory=lambda: ["h2h", "spreads", "totals"])


class TheOddsEventsRequest(BaseModel):
    sport_keys: list[str] = Field(default_factory=lambda: ["baseball_mlb"])


class TheOddsEventsResponse(BaseModel):
    job: SyncJobRunRead
    sports_seen: int
    events_upserted: int
    requests_used: str | None
    requests_remaining: str | None
    errors: list[str]


class TheOddsSyncResponse(BaseModel):
    job: SyncJobRunRead
    sports_seen: int
    events_upserted: int
    markets_upserted: int
    odds_inserted: int
    sportsbooks_upserted: int
    requests_used: str | None
    requests_remaining: str | None
    errors: list[str]


class PredictionRecordRead(BaseModel):
    id: str
    event_id: str
    analysis_id: str | None
    market_type: str
    selection_name: str
    estimated_probability: Decimal
    fair_odds: Decimal
    offered_odds: Decimal | None
    edge: Decimal | None
    confidence_score: Decimal
    result: str | None
    closing_odds: Decimal | None
    clv: Decimal | None
    evaluated_at: str | None

    model_config = {"from_attributes": True}


class PredictionResultUpdate(BaseModel):
    result: str = Field(pattern="^(win|loss|void)$")
    closing_odds: Decimal | None = Field(default=None, gt=1)


class BacktestBucket(BaseModel):
    bucket: str
    predictions: int
    average_probability: Decimal
    actual_win_rate: Decimal
    calibration_error: Decimal


class BacktestRunRead(BaseModel):
    id: str
    model_version: str
    started_at: str
    finished_at: str
    sample_size: int
    brier_score: Decimal
    calibration_error: Decimal
    roi_if_flat_bet: Decimal
    summary: str
    buckets: list[BacktestBucket]


class StoredAssessmentCreate(BaseModel):
    event_id: str
    market_selection_id: str
    odds_snapshot_id: str
    estimated_probability: Decimal = Field(gt=0, le=1)
    bankroll_id: str
    source: str = "manual"
    generated_at: str
    explanation: str | None = None


class StoredAssessmentRead(BaseModel):
    prediction_id: str
    value_assessment_id: str
    grade: str
    score: int
    expected_value: Decimal
    edge: Decimal
    recommended_stake: Decimal
    warnings: list[str]


class BetLegCreate(BaseModel):
    event_id: str
    market_selection_id: str
    odds_at_placement: Decimal = Field(gt=1)
    line_at_placement: Decimal | None = None
    estimated_probability_at_placement: Decimal | None = Field(default=None, gt=0, le=1)
    fair_odds_at_placement: Decimal | None = None
    ev_at_placement: Decimal | None = None
    correlation_group: str | None = None


class BetCreate(BaseModel):
    bankroll_id: str
    sportsbook_id: str
    bet_type: str = Field(pattern="^(single|parlay)$")
    stake: Decimal = Field(gt=0)
    notes: str | None = None
    currency: str = Field(default="USD", min_length=3, max_length=3)
    legs: list[BetLegCreate] = Field(min_length=1)


class BetRead(BaseModel):
    id: str
    bankroll_id: str
    sportsbook_id: str
    bet_type: str
    stake: Decimal
    combined_decimal_odds: Decimal
    potential_return: Decimal
    actual_return: Decimal | None
    profit_loss: Decimal | None
    status: str
    currency: str

    model_config = {"from_attributes": True}


class BetLegDetail(BaseModel):
    id: str
    event_id: str
    event_name: str
    league_name: str
    market_selection_id: str
    market_type: str
    selection_name: str
    odds_at_placement: Decimal
    line_at_placement: Decimal | None
    estimated_probability_at_placement: Decimal | None
    fair_odds_at_placement: Decimal | None
    ev_at_placement: Decimal | None
    result: str


class BetDetailRead(BetRead):
    bankroll_name: str
    sportsbook_name: str
    notes: str | None
    source: str
    created_at: str
    updated_at: str
    legs: list[BetLegDetail]
    postmortems: list[PostmortemRead]


class BetSettleRequest(BaseModel):
    result: str


class PostmortemCreate(BaseModel):
    bet_id: str
    analysis_quality: str
    result_quality: str | None = None
    process_followed: bool = False
    primary_failure_reason: str | None = None
    secondary_failure_reason: str | None = None
    lessons: str | None = None
    generated_summary: str | None = None
    reviewed_by_user: bool = False


class PostmortemRead(PostmortemCreate):
    id: str

    model_config = {"from_attributes": True}


class DashboardRead(BaseModel):
    bankroll_count: int
    bankroll_balance: Decimal
    total_staked: Decimal
    settled_profit_loss: Decimal
    roi: Decimal
    yield_value: Decimal
    open_bets: int
    exposure: Decimal


class AnalyticsBucket(BaseModel):
    label: str
    bets: int
    stake: Decimal
    profit_loss: Decimal
    roi: Decimal


class AnalyticsSummary(BaseModel):
    total_bets: int
    open_bets: int
    settled_bets: int
    total_staked: Decimal
    profit_loss: Decimal
    roi: Decimal
    yield_value: Decimal
    by_status: list[AnalyticsBucket]
    by_bet_type: list[AnalyticsBucket]


class ImportRowRead(BaseModel):
    id: str
    import_id: str
    row_number: int
    status: str
    sport: str | None
    league: str | None
    event: str | None
    home_team: str | None
    away_team: str | None
    starts_at: str | None
    market_type: str | None
    selection: str | None
    line: Decimal | None
    odds: Decimal | None
    odds_format: str | None
    sportsbook: str | None
    captured_at: str | None
    error_message: str | None
    created_event_id: str | None
    created_market_id: str | None
    created_odds_snapshot_id: str | None

    model_config = {"from_attributes": True}


class ImportRowUpdate(BaseModel):
    sport: str | None = None
    league: str | None = None
    event: str | None = None
    home_team: str | None = None
    away_team: str | None = None
    starts_at: str | None = None
    market_type: str | None = None
    selection: str | None = None
    line: Decimal | None = None
    odds: Decimal | None = None
    odds_format: str | None = None
    sportsbook: str | None = None
    captured_at: str | None = None


class ImportConfirmResponse(BaseModel):
    row: ImportRowRead
    event_id: str
    market_id: str
    odds_snapshot_id: str
