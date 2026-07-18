from __future__ import annotations

import json
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, Protocol
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DataProvider, Event, Market, MarketSelection, OddsSnapshot, Sport, Sportsbook
from app.services.odds import decimal_to_american, implied_probability

THE_ODDS_BASE_URL = "https://api.the-odds-api.com"
DEFAULT_SPORT_KEYS = ["baseball_mlb"]
DEFAULT_MARKETS = ["h2h", "spreads", "totals"]


class TheOddsClient(Protocol):
    def get_sports(self, all_sports: bool = False) -> tuple[list[dict[str, Any]], dict[str, str]]:
        ...

    def get_odds(
        self,
        sport_key: str,
        regions: str,
        markets: list[str],
        odds_format: str,
        date_format: str,
    ) -> tuple[list[dict[str, Any]], dict[str, str]]:
        ...


class TheOddsApiClient:
    def __init__(self, api_key: str, base_url: str = THE_ODDS_BASE_URL) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def _get(self, path: str, params: dict[str, str]) -> tuple[Any, dict[str, str]]:
        query = urlencode({"apiKey": self.api_key, **params})
        request = Request(f"{self.base_url}{path}?{query}", headers={"Accept": "application/json"})
        with urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
            headers = {key.lower(): value for key, value in response.headers.items()}
            return payload, headers

    def get_sports(self, all_sports: bool = False) -> tuple[list[dict[str, Any]], dict[str, str]]:
        params = {"all": "true"} if all_sports else {}
        payload, headers = self._get("/v4/sports/", params)
        return list(payload), headers

    def get_odds(
        self,
        sport_key: str,
        regions: str,
        markets: list[str],
        odds_format: str,
        date_format: str,
    ) -> tuple[list[dict[str, Any]], dict[str, str]]:
        payload, headers = self._get(
            f"/v4/sports/{sport_key}/odds/",
            {
                "regions": regions,
                "markets": ",".join(markets),
                "oddsFormat": odds_format,
                "dateFormat": date_format,
            },
        )
        return list(payload), headers


@dataclass
class TheOddsSyncResult:
    sports_seen: int = 0
    events_upserted: int = 0
    markets_upserted: int = 0
    odds_inserted: int = 0
    sportsbooks_upserted: int = 0
    requests_used: str | None = None
    requests_remaining: str | None = None
    errors: list[str] = field(default_factory=list)

    @property
    def records_upserted(self) -> int:
        return self.events_upserted + self.markets_upserted + self.odds_inserted + self.sportsbooks_upserted


def normalize_markets(markets: list[str] | None) -> list[str]:
    clean = [market.strip() for market in markets or DEFAULT_MARKETS if market.strip()]
    return clean or DEFAULT_MARKETS


def sync_the_odds(
    db: Session,
    user_id: str,
    api_key: str,
    sport_keys: list[str] | None = None,
    regions: str = "us",
    markets: list[str] | None = None,
    client: TheOddsClient | None = None,
) -> TheOddsSyncResult:
    active_client = client or TheOddsApiClient(api_key)
    selected_sports = sport_keys or DEFAULT_SPORT_KEYS
    selected_markets = normalize_markets(markets)
    result = TheOddsSyncResult()

    sports_payload, sports_headers = active_client.get_sports()
    result.sports_seen = len(sports_payload)
    update_usage(result, sports_headers)
    sport_meta = {item.get("key"): item for item in sports_payload if item.get("key")}

    ensure_provider(db, user_id)

    for sport_key in selected_sports:
        try:
            odds_payload, odds_headers = active_client.get_odds(
                sport_key=sport_key,
                regions=regions,
                markets=selected_markets,
                odds_format="decimal",
                date_format="iso",
            )
            update_usage(result, odds_headers)
            sport = upsert_sport(db, sport_key, sport_meta.get(sport_key))
            for event_payload in odds_payload:
                event = upsert_event(db, user_id, sport, event_payload)
                result.events_upserted += 1
                for bookmaker_payload in event_payload.get("bookmakers", []):
                    sportsbook = upsert_sportsbook(db, user_id, bookmaker_payload)
                    result.sportsbooks_upserted += 1
                    for market_payload in bookmaker_payload.get("markets", []):
                        market_result = upsert_market_odds(
                            db=db,
                            user_id=user_id,
                            event=event,
                            sportsbook=sportsbook,
                            market_payload=market_payload,
                            captured_at=bookmaker_payload.get("last_update") or event_payload.get("commence_time"),
                        )
                        result.markets_upserted += market_result[0]
                        result.odds_inserted += market_result[1]
        except Exception as exc:  # pragma: no cover - exercised by API route behavior.
            result.errors.append(f"{sport_key}: {exc}")

    return result


