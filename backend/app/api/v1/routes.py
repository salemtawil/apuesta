import csv
import json
from datetime import UTC, datetime
from decimal import Decimal
from io import StringIO

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import current_user_id
from app.db.seeds import seed_demo_data
from app.db.session import get_db
from app.models import (
    Attachment,
    BacktestRun,
    Bankroll,
    BankrollTransaction,
    Bet,
    BetLeg,
    DataProvider,
    Event,
    GameAnalysis,
    ImportBatch,
    ImportRow,
    InjuryReport,
    Market,
    MarketMovement,
    MarketSelection,
    OddsSnapshot,
    Postmortem,
    Prediction,
    PredictionRecord,
    Sport,
    Sportsbook,
    SyncJobRun,
    TeamStatSnapshot,
    ValueAssessment,
)
from app.schemas.mvp import (
    AnalyticsBucket,
    AnalyticsSummary,
    BacktestRunRead,
    BankrollControlRead,
    BankrollCreate,
    BankrollRead,
    BankrollTransactionCreate,
    BankrollTransactionRead,
    BetCreate,
    BetDetailRead,
    BetLegDetail,
    BetRead,
    BetSettleRequest,
    DashboardRead,
    DataProviderCreate,
    DataProviderRead,
    EventCreate,
    EventRead,
    GameAnalysisRead,
    GameAnalysisRequest,
    ImportConfirmResponse,
    ImportRowRead,
    ImportRowUpdate,
    InjuryReportCreate,
    InjuryReportRead,
    MarketCreate,
    MarketMovementCreate,
    MarketMovementRead,
    MarketRead,
    OddsCreate,
    OddsRead,
    PostmortemCreate,
    PostmortemRead,
    PredictionRecordRead,
    PredictionResultUpdate,
    RiskAlert,
    SportRead,
    SportsbookCreate,
    SportsbookExposure,
    SportsbookRead,
    StoredAssessmentCreate,
    StoredAssessmentRead,
    SyncJobRunRead,
    TeamStatCreate,
    TeamStatRead,
    TheOddsEventsRequest,
    TheOddsEventsResponse,
    TheOddsSyncRequest,
    TheOddsSyncResponse,
)
from app.services.backtesting import run_backtest
from app.services.betalpha import BetAlphaAssessment, BetAlphaInput, assess_value
from app.services.correlation import CorrelationResult, TicketLeg, assess_correlation
from app.services.odds import (
    american_to_decimal,
    decimal_to_american,
    decimal_to_fractional,
    expected_value,
    fair_odds,
    implied_probability,
    parlay_decimal_odds,
    quantize_money,
)
from app.services.settlement import profit_loss, settle_single
from app.services.sports_intelligence import analyze_matchup
from app.services.the_odds_api import discover_the_odds_events, sync_the_odds

router = APIRouter()


class OddsConversionRequest(BaseModel):
    decimal_odds: Decimal = Field(gt=1)


class AmericanConversionRequest(BaseModel):
    american_odds: int


class TicketRequest(BaseModel):
    stake: Decimal = Field(gt=0)
    legs: list[TicketLeg]
    decimal_odds: list[Decimal]
    probabilities: list[Decimal] = Field(default_factory=list)
    joint_probability: Decimal | None = None


class TicketResponse(BaseModel):
    combined_decimal_odds: Decimal
    implied_probability: Decimal
    potential_return: Decimal
    potential_profit: Decimal
    correlation: CorrelationResult


class SettlementRequest(BaseModel):
    stake: Decimal = Field(gt=0)
    decimal_odds: Decimal = Field(gt=1)
    result: str


def utc_now_text() -> str:
    return datetime.now(UTC).isoformat()


def require_user_owned(db: Session, model: type, object_id: str, user_id: str):
    item = db.get(model, object_id)
    if item is None or getattr(item, "user_id", None) != user_id:
        raise HTTPException(status_code=404, detail="Resource not found")
    return item


def market_to_read(db: Session, market: Market) -> MarketRead:
    selection = db.scalar(select(MarketSelection).where(MarketSelection.market_id == market.id))
    if selection is None:
        raise HTTPException(status_code=500, detail="Market selection missing")
    return MarketRead(
        id=market.id,
        event_id=market.event_id,
        market_type=market.market_type,
        period=market.period,
        participant=market.participant,
        line=market.line,
        status=market.status,
        selection=selection,
    )


def slugify(value: str) -> str:
    return value.strip().lower().replace("/", "-").replace(" ", "-")


def parse_decimal(value: str | None) -> Decimal | None:
    if value is None or value.strip() == "":
        return None
    return Decimal(value.strip())


def row_value(row: dict[str, str], key: str) -> str | None:
    value = row.get(key)
    return value.strip() if value and value.strip() else None


def validate_import_row(row: ImportRow) -> str | None:
    missing = []
    fields = ["sport", "league", "event", "market_type", "selection", "odds", "sportsbook", "captured_at"]
    for field in fields:
        if getattr(row, field) in (None, ""):
            missing.append(field)
    if row.odds is not None and row.odds <= 1:
        missing.append("odds_gt_1")
    return ", ".join(missing) if missing else None


def analytics_bucket(label: str, bets: list[Bet]) -> AnalyticsBucket:
    stake = sum((bet.stake for bet in bets), Decimal("0"))
    pnl = sum((bet.profit_loss or Decimal("0") for bet in bets), Decimal("0"))
    roi = pnl / stake if stake else Decimal("0")
    return AnalyticsBucket(label=label, bets=len(bets), stake=stake, profit_loss=pnl, roi=roi)


def signed_transaction_amount(transaction_type: str, amount: Decimal) -> Decimal:
    if amount == 0:
        raise HTTPException(status_code=422, detail="Amount cannot be zero")
    if transaction_type == "withdrawal":
        return -abs(amount)
    if transaction_type == "deposit":
        return abs(amount)
    return amount


def sportsbook_exposures(db: Session, user_id: str) -> list[SportsbookExposure]:
    books = list(db.scalars(select(Sportsbook).where(Sportsbook.user_id == user_id).order_by(Sportsbook.name)).all())
    bets = list(db.scalars(select(Bet).where(Bet.user_id == user_id)).all())
    exposures = []
    for book in books:
        book_bets = [bet for bet in bets if bet.sportsbook_id == book.id]
        stake = sum((bet.stake for bet in book_bets), Decimal("0"))
        pnl = sum((bet.profit_loss or Decimal("0") for bet in book_bets), Decimal("0"))
        open_bets = [bet for bet in book_bets if bet.status == "open"]
        roi = pnl / stake if stake else Decimal("0")
        exposures.append(
            SportsbookExposure(
                sportsbook_id=book.id,
                sportsbook_name=book.name,
                open_bets=len(open_bets),
                settled_bets=sum(1 for bet in book_bets if bet.status != "open"),
                open_exposure=sum((bet.stake for bet in open_bets), Decimal("0")),
                total_staked=stake,
                profit_loss=pnl,
                roi=roi,
            )
        )
    return exposures


