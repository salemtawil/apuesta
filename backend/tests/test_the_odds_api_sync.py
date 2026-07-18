from typing import Any

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models import Event, Market, OddsSnapshot, Sport, Sportsbook
from app.services.the_odds_api import discover_the_odds_events, sync_the_odds


class FakeTheOddsClient:
    def get_sports(self, all_sports: bool = False) -> tuple[list[dict[str, Any]], dict[str, str]]:
        return (
            [
                {
                    "key": "basketball_nba",
                    "group": "Basketball",
                    "title": "NBA",
                    "description": "US Basketball",
                    "active": True,
                    "has_outrights": False,
                }
            ],
            {"x-requests-used": "0", "x-requests-remaining": "500"},
        )

    def get_odds(
        self,
        sport_key: str,
        regions: str,
        markets: list[str],
        odds_format: str,
        date_format: str,
    ) -> tuple[list[dict[str, Any]], dict[str, str]]:
        assert sport_key == "basketball_nba"
        assert regions == "us"
        assert markets == ["h2h", "spreads", "totals"]
        assert odds_format == "decimal"
        assert date_format == "iso"
        return (
            [
                {
                    "id": "evt_1",
                    "sport_key": "basketball_nba",
                    "sport_title": "NBA",
                    "commence_time": "2026-07-20T00:00:00Z",
                    "home_team": "New York Knicks",
                    "away_team": "Boston Celtics",
                    "bookmakers": [
                        {
                            "key": "draftkings",
                            "title": "DraftKings",
                            "last_update": "2026-07-17T05:00:00Z",
                            "markets": [
                                {
                                    "key": "h2h",
                                    "outcomes": [
                                        {"name": "Boston Celtics", "price": "1.80"},
                                        {"name": "New York Knicks", "price": "2.05"},
                                    ],
                                },
                                {
                                    "key": "spreads",
                                    "outcomes": [
                                        {"name": "Boston Celtics", "price": "1.91", "point": -2.5},
                                        {"name": "New York Knicks", "price": "1.91", "point": 2.5},
                                    ],
                                },
                                {
                                    "key": "totals",
                                    "outcomes": [
                                        {"name": "Over", "price": "1.90", "point": 218.5},
                                        {"name": "Under", "price": "1.92", "point": 218.5},
                                    ],
                                },
                            ],
                        }
                    ],
                }
            ],
            {"x-requests-used": "1", "x-requests-remaining": "499"},
        )

    def get_events(self, sport_key: str, date_format: str) -> tuple[list[dict[str, Any]], dict[str, str]]:
        assert sport_key == "basketball_nba"
        assert date_format == "iso"
        return (
            [
                {
                    "id": "evt_2",
                    "sport_key": "basketball_nba",
                    "sport_title": "NBA",
                    "commence_time": "2026-07-21T00:00:00Z",
                    "home_team": "Los Angeles Lakers",
                    "away_team": "Miami Heat",
                }
            ],
            {"x-requests-used": "0", "x-requests-remaining": "499"},
        )


def test_sync_the_odds_maps_provider_payload_to_local_models() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with testing_session() as db:
        result = sync_the_odds(
            db=db,
            user_id="00000000-0000-4000-8000-000000000077",
            api_key="fake",
            sport_keys=["basketball_nba"],
            regions="us",
            markets=["h2h", "spreads", "totals"],
            client=FakeTheOddsClient(),
        )
        db.commit()

        assert result.sports_seen == 1
        assert result.events_upserted == 1
        assert result.sportsbooks_upserted == 1
        assert result.markets_upserted == 6
        assert result.odds_inserted == 6
        assert result.requests_remaining == "499"

        assert db.scalar(select(Sport).where(Sport.slug == "basketball_nba")) is not None
        assert db.scalar(select(Event).where(Event.event_name == "Boston Celtics @ New York Knicks")) is not None
        assert db.scalar(select(Sportsbook).where(Sportsbook.name == "DraftKings")) is not None
        assert db.scalar(select(Market).where(Market.market_type == "moneyline")) is not None
        assert len(list(db.scalars(select(OddsSnapshot)).all())) == 6


def test_discover_the_odds_events_maps_candidates_without_odds() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with testing_session() as db:
        result = discover_the_odds_events(
            db=db,
            user_id="00000000-0000-4000-8000-000000000077",
            api_key="fake",
            sport_keys=["basketball_nba"],
            client=FakeTheOddsClient(),
        )
        db.commit()

        assert result.sports_seen == 1
        assert result.events_upserted == 1
        assert result.requests_remaining == "499"

        assert db.scalar(select(Sport).where(Sport.slug == "basketball_nba")) is not None
        assert db.scalar(select(Event).where(Event.event_name == "Miami Heat @ Los Angeles Lakers")) is not None
        assert len(list(db.scalars(select(Market)).all())) == 0
        assert len(list(db.scalars(select(OddsSnapshot)).all())) == 0