def update_usage(result: TheOddsSyncResult, headers: dict[str, str]) -> None:
    result.requests_used = headers.get("x-requests-used") or result.requests_used
    result.requests_remaining = headers.get("x-requests-remaining") or result.requests_remaining


def ensure_provider(db: Session, user_id: str) -> DataProvider:
    provider = db.scalar(
        select(DataProvider).where(
            DataProvider.user_id == user_id,
            DataProvider.provider_key == "the_odds_api",
        )
    )
    if provider is None:
        provider = DataProvider(
            user_id=user_id,
            provider_key="the_odds_api",
            name="The Odds API",
            base_url=THE_ODDS_BASE_URL,
            api_key_env="THE_ODDS_API_KEY",
            status="configured",
            notes="Odds, sportsbooks, events and market prices.",
        )
        db.add(provider)
        db.flush()
    return provider


def upsert_sport(db: Session, sport_key: str, meta: dict[str, Any] | None) -> Sport:
    sport = db.scalar(select(Sport).where(Sport.slug == sport_key))
    if sport is None:
        sport = Sport(name=str((meta or {}).get("title") or sport_key), slug=sport_key)
        db.add(sport)
        db.flush()
    return sport


def upsert_event(db: Session, user_id: str, sport: Sport, payload: dict[str, Any]) -> Event:
    home_team = payload.get("home_team")
    away_team = payload.get("away_team")
    starts_at = payload.get("commence_time")
    league_name = payload.get("sport_title") or payload.get("sport_key") or sport.name
    event_name = f"{away_team} @ {home_team}" if home_team and away_team else str(payload.get("id"))
    event = db.scalar(
        select(Event).where(
            Event.user_id == user_id,
            Event.sport_id == sport.id,
            Event.starts_at == starts_at,
            Event.home_team == home_team,
            Event.away_team == away_team,
        )
    )
    if event is None:
        event = Event(
            user_id=user_id,
            sport_id=sport.id,
            league_name=str(league_name),
            home_team=home_team,
            away_team=away_team,
            event_name=event_name,
            starts_at=str(starts_at),
            timezone="UTC",
            status="scheduled",
        )
        db.add(event)
        db.flush()
    else:
        event.league_name = str(league_name)
        event.event_name = event_name
        event.status = "scheduled"
    return event


def upsert_sportsbook(db: Session, user_id: str, payload: dict[str, Any]) -> Sportsbook:
    name = str(payload.get("title") or payload.get("key") or "Unknown sportsbook")
    sportsbook = db.scalar(
        select(Sportsbook).where(Sportsbook.user_id == user_id, Sportsbook.name == name)
    )
    if sportsbook is None:
        sportsbook = Sportsbook(user_id=user_id, name=name, country=None)
        db.add(sportsbook)
        db.flush()
    return sportsbook


def upsert_market_odds(
    db: Session,
    user_id: str,
    event: Event,
    sportsbook: Sportsbook,
    market_payload: dict[str, Any],
    captured_at: str | None,
) -> tuple[int, int]:
    market_key = str(market_payload.get("key") or "unknown")
    market_type = map_market_type(market_key)
    markets_created = 0
    odds_inserted = 0
    for outcome in market_payload.get("outcomes", []):
        selection_name = str(outcome.get("name") or "")
        if not selection_name:
            continue
        line = decimal_or_none(outcome.get("point"))
        market = db.scalar(
            select(Market).where(
                Market.event_id == event.id,
                Market.market_type == market_type,
                Market.line == line,
                Market.participant == selection_name,
            )
        )
        if market is None:
            market = Market(
                event_id=event.id,
                market_type=market_type,
                participant=selection_name,
                line=line,
                status="open",
            )
            db.add(market)
            db.flush()
            markets_created += 1
        selection = db.scalar(
            select(MarketSelection).where(
                MarketSelection.market_id == market.id,
                MarketSelection.selection_name == selection_name,
            )
        )
        if selection is None:
            selection = MarketSelection(
                market_id=market.id,
                selection_name=selection_name,
                participant=selection_name,
            )
            db.add(selection)
            db.flush()
        price = decimal_or_none(outcome.get("price"))
        if price is None or price <= Decimal("1"):
            continue
        odds = OddsSnapshot(
            user_id=user_id,
            sportsbook_id=sportsbook.id,
            market_selection_id=selection.id,
            odds_format="decimal",
            decimal_odds=price,
            american_odds=decimal_to_american(price),
            implied_probability=implied_probability(price),
            captured_at=str(captured_at or ""),
            source="the_odds_api",
            is_closing_line=False,
            raw_payload=json.dumps(outcome, sort_keys=True),
        )
        db.add(odds)
        odds_inserted += 1
    return markets_created, odds_inserted


def decimal_or_none(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def map_market_type(market_key: str) -> str:
    return {
        "h2h": "moneyline",
        "spreads": "spread",
        "totals": "total",
    }.get(market_key, market_key)