def bankroll_risk_alerts(db: Session, user_id: str) -> list[RiskAlert]:
    alerts = []
    bankrolls = list(db.scalars(select(Bankroll).where(Bankroll.user_id == user_id)).all())
    bets = list(db.scalars(select(Bet).where(Bet.user_id == user_id).order_by(Bet.created_at.desc())).all())
    for bankroll in bankrolls:
        bankroll_bets = [bet for bet in bets if bet.bankroll_id == bankroll.id]
        open_exposure = sum((bet.stake for bet in bankroll_bets if bet.status == "open"), Decimal("0"))
        max_open_exposure = bankroll.current_balance * bankroll.daily_stop_pct
        if open_exposure > max_open_exposure:
            alerts.append(
                RiskAlert(
                    severity="high",
                    code="open_exposure_limit",
                    message=f"{bankroll.name}: exposicion abierta {open_exposure} supera limite {max_open_exposure:.2f}.",
                )
            )
        max_stake = bankroll.current_balance * bankroll.max_stake_pct
        for bet in bankroll_bets:
            if bet.status == "open" and bet.stake > max_stake:
                alerts.append(
                    RiskAlert(
                        severity="medium",
                        code="stake_over_limit",
                        message=f"{bankroll.name}: apuesta {bet.id} excede stake maximo sugerido {max_stake:.2f}.",
                    )
                )
        recent_settled = [bet for bet in bankroll_bets if bet.status != "open"][:3]
        if len(recent_settled) == 3 and all((bet.profit_loss or Decimal("0")) < 0 for bet in recent_settled):
            alerts.append(
                RiskAlert(
                    severity="medium",
                    code="losing_streak",
                    message=f"{bankroll.name}: tres resultados negativos consecutivos.",
                )
            )
    return alerts


def parse_datetime_filter(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid datetime filter: {value}") from exc


def bet_to_detail(db: Session, bet: Bet, user_id: str) -> BetDetailRead:
    bankroll = require_user_owned(db, Bankroll, bet.bankroll_id, user_id)
    sportsbook = require_user_owned(db, Sportsbook, bet.sportsbook_id, user_id)
    legs = list(db.scalars(select(BetLeg).where(BetLeg.bet_id == bet.id)).all())
    leg_details = []
    for leg in legs:
        event = require_user_owned(db, Event, leg.event_id, user_id)
        selection = db.get(MarketSelection, leg.market_selection_id)
        if selection is None:
            raise HTTPException(status_code=500, detail="Bet leg selection missing")
        market = db.get(Market, selection.market_id)
        if market is None:
            raise HTTPException(status_code=500, detail="Bet leg market missing")
        leg_details.append(
            BetLegDetail(
                id=leg.id,
                event_id=event.id,
                event_name=event.event_name,
                league_name=event.league_name,
                market_selection_id=selection.id,
                market_type=market.market_type,
                selection_name=selection.selection_name,
                odds_at_placement=leg.odds_at_placement,
                line_at_placement=leg.line_at_placement,
                estimated_probability_at_placement=leg.estimated_probability_at_placement,
                fair_odds_at_placement=leg.fair_odds_at_placement,
                ev_at_placement=leg.ev_at_placement,
                result=leg.result,
            )
        )
    postmortems = list(
        db.scalars(
            select(Postmortem).where(Postmortem.user_id == user_id, Postmortem.bet_id == bet.id).order_by(Postmortem.created_at.desc())
        ).all()
    )
    return BetDetailRead(
        id=bet.id,
        bankroll_id=bet.bankroll_id,
        sportsbook_id=bet.sportsbook_id,
        bet_type=bet.bet_type,
        stake=bet.stake,
        combined_decimal_odds=bet.combined_decimal_odds,
        potential_return=bet.potential_return,
        actual_return=bet.actual_return,
        profit_loss=bet.profit_loss,
        status=bet.status,
        currency=bet.currency,
        bankroll_name=bankroll.name,
        sportsbook_name=sportsbook.name,
        notes=bet.notes,
        source=bet.source,
        created_at=bet.created_at.isoformat(),
        updated_at=bet.updated_at.isoformat(),
        legs=leg_details,
        postmortems=postmortems,
    )


def analysis_to_read(analysis: GameAnalysis, home_edge: Decimal | None = None, away_edge: Decimal | None = None) -> GameAnalysisRead:
    return GameAnalysisRead(
        id=analysis.id,
        event_id=analysis.event_id,
        generated_at=analysis.generated_at,
        model_version=analysis.model_version,
        estimated_home_probability=analysis.estimated_home_probability,
        estimated_away_probability=analysis.estimated_away_probability,
        fair_home_odds=analysis.fair_home_odds,
        fair_away_odds=analysis.fair_away_odds,
        confidence_score=analysis.confidence_score,
        summary=analysis.summary,
        factors=json.loads(analysis.factors_json),
        risks=json.loads(analysis.risks_json),
        home_edge=home_edge,
        away_edge=away_edge,
    )


def backtest_to_read(run: BacktestRun) -> BacktestRunRead:
    return BacktestRunRead(
        id=run.id,
        model_version=run.model_version,
        started_at=run.started_at,
        finished_at=run.finished_at,
        sample_size=run.sample_size,
        brier_score=run.brier_score,
        calibration_error=run.calibration_error,
        roi_if_flat_bet=run.roi_if_flat_bet,
        summary=run.summary,
        buckets=json.loads(run.buckets_json),
    )


def latest_team_stat(
    db: Session,
    user_id: str,
    sport_id: str,
    team_name: str | None,
) -> TeamStatSnapshot | None:
    if not team_name:
        return None
    return db.scalar(
        select(TeamStatSnapshot)
        .where(
            TeamStatSnapshot.user_id == user_id,
            TeamStatSnapshot.sport_id == sport_id,
            TeamStatSnapshot.team_name == team_name,
        )
        .order_by(TeamStatSnapshot.created_at.desc())
    )


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "betalpha-api"}


@router.get("/me")
def me(user_id: str = Depends(current_user_id)) -> dict[str, str]:
    return {"user_id": user_id}


@router.post("/odds/decimal")
def convert_decimal(payload: OddsConversionRequest) -> dict[str, Decimal | int | str]:
    return {
        "decimal_odds": payload.decimal_odds,
        "american_odds": decimal_to_american(payload.decimal_odds),
        "fractional_odds": decimal_to_fractional(payload.decimal_odds),
        "implied_probability": implied_probability(payload.decimal_odds),
    }


@router.post("/odds/american")
def convert_american(payload: AmericanConversionRequest) -> dict[str, Decimal]:
    decimal = american_to_decimal(payload.american_odds)
    return {"decimal_odds": decimal, "implied_probability": implied_probability(decimal)}


@router.post("/assessments", response_model=BetAlphaAssessment)
def create_assessment(payload: BetAlphaInput) -> BetAlphaAssessment:
    return assess_value(payload)


@router.post("/assessments/stored", response_model=StoredAssessmentRead)
def create_stored_assessment(
    payload: StoredAssessmentCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> StoredAssessmentRead:
    bankroll = require_user_owned(db, Bankroll, payload.bankroll_id, user_id)
    odds_snapshot = require_user_owned(db, OddsSnapshot, payload.odds_snapshot_id, user_id)
    event = require_user_owned(db, Event, payload.event_id, user_id)
    selection = db.get(MarketSelection, payload.market_selection_id)
    if selection is None or odds_snapshot.market_selection_id != selection.id:
        raise HTTPException(status_code=404, detail="Market selection not found")

    assessment = assess_value(
        BetAlphaInput(
            estimated_probability=payload.estimated_probability,
            offered_decimal_odds=odds_snapshot.decimal_odds,
            bankroll=bankroll.current_balance,
            max_stake_pct=bankroll.max_stake_pct,
        )
    )
    prediction = Prediction(
        user_id=user_id,
        event_id=event.id,
        market_selection_id=selection.id,
        source=payload.source,
        estimated_probability=payload.estimated_probability,
        generated_at=payload.generated_at,
        explanation=payload.explanation,
    )
    db.add(prediction)
    db.flush()
    value = ValueAssessment(
        user_id=user_id,
        prediction_id=prediction.id,
        odds_snapshot_id=odds_snapshot.id,
        offered_decimal_odds=odds_snapshot.decimal_odds,
        fair_odds=assessment.fair_odds,
        implied_probability=assessment.implied_probability,
        edge=assessment.edge,
        expected_value=assessment.expected_value,
        full_kelly_fraction=assessment.full_kelly_fraction,
        applied_kelly_fraction=assessment.applied_kelly_fraction,
        recommended_stake=assessment.recommended_stake,
        score=assessment.score,
        grade=assessment.grade,
        warnings="\n".join(assessment.warnings),
    )
    db.add(value)
    db.commit()
    db.refresh(value)
    return StoredAssessmentRead(
        prediction_id=prediction.id,
        value_assessment_id=value.id,
        grade=value.grade,
        score=value.score,
        expected_value=value.expected_value,
        edge=value.edge,
        recommended_stake=value.recommended_stake,
        warnings=assessment.warnings,
    )


@router.post("/tickets/preview", response_model=TicketResponse)
def preview_ticket(payload: TicketRequest) -> TicketResponse:
    combined = parlay_decimal_odds(payload.decimal_odds)
    potential_return = payload.stake * combined
    return TicketResponse(
        combined_decimal_odds=combined,
        implied_probability=implied_probability(combined),
        potential_return=potential_return,
        potential_profit=potential_return - payload.stake,
        correlation=assess_correlation(payload.legs),
    )


@router.post("/settlements")
def settle(payload: SettlementRequest) -> dict[str, Decimal]:
    actual_return = settle_single(payload.stake, payload.decimal_odds, payload.result)
    return {"actual_return": actual_return, "profit_loss": profit_loss(payload.stake, actual_return)}


@router.get("/sports", response_model=list[SportRead])
def list_sports(db: Session = Depends(get_db)) -> list[Sport]:
    return list(db.scalars(select(Sport).order_by(Sport.name)).all())


@router.post("/sportsbooks", response_model=SportsbookRead)
def create_sportsbook(
    payload: SportsbookCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> Sportsbook:
    sportsbook = Sportsbook(user_id=user_id, name=payload.name, country=payload.country)
    db.add(sportsbook)
    db.commit()
    db.refresh(sportsbook)
    return sportsbook


@router.get("/sportsbooks", response_model=list[SportsbookRead])
def list_sportsbooks(
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> list[Sportsbook]:
    query = select(Sportsbook).where(Sportsbook.user_id == user_id).order_by(Sportsbook.name)
    return list(db.scalars(query).all())


@router.post("/bankrolls", response_model=BankrollRead)
def create_bankroll(
    payload: BankrollCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> Bankroll:
    unit_size = payload.unit_size or quantize_money(payload.starting_balance * Decimal("0.01"))
    bankroll = Bankroll(
        user_id=user_id,
        name=payload.name,
        currency=payload.currency.upper(),
        starting_balance=payload.starting_balance,
        current_balance=payload.starting_balance,
        unit_size=unit_size,
        max_stake_pct=payload.max_stake_pct,
        daily_stop_pct=payload.daily_stop_pct,
    )
    db.add(bankroll)
    db.flush()
    db.add(
        BankrollTransaction(
            user_id=user_id,
            bankroll_id=bankroll.id,
            transaction_type="initial",
            amount=payload.starting_balance,
            balance_after=payload.starting_balance,
            note="Initial bankroll",
        )
    )
    db.commit()
    db.refresh(bankroll)
    return bankroll


@router.get("/bankrolls", response_model=list[BankrollRead])
def list_bankrolls(
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> list[Bankroll]:
    query = select(Bankroll).where(Bankroll.user_id == user_id).order_by(Bankroll.created_at)
    return list(db.scalars(query).all())


@router.post("/bankroll-transactions", response_model=BankrollTransactionRead)
def create_bankroll_transaction(
    payload: BankrollTransactionCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> BankrollTransaction:
    bankroll = require_user_owned(db, Bankroll, payload.bankroll_id, user_id)
    signed_amount = signed_transaction_amount(payload.transaction_type, payload.amount)
    next_balance = quantize_money(bankroll.current_balance + signed_amount)
    if next_balance < 0:
        raise HTTPException(status_code=422, detail="Bankroll balance cannot go below zero")
    bankroll.current_balance = next_balance
    transaction = BankrollTransaction(
        user_id=user_id,
        bankroll_id=bankroll.id,
        transaction_type=payload.transaction_type,
        amount=quantize_money(signed_amount),
        balance_after=next_balance,
        note=payload.note,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


@router.get("/bankroll-transactions", response_model=list[BankrollTransactionRead])
def list_bankroll_transactions(
    bankroll_id: str | None = None,
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> list[BankrollTransaction]:
    filters = [BankrollTransaction.user_id == user_id]
    if bankroll_id:
        require_user_owned(db, Bankroll, bankroll_id, user_id)
        filters.append(BankrollTransaction.bankroll_id == bankroll_id)
    query = select(BankrollTransaction).where(*filters).order_by(BankrollTransaction.created_at.desc())
    return list(db.scalars(query).all())


@router.get("/bankroll-control", response_model=BankrollControlRead)
def bankroll_control(
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> BankrollControlRead:
    bankrolls = list(db.scalars(select(Bankroll).where(Bankroll.user_id == user_id).order_by(Bankroll.created_at)).all())
    transactions = list(
        db.scalars(
            select(BankrollTransaction)
            .where(BankrollTransaction.user_id == user_id)
            .order_by(BankrollTransaction.created_at.desc())
        ).all()
    )
    return BankrollControlRead(
        bankrolls=bankrolls,
        transactions=transactions,
        exposures=sportsbook_exposures(db, user_id),
        alerts=bankroll_risk_alerts(db, user_id),
    )


@router.post("/events", response_model=EventRead)
def create_event(
    payload: EventCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> Event:
    if db.get(Sport, payload.sport_id) is None:
        raise HTTPException(status_code=404, detail="Sport not found")
    event = Event(user_id=user_id, **payload.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.get("/events", response_model=list[EventRead])
def list_events(
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> list[Event]:
    query = select(Event).where(Event.user_id == user_id).order_by(Event.starts_at)
    return list(db.scalars(query).all())


@router.post("/markets", response_model=MarketRead)
def create_market(
    payload: MarketCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> MarketRead:
    require_user_owned(db, Event, payload.event_id, user_id)
    market = Market(
        event_id=payload.event_id,
        market_type=payload.market_type,
        period=payload.period,
        participant=payload.participant,
        line=payload.line,
        scope=payload.scope,
        settlement_rules=payload.settlement_rules,
    )
    db.add(market)
    db.flush()
    selection = MarketSelection(
        market_id=market.id,
        selection_name=payload.selection_name,
        participant=payload.participant,
    )
    db.add(selection)
    db.commit()
    db.refresh(market)
    db.refresh(selection)
    return market_to_read(db, market)


@router.get("/markets", response_model=list[MarketRead])
def list_markets(
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> list[MarketRead]:
    event_ids = select(Event.id).where(Event.user_id == user_id)
    markets = list(db.scalars(select(Market).where(Market.event_id.in_(event_ids))).all())
    return [market_to_read(db, market) for market in markets]


@router.post("/odds", response_model=OddsRead)
def create_odds(
    payload: OddsCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> OddsSnapshot:
    require_user_owned(db, Sportsbook, payload.sportsbook_id, user_id)
    selection = db.get(MarketSelection, payload.market_selection_id)
    if selection is None:
        raise HTTPException(status_code=404, detail="Market selection not found")
    odds = OddsSnapshot(
        user_id=user_id,
        sportsbook_id=payload.sportsbook_id,
        market_selection_id=payload.market_selection_id,
        odds_format=payload.odds_format,
        decimal_odds=payload.decimal_odds,
        american_odds=decimal_to_american(payload.decimal_odds),
        implied_probability=implied_probability(payload.decimal_odds),
        captured_at=payload.captured_at,
        source=payload.source,
        is_closing_line=payload.is_closing_line,
        raw_payload=payload.raw_payload,
    )
    db.add(odds)
    db.commit()
    db.refresh(odds)
    return odds


@router.get("/odds", response_model=list[OddsRead])
def list_odds(
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> list[OddsSnapshot]:
    query = select(OddsSnapshot).where(OddsSnapshot.user_id == user_id).order_by(OddsSnapshot.captured_at)
    return list(db.scalars(query).all())


@router.post("/intelligence/team-stats", response_model=TeamStatRead)
def create_team_stat(
    payload: TeamStatCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> TeamStatSnapshot:
    if db.get(Sport, payload.sport_id) is None:
        raise HTTPException(status_code=404, detail="Sport not found")
    stat = TeamStatSnapshot(user_id=user_id, **payload.model_dump())
    db.add(stat)
    db.commit()
    db.refresh(stat)
    return stat


@router.get("/intelligence/team-stats", response_model=list[TeamStatRead])
def list_team_stats(
    sport_id: str | None = None,
    team_name: str | None = None,
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> list[TeamStatSnapshot]:
    filters = [TeamStatSnapshot.user_id == user_id]
    if sport_id:
        filters.append(TeamStatSnapshot.sport_id == sport_id)
    if team_name:
        filters.append(TeamStatSnapshot.team_name == team_name)
    return list(
        db.scalars(select(TeamStatSnapshot).where(*filters).order_by(TeamStatSnapshot.created_at.desc())).all()
    )


@router.post("/intelligence/injuries", response_model=InjuryReportRead)
def create_injury_report(
    payload: InjuryReportCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> InjuryReport:
    if db.get(Sport, payload.sport_id) is None:
        raise HTTPException(status_code=404, detail="Sport not found")
    report = InjuryReport(user_id=user_id, **payload.model_dump())
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("/intelligence/injuries", response_model=list[InjuryReportRead])
def list_injury_reports(
    sport_id: str | None = None,
    team_name: str | None = None,
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> list[InjuryReport]:
    filters = [InjuryReport.user_id == user_id]
    if sport_id:
        filters.append(InjuryReport.sport_id == sport_id)
    if team_name:
        filters.append(InjuryReport.team_name == team_name)
    return list(db.scalars(select(InjuryReport).where(*filters).order_by(InjuryReport.created_at.desc())).all())


@router.post("/intelligence/market-movements", response_model=MarketMovementRead)
def create_market_movement(
    payload: MarketMovementCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> MarketMovement:
    require_user_owned(db, Event, payload.event_id, user_id)
    require_user_owned(db, Sportsbook, payload.sportsbook_id, user_id)
    movement = MarketMovement(user_id=user_id, **payload.model_dump())
    db.add(movement)
    db.commit()
    db.refresh(movement)
    return movement


@router.get("/intelligence/market-movements", response_model=list[MarketMovementRead])
def list_market_movements(
    event_id: str | None = None,
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> list[MarketMovement]:
    filters = [MarketMovement.user_id == user_id]
    if event_id:
        require_user_owned(db, Event, event_id, user_id)
        filters.append(MarketMovement.event_id == event_id)
    return list(db.scalars(select(MarketMovement).where(*filters).order_by(MarketMovement.created_at.desc())).all())


@router.post("/intelligence/analyze", response_model=GameAnalysisRead)
def create_game_analysis(
    payload: GameAnalysisRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> GameAnalysisRead:
    event = require_user_owned(db, Event, payload.event_id, user_id)
    home_stats = (
        require_user_owned(db, TeamStatSnapshot, payload.home_team_stat_id, user_id)
        if payload.home_team_stat_id
        else latest_team_stat(db, user_id, event.sport_id, event.home_team)
    )
    away_stats = (
        require_user_owned(db, TeamStatSnapshot, payload.away_team_stat_id, user_id)
        if payload.away_team_stat_id
        else latest_team_stat(db, user_id, event.sport_id, event.away_team)
    )
    if home_stats is None or away_stats is None:
        raise HTTPException(status_code=422, detail="Both home and away team stats are required")

    result = analyze_matchup(
        home_stats,
        away_stats,
        event.home_team or "Home",
        event.away_team or "Away",
    )
    home_edge = (
        result.home_probability - implied_probability(payload.offered_home_odds)
        if payload.offered_home_odds is not None
        else None
    )
    away_edge = (
        result.away_probability - implied_probability(payload.offered_away_odds)
        if payload.offered_away_odds is not None
        else None
    )
    analysis = GameAnalysis(
        user_id=user_id,
        event_id=event.id,
        generated_at=utc_now_text(),
        model_version="explainable-v1",
        estimated_home_probability=result.home_probability,
        estimated_away_probability=result.away_probability,
        fair_home_odds=fair_odds(result.home_probability),
        fair_away_odds=fair_odds(result.away_probability),
        confidence_score=result.confidence_score,
        summary=result.summary,
        factors_json=json.dumps([factor.model_dump(mode="json") for factor in result.factors], ensure_ascii=True),
        risks_json=json.dumps(result.risks, ensure_ascii=True),
    )
    db.add(analysis)
    db.flush()
    db.add(
        PredictionRecord(
            user_id=user_id,
            event_id=event.id,
            analysis_id=analysis.id,
            market_type="moneyline",
            selection_name=event.home_team or "Home",
            estimated_probability=result.home_probability,
            fair_odds=fair_odds(result.home_probability),
            offered_odds=payload.offered_home_odds,
            edge=home_edge,
            confidence_score=result.confidence_score,
        )
    )
    db.add(
        PredictionRecord(
            user_id=user_id,
            event_id=event.id,
            analysis_id=analysis.id,
            market_type="moneyline",
            selection_name=event.away_team or "Away",
            estimated_probability=result.away_probability,
            fair_odds=fair_odds(result.away_probability),
            offered_odds=payload.offered_away_odds,
            edge=away_edge,
            confidence_score=result.confidence_score,
        )
    )
    db.commit()
    db.refresh(analysis)
    return analysis_to_read(analysis, home_edge=home_edge, away_edge=away_edge)


@router.get("/intelligence/analyses", response_model=list[GameAnalysisRead])
def list_game_analyses(
    event_id: str | None = None,
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> list[GameAnalysisRead]:
    filters = [GameAnalysis.user_id == user_id]
    if event_id:
        require_user_owned(db, Event, event_id, user_id)
        filters.append(GameAnalysis.event_id == event_id)
    analyses = list(db.scalars(select(GameAnalysis).where(*filters).order_by(GameAnalysis.created_at.desc())).all())
    return [analysis_to_read(analysis) for analysis in analyses]


@router.post("/intelligence/providers", response_model=DataProviderRead)
def create_data_provider(
    payload: DataProviderCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> DataProvider:
    provider = db.scalar(
        select(DataProvider).where(DataProvider.user_id == user_id, DataProvider.provider_key == payload.provider_key)
    )
    if provider is None:
        provider = DataProvider(user_id=user_id, **payload.model_dump(), last_sync_at=None)
        db.add(provider)
    else:
        for key, value in payload.model_dump().items():
            setattr(provider, key, value)
    db.commit()
    db.refresh(provider)
    return provider


@router.get("/intelligence/providers", response_model=list[DataProviderRead])
def list_data_providers(
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> list[DataProvider]:
    return list(db.scalars(select(DataProvider).where(DataProvider.user_id == user_id).order_by(DataProvider.name)).all())


@router.post("/intelligence/sync/demo", response_model=SyncJobRunRead)
def run_demo_sync(
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> SyncJobRun:
    started_at = utc_now_text()
    provider = db.scalar(select(DataProvider).where(DataProvider.user_id == user_id, DataProvider.provider_key == "demo"))
    if provider is None:
        provider = DataProvider(
            user_id=user_id,
            provider_key="demo",
            name="Proveedor demo local",
            sport_slug="baloncesto",
            status="configured",
            notes="Fuente local para validar pipeline sin API key externa.",
        )
        db.add(provider)
        db.flush()
    result = seed_intelligence_demo(db, user_id)
    provider.last_sync_at = utc_now_text()
    job = SyncJobRun(
        user_id=user_id,
        provider_key="demo",
        job_type="fixtures_stats_odds",
        status="success",
        started_at=started_at,
        finished_at=utc_now_text(),
        records_upserted=int(result["created"]),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.get("/intelligence/sync/jobs", response_model=list[SyncJobRunRead])
def list_sync_jobs(
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> list[SyncJobRun]:
    return list(db.scalars(select(SyncJobRun).where(SyncJobRun.user_id == user_id).order_by(SyncJobRun.created_at.desc())).all())


@router.post("/intelligence/events/candidates", response_model=TheOddsEventsResponse)
def discover_the_odds_candidates(
    payload: TheOddsEventsRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> TheOddsEventsResponse:
    settings = get_settings()
    if not settings.the_odds_api_key:
        raise HTTPException(status_code=400, detail="THE_ODDS_API_KEY is not configured")
    started_at = utc_now_text()
    result = discover_the_odds_events(
        db=db,
        user_id=user_id,
        api_key=settings.the_odds_api_key,
        sport_keys=payload.sport_keys,
    )
    finished_at = utc_now_text()
    provider = db.scalar(
        select(DataProvider).where(
            DataProvider.user_id == user_id,
            DataProvider.provider_key == "the_odds_api",
        )
    )
    if provider is not None:
        provider.last_sync_at = finished_at
        provider.status = "error" if result.errors and result.records_upserted == 0 else "configured"
    job = SyncJobRun(
        user_id=user_id,
        provider_key="the_odds_api",
        job_type="events_candidates",
        status="error" if result.errors and result.records_upserted == 0 else "success",
        started_at=started_at,
        finished_at=finished_at,
        records_upserted=result.records_upserted,
        error_message="; ".join(result.errors) if result.errors else None,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return TheOddsEventsResponse(
        job=SyncJobRunRead.model_validate(job),
        sports_seen=result.sports_seen,
        events_upserted=result.events_upserted,
        requests_used=result.requests_used,
        requests_remaining=result.requests_remaining,
        errors=result.errors,
    )


@router.post("/intelligence/sync/odds", response_model=TheOddsSyncResponse)
def run_the_odds_sync(
    payload: TheOddsSyncRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> TheOddsSyncResponse:
    settings = get_settings()
    if not settings.the_odds_api_key:
        raise HTTPException(status_code=400, detail="THE_ODDS_API_KEY is not configured")
    started_at = utc_now_text()
    result = sync_the_odds(
        db=db,
        user_id=user_id,
        api_key=settings.the_odds_api_key,
        sport_keys=payload.sport_keys,
        regions=payload.regions,
        markets=payload.markets,
    )
    finished_at = utc_now_text()
    provider = db.scalar(
        select(DataProvider).where(
            DataProvider.user_id == user_id,
            DataProvider.provider_key == "the_odds_api",
        )
    )
    if provider is not None:
        provider.last_sync_at = finished_at
        provider.status = "error" if result.errors and result.records_upserted == 0 else "configured"
    job = SyncJobRun(
        user_id=user_id,
        provider_key="the_odds_api",
        job_type="odds_current",
        status="error" if result.errors and result.records_upserted == 0 else "success",
        started_at=started_at,
        finished_at=finished_at,
        records_upserted=result.records_upserted,
        error_message="; ".join(result.errors) if result.errors else None,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return TheOddsSyncResponse(
        job=SyncJobRunRead.model_validate(job),
        sports_seen=result.sports_seen,
        events_upserted=result.events_upserted,
        markets_upserted=result.markets_upserted,
        odds_inserted=result.odds_inserted,
        sportsbooks_upserted=result.sportsbooks_upserted,
        requests_used=result.requests_used,
        requests_remaining=result.requests_remaining,
        errors=result.errors,
    )


@router.get("/intelligence/predictions", response_model=list[PredictionRecordRead])
def list_prediction_records(
    event_id: str | None = None,
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> list[PredictionRecord]:
    filters = [PredictionRecord.user_id == user_id]
    if event_id:
        require_user_owned(db, Event, event_id, user_id)
        filters.append(PredictionRecord.event_id == event_id)
    return list(
        db.scalars(select(PredictionRecord).where(*filters).order_by(PredictionRecord.created_at.desc())).all()
    )


@router.patch("/intelligence/predictions/{prediction_id}", response_model=PredictionRecordRead)
def update_prediction_result(
    prediction_id: str,
    payload: PredictionResultUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> PredictionRecord:
    prediction = require_user_owned(db, PredictionRecord, prediction_id, user_id)
    prediction.result = payload.result
    prediction.closing_odds = payload.closing_odds
    if payload.closing_odds and prediction.offered_odds:
        prediction.clv = (payload.closing_odds - prediction.offered_odds) / prediction.offered_odds
    prediction.evaluated_at = utc_now_text()
    db.commit()
    db.refresh(prediction)
    return prediction


@router.post("/intelligence/backtests/run", response_model=BacktestRunRead)
def create_backtest_run(
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> BacktestRunRead:
    started_at = utc_now_text()
    records = list(db.scalars(select(PredictionRecord).where(PredictionRecord.user_id == user_id)).all())
    metrics = run_backtest(records)
    finished_at = utc_now_text()
    run = BacktestRun(
        user_id=user_id,
        model_version="explainable-v1",
        started_at=started_at,
        finished_at=finished_at,
        sample_size=metrics.sample_size,
        brier_score=metrics.brier_score,
        calibration_error=metrics.calibration_error,
        roi_if_flat_bet=metrics.roi_if_flat_bet,
        summary=metrics.summary,
        buckets_json=json.dumps([bucket.model_dump(mode="json") for bucket in metrics.buckets], ensure_ascii=True),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return backtest_to_read(run)


@router.get("/intelligence/backtests", response_model=list[BacktestRunRead])
def list_backtest_runs(
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> list[BacktestRunRead]:
    runs = list(db.scalars(select(BacktestRun).where(BacktestRun.user_id == user_id).order_by(BacktestRun.created_at.desc())).all())
    return [backtest_to_read(run) for run in runs]


@router.post("/intelligence/demo/seed")
def seed_intelligence_demo(
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> dict[str, int | str]:
    seed_demo_data(db, user_id)
    sport = db.scalar(select(Sport).where(Sport.slug == "baloncesto"))
    sportsbook = db.scalar(select(Sportsbook).where(Sportsbook.user_id == user_id, Sportsbook.name == "Triunfobet DEMO"))
    if sport is None or sportsbook is None:
        raise HTTPException(status_code=500, detail="Demo seed failed")
    event = db.scalar(select(Event).where(Event.user_id == user_id, Event.event_name == "DEMO Analytics Norte vs Sur"))
    created = 0
    if event is None:
        event = Event(
            user_id=user_id,
            sport_id=sport.id,
            league_name="DEMO Basketball League",
            home_team="DEMO Norte",
            away_team="DEMO Sur",
            event_name="DEMO Analytics Norte vs Sur",
            starts_at="2026-01-03T21:00:00Z",
            timezone="UTC",
        )
        db.add(event)
        db.flush()
        created += 1
    if latest_team_stat(db, user_id, sport.id, "DEMO Norte") is None:
        db.add(
            TeamStatSnapshot(
                user_id=user_id,
                sport_id=sport.id,
                team_name="DEMO Norte",
                league_name="DEMO Basketball League",
                season="2026",
                sample_label="last_10",
                games_played=10,
                wins=7,
                losses=3,
                offensive_rating=Decimal("114.2"),
                defensive_rating=Decimal("108.1"),
                pace=Decimal("99.4"),
                recent_form=Decimal("0.7000"),
                home_away_split="home",
                rest_days=2,
                injury_impact=Decimal("0.0500"),
                source="demo",
                captured_at=utc_now_text(),
            )
        )
        created += 1
    if latest_team_stat(db, user_id, sport.id, "DEMO Sur") is None:
        db.add(
            TeamStatSnapshot(
                user_id=user_id,
                sport_id=sport.id,
                team_name="DEMO Sur",
                league_name="DEMO Basketball League",
                season="2026",
                sample_label="last_10",
                games_played=10,
                wins=4,
                losses=6,
                offensive_rating=Decimal("109.3"),
                defensive_rating=Decimal("111.7"),
                pace=Decimal("97.8"),
                recent_form=Decimal("0.4000"),
                home_away_split="away",
                rest_days=1,
                injury_impact=Decimal("0.1800"),
                source="demo",
                captured_at=utc_now_text(),
            )
        )
        created += 1
    db.add(
        MarketMovement(
            user_id=user_id,
            event_id=event.id,
            sportsbook_id=sportsbook.id,
            market_type="moneyline",
            opening_decimal_odds=Decimal("1.95"),
            current_decimal_odds=Decimal("1.83"),
            source="demo",
            captured_at=utc_now_text(),
        )
    )
    created += 1
    db.commit()
    return {"created": created, "event_id": event.id}


@router.post("/bets", response_model=BetRead)
def create_bet(
    payload: BetCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> Bet:
    require_user_owned(db, Bankroll, payload.bankroll_id, user_id)
    require_user_owned(db, Sportsbook, payload.sportsbook_id, user_id)
    if payload.bet_type == "single" and len(payload.legs) != 1:
        raise HTTPException(status_code=422, detail="Single bets require exactly one leg")
    if payload.bet_type == "parlay" and len(payload.legs) < 2:
        raise HTTPException(status_code=422, detail="Parlays require at least two legs")

    combined = parlay_decimal_odds([leg.odds_at_placement for leg in payload.legs])
    bet = Bet(
        user_id=user_id,
        bankroll_id=payload.bankroll_id,
        sportsbook_id=payload.sportsbook_id,
        bet_type=payload.bet_type,
        stake=payload.stake,
        combined_decimal_odds=combined,
        potential_return=quantize_money(payload.stake * combined),
        notes=payload.notes,
        currency=payload.currency.upper(),
    )
    db.add(bet)
    db.flush()
    for leg in payload.legs:
        selection = db.get(MarketSelection, leg.market_selection_id)
        event = require_user_owned(db, Event, leg.event_id, user_id)
        if selection is None:
            raise HTTPException(status_code=404, detail="Market selection not found")
        db.add(
            BetLeg(
                bet_id=bet.id,
                event_id=event.id,
                market_selection_id=selection.id,
                odds_at_placement=leg.odds_at_placement,
                line_at_placement=leg.line_at_placement,
                estimated_probability_at_placement=leg.estimated_probability_at_placement,
                fair_odds_at_placement=leg.fair_odds_at_placement
                or (
                    fair_odds(leg.estimated_probability_at_placement)
                    if leg.estimated_probability_at_placement is not None
                    else None
                ),
                ev_at_placement=leg.ev_at_placement
                or (
                    expected_value(leg.estimated_probability_at_placement, leg.odds_at_placement)
                    if leg.estimated_probability_at_placement is not None
                    else None
                ),
                correlation_group=leg.correlation_group,
            )
        )
    db.commit()
    db.refresh(bet)
    return bet


@router.get("/bets", response_model=list[BetRead])
def list_bets(
    status: str | None = None,
    bet_type: str | None = None,
    bankroll_id: str | None = None,
    sportsbook_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> list[Bet]:
    filters = [Bet.user_id == user_id]
    if status:
        filters.append(Bet.status == status)
    if bet_type:
        filters.append(Bet.bet_type == bet_type)
    if bankroll_id:
        require_user_owned(db, Bankroll, bankroll_id, user_id)
        filters.append(Bet.bankroll_id == bankroll_id)
    if sportsbook_id:
        require_user_owned(db, Sportsbook, sportsbook_id, user_id)
        filters.append(Bet.sportsbook_id == sportsbook_id)
    parsed_from = parse_datetime_filter(date_from)
    parsed_to = parse_datetime_filter(date_to)
    if parsed_from:
        filters.append(Bet.created_at >= parsed_from)
    if parsed_to:
        filters.append(Bet.created_at <= parsed_to)
    query = select(Bet).where(*filters).order_by(Bet.created_at.desc())
    return list(db.scalars(query).all())


@router.get("/bets/{bet_id}", response_model=BetDetailRead)
def get_bet_detail(
    bet_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> BetDetailRead:
    bet = require_user_owned(db, Bet, bet_id, user_id)
    return bet_to_detail(db, bet, user_id)


@router.post("/bets/{bet_id}/settle", response_model=BetRead)
def settle_bet(
    bet_id: str,
    payload: BetSettleRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> Bet:
    bet = require_user_owned(db, Bet, bet_id, user_id)
    bankroll = require_user_owned(db, Bankroll, bet.bankroll_id, user_id)
    if bet.status != "open":
        raise HTTPException(status_code=409, detail="Bet is already settled")
    actual_return = quantize_money(settle_single(bet.stake, bet.combined_decimal_odds, payload.result))
    pnl = quantize_money(profit_loss(bet.stake, actual_return))
    bet.actual_return = actual_return
    bet.profit_loss = pnl
    bet.status = payload.result
    bankroll.current_balance = quantize_money(bankroll.current_balance + pnl)
    db.add(
        BankrollTransaction(
            user_id=user_id,
            bankroll_id=bankroll.id,
            transaction_type=f"settlement:{payload.result}",
            amount=pnl,
            balance_after=bankroll.current_balance,
            note=f"Bet {bet.id} settled",
        )
    )
    db.commit()
    db.refresh(bet)
    return bet


@router.post("/postmortems", response_model=PostmortemRead)
def create_postmortem(
    payload: PostmortemCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> Postmortem:
    require_user_owned(db, Bet, payload.bet_id, user_id)
    postmortem = Postmortem(user_id=user_id, **payload.model_dump())
    db.add(postmortem)
    db.commit()
    db.refresh(postmortem)
    return postmortem


@router.get("/dashboard", response_model=DashboardRead)
def dashboard(
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> DashboardRead:
    bankrolls = list(db.scalars(select(Bankroll).where(Bankroll.user_id == user_id)).all())
    bets = list(db.scalars(select(Bet).where(Bet.user_id == user_id)).all())
    bankroll_balance = sum((b.current_balance for b in bankrolls), Decimal("0"))
    total_staked = sum((b.stake for b in bets), Decimal("0"))
    settled_profit_loss = sum((b.profit_loss or Decimal("0") for b in bets), Decimal("0"))
    open_bets = sum(1 for b in bets if b.status == "open")
    exposure = sum((b.stake for b in bets if b.status == "open"), Decimal("0"))
    roi = settled_profit_loss / total_staked if total_staked else Decimal("0")
    yield_value = settled_profit_loss / total_staked if total_staked else Decimal("0")
    return DashboardRead(
        bankroll_count=len(bankrolls),
        bankroll_balance=bankroll_balance,
        total_staked=total_staked,
        settled_profit_loss=settled_profit_loss,
        roi=roi,
        yield_value=yield_value,
        open_bets=open_bets,
        exposure=exposure,
    )


@router.get("/analytics/summary", response_model=AnalyticsSummary)
def analytics_summary(
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> AnalyticsSummary:
    bets = list(db.scalars(select(Bet).where(Bet.user_id == user_id)).all())
    total_staked = sum((bet.stake for bet in bets), Decimal("0"))
    settled = [bet for bet in bets if bet.status != "open"]
    profit = sum((bet.profit_loss or Decimal("0") for bet in settled), Decimal("0"))
    roi = profit / total_staked if total_staked else Decimal("0")

    statuses = sorted({bet.status for bet in bets})
    bet_types = sorted({bet.bet_type for bet in bets})
    return AnalyticsSummary(
        total_bets=len(bets),
        open_bets=sum(1 for bet in bets if bet.status == "open"),
        settled_bets=len(settled),
        total_staked=total_staked,
        profit_loss=profit,
        roi=roi,
        yield_value=roi,
        by_status=[analytics_bucket(status, [bet for bet in bets if bet.status == status]) for status in statuses],
        by_bet_type=[analytics_bucket(bet_type, [bet for bet in bets if bet.bet_type == bet_type]) for bet_type in bet_types],
    )


@router.get("/exports/bets.csv")
def export_bets_csv(
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> Response:
    bets = list(db.scalars(select(Bet).where(Bet.user_id == user_id).order_by(Bet.created_at.desc())).all())
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "id",
            "bankroll_id",
            "sportsbook_id",
            "bet_type",
            "stake",
            "combined_decimal_odds",
            "potential_return",
            "actual_return",
            "profit_loss",
            "status",
            "currency",
            "created_at",
            "updated_at",
        ]
    )
    for bet in bets:
        writer.writerow(
            [
                bet.id,
                bet.bankroll_id,
                bet.sportsbook_id,
                bet.bet_type,
                bet.stake,
                bet.combined_decimal_odds,
                bet.potential_return,
                bet.actual_return,
                bet.profit_loss,
                bet.status,
                bet.currency,
                bet.created_at,
                bet.updated_at,
            ]
        )
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="betalpha-bets.csv"'},
    )


@router.post("/imports/csv")
async def import_csv(file: UploadFile = File(...)) -> dict[str, int | str]:
    raw = await file.read()
    if len(raw) > 8 * 1024 * 1024:
        return {"status": "rejected", "rows": 0, "reason": "File exceeds the MVP 8MB limit."}
    text = raw.decode("utf-8-sig")
    rows = [line for line in text.splitlines() if line.strip()]
    if not rows:
        return {"status": "empty", "rows": 0}
    return {"status": "validated", "rows": max(0, len(rows) - 1)}


@router.post("/imports/csv/stored")
async def import_csv_stored(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> dict[str, int | str]:
    raw = await file.read()
    if len(raw) > 8 * 1024 * 1024:
        return {"status": "rejected", "rows": 0, "reason": "File exceeds the MVP 8MB limit."}

    text = raw.decode("utf-8-sig")
    rows = list(csv.DictReader(StringIO(text)))
    batch = ImportBatch(
        user_id=user_id,
        filename=file.filename or "import.csv",
        import_type="csv",
        status="pending_review",
        row_count=len(rows),
        error_count=0,
    )
    db.add(batch)
    db.flush()

    error_count = 0
    for index, raw_row in enumerate(rows, start=1):
        import_row = ImportRow(
            user_id=user_id,
            import_id=batch.id,
            row_number=index,
            sport=row_value(raw_row, "sport"),
            league=row_value(raw_row, "league"),
            event=row_value(raw_row, "event"),
            home_team=row_value(raw_row, "home_team"),
            away_team=row_value(raw_row, "away_team"),
            starts_at=row_value(raw_row, "starts_at"),
            market_type=row_value(raw_row, "market_type"),
            selection=row_value(raw_row, "selection"),
            line=parse_decimal(row_value(raw_row, "line")),
            odds=parse_decimal(row_value(raw_row, "odds")),
            odds_format=row_value(raw_row, "odds_format") or "decimal",
            sportsbook=row_value(raw_row, "sportsbook"),
            captured_at=row_value(raw_row, "captured_at"),
            raw_payload=json.dumps(raw_row, ensure_ascii=True),
        )
        error = validate_import_row(import_row)
        if error:
            import_row.status = "invalid"
            import_row.error_message = error
            error_count += 1
        db.add(import_row)

    batch.error_count = error_count
    if rows and error_count == len(rows):
        batch.status = "invalid"
    db.commit()
    return {"id": batch.id, "status": batch.status, "rows": len(rows), "errors": error_count}


@router.get("/imports/rows", response_model=list[ImportRowRead])
def list_import_rows(
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> list[ImportRow]:
    query = select(ImportRow).where(ImportRow.user_id == user_id).order_by(ImportRow.created_at.desc())
    return list(db.scalars(query).all())


@router.patch("/imports/rows/{row_id}", response_model=ImportRowRead)
def update_import_row(
    row_id: str,
    payload: ImportRowUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> ImportRow:
    row = require_user_owned(db, ImportRow, row_id, user_id)
    if row.status == "confirmed":
        raise HTTPException(status_code=409, detail="Confirmed rows cannot be edited")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, key, value.strip() if isinstance(value, str) else value)

    error = validate_import_row(row)
    row.error_message = error
    row.status = "invalid" if error else "pending_review"
    db.commit()
    db.refresh(row)
    return row


@router.post("/imports/rows/{row_id}/confirm", response_model=ImportConfirmResponse)
def confirm_import_row(
    row_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> ImportConfirmResponse:
    row = require_user_owned(db, ImportRow, row_id, user_id)
    if row.status == "confirmed":
        if row.created_event_id and row.created_market_id and row.created_odds_snapshot_id:
            return ImportConfirmResponse(
                row=row,
                event_id=row.created_event_id,
                market_id=row.created_market_id,
                odds_snapshot_id=row.created_odds_snapshot_id,
            )
        raise HTTPException(status_code=409, detail="Row is confirmed but missing created ids")

    error = validate_import_row(row)
    if error:
        row.status = "invalid"
        row.error_message = error
        db.commit()
        raise HTTPException(status_code=422, detail=f"Invalid import row: {error}")

    sport = db.scalar(select(Sport).where(Sport.slug == slugify(row.sport or "")))
    if sport is None:
        sport = Sport(name=row.sport or "Imported sport", slug=slugify(row.sport or "imported-sport"))
        db.add(sport)
        db.flush()

    sportsbook = db.scalar(
        select(Sportsbook).where(Sportsbook.user_id == user_id, Sportsbook.name == row.sportsbook)
    )
    if sportsbook is None:
        sportsbook = Sportsbook(user_id=user_id, name=row.sportsbook or "Imported sportsbook")
        db.add(sportsbook)
        db.flush()

    event = Event(
        user_id=user_id,
        sport_id=sport.id,
        league_name=row.league or "Imported league",
        home_team=row.home_team,
        away_team=row.away_team,
        event_name=row.event or "Imported event",
        starts_at=row.starts_at or utc_now_text(),
        timezone="UTC",
    )
    db.add(event)
    db.flush()

    market = Market(event_id=event.id, market_type=row.market_type or "imported", line=row.line)
    db.add(market)
    db.flush()

    selection = MarketSelection(market_id=market.id, selection_name=row.selection or "Imported selection")
    db.add(selection)
    db.flush()

    decimal_odds = row.odds or Decimal("2.0")
    odds = OddsSnapshot(
        user_id=user_id,
        sportsbook_id=sportsbook.id,
        market_selection_id=selection.id,
        odds_format=row.odds_format or "decimal",
        decimal_odds=decimal_odds,
        american_odds=decimal_to_american(decimal_odds),
        implied_probability=implied_probability(decimal_odds),
        captured_at=row.captured_at or utc_now_text(),
        source="csv",
        raw_payload=row.raw_payload,
    )
    db.add(odds)
    db.flush()

    row.status = "confirmed"
    row.error_message = None
    row.created_event_id = event.id
    row.created_market_id = market.id
    row.created_odds_snapshot_id = odds.id
    db.commit()
    db.refresh(row)
    return ImportConfirmResponse(row=row, event_id=event.id, market_id=market.id, odds_snapshot_id=odds.id)


@router.post("/attachments/screenshots")
async def upload_screenshot(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> dict[str, str | int]:
    raw = await file.read()
    attachment = Attachment(
        user_id=user_id,
        filename=file.filename or "screenshot",
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(raw),
        storage_path=f"local://pending/{user_id}/{file.filename or 'screenshot'}",
    )
    db.add(attachment)
    db.commit()
    return {
        "status": "received",
        "id": attachment.id,
        "filename": file.filename or "screenshot",
        "bytes": len(raw),
        "note": "OCR is optional and requires provider configuration plus human review.",
    }


@router.post("/demo/seed")
def seed_demo(
    db: Session = Depends(get_db),
    user_id: str = Depends(current_user_id),
) -> dict[str, int]:
    return seed_demo_data(db, user_id)


@router.get("/demo/dashboard")
def demo_dashboard() -> dict[str, object]:
    roi = expected_value(Decimal("0.56"), Decimal("1.95"))
    return {
        "bankroll": 1000,
        "profit": 48.5,
        "roi": roi,
        "yield": Decimal("0.0485"),
        "drawdown": Decimal("0.032"),
        "open_bets": 2,
        "exposure": 34,
        "alerts": ["Demo: parlays with 5+ legs are classified as high risk."],
    }
