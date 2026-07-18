from collections.abc import Iterator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import current_user_id
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Sport


def test_mvp_api_flow() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with testing_session() as seed_db:
        seed_db.add(Sport(name="Baloncesto", slug="baloncesto"))
        seed_db.commit()

    def override_db() -> Iterator[Session]:
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[current_user_id] = lambda: "00000000-0000-4000-8000-000000000099"
    client = TestClient(app)

    try:
        sport = client.get("/api/v1/sports").json()[0]
        sportsbook = client.post("/api/v1/sportsbooks", json={"name": "Triunfobet DEMO", "country": "VE"})
        assert sportsbook.status_code == 200
        sportsbook_id = sportsbook.json()["id"]

        bankroll = client.post(
            "/api/v1/bankrolls",
            json={"name": "Principal", "currency": "USD", "starting_balance": "1000.00"},
        )
        assert bankroll.status_code == 200
        bankroll_id = bankroll.json()["id"]
        assert bankroll.json()["unit_size"] == "10.00"

        event = client.post(
            "/api/v1/events",
            json={
                "sport_id": sport["id"],
                "league_name": "DEMO NBA",
                "home_team": "DEMO Lakers",
                "away_team": "DEMO Suns",
                "event_name": "DEMO Lakers vs DEMO Suns",
                "starts_at": "2026-01-01T20:00:00Z",
            },
        )
        assert event.status_code == 200
        event_id = event.json()["id"]

        home_stat = client.post(
            "/api/v1/intelligence/team-stats",
            json={
                "sport_id": sport["id"],
                "team_name": "DEMO Lakers",
                "league_name": "DEMO NBA",
                "season": "2026",
                "sample_label": "last_10",
                "games_played": 10,
                "wins": 7,
                "losses": 3,
                "offensive_rating": "114.0",
                "defensive_rating": "108.0",
                "pace": "99.0",
                "recent_form": "0.7000",
                "home_away_split": "home",
                "rest_days": 2,
                "injury_impact": "0.0500",
                "captured_at": "2026-01-01T12:00:00Z",
            },
        )
        assert home_stat.status_code == 200

        away_stat = client.post(
            "/api/v1/intelligence/team-stats",
            json={
                "sport_id": sport["id"],
                "team_name": "DEMO Suns",
                "league_name": "DEMO NBA",
                "season": "2026",
                "sample_label": "last_10",
                "games_played": 10,
                "wins": 4,
                "losses": 6,
                "offensive_rating": "109.0",
                "defensive_rating": "112.0",
                "pace": "97.0",
                "recent_form": "0.4000",
                "home_away_split": "away",
                "rest_days": 1,
                "injury_impact": "0.1500",
                "captured_at": "2026-01-01T12:00:00Z",
            },
        )
        assert away_stat.status_code == 200

        injury = client.post(
            "/api/v1/intelligence/injuries",
            json={
                "sport_id": sport["id"],
                "team_name": "DEMO Suns",
                "player_name": "DEMO Starter",
                "status": "questionable",
                "impact_score": "0.1500",
                "captured_at": "2026-01-01T12:00:00Z",
            },
        )
        assert injury.status_code == 200

        market = client.post(
            "/api/v1/markets",
            json={
                "event_id": event_id,
                "market_type": "spread",
                "selection_name": "DEMO Lakers +3.5",
                "line": "3.5",
            },
        )
        assert market.status_code == 200
        selection_id = market.json()["selection"]["id"]

        movement = client.post(
            "/api/v1/intelligence/market-movements",
            json={
                "event_id": event_id,
                "sportsbook_id": sportsbook_id,
                "market_type": "moneyline",
                "opening_decimal_odds": "1.95",
                "current_decimal_odds": "1.88",
                "captured_at": "2026-01-01T12:00:00Z",
            },
        )
        assert movement.status_code == 200

        analysis = client.post(
            "/api/v1/intelligence/analyze",
            json={
                "event_id": event_id,
                "offered_home_odds": "1.91",
                "offered_away_odds": "1.91",
            },
        )
        assert analysis.status_code == 200
        assert analysis.json()["estimated_home_probability"] > analysis.json()["estimated_away_probability"]
        assert analysis.json()["fair_home_odds"] < "2.0000"
        assert analysis.json()["factors"]

        analyses = client.get("/api/v1/intelligence/analyses", params={"event_id": event_id})
        assert analyses.status_code == 200
        assert analyses.json()[0]["model_version"] == "explainable-v1"

        predictions = client.get("/api/v1/intelligence/predictions", params={"event_id": event_id})
        assert predictions.status_code == 200
        assert len(predictions.json()) == 2
        home_prediction = next(item for item in predictions.json() if item["selection_name"] == "DEMO Lakers")
        away_prediction = next(item for item in predictions.json() if item["selection_name"] == "DEMO Suns")

        updated_home = client.patch(
            f"/api/v1/intelligence/predictions/{home_prediction['id']}",
            json={"result": "win", "closing_odds": "1.85"},
        )
        assert updated_home.status_code == 200
        assert updated_home.json()["result"] == "win"
        assert updated_home.json()["clv"] is not None

        updated_away = client.patch(
            f"/api/v1/intelligence/predictions/{away_prediction['id']}",
            json={"result": "loss"},
        )
        assert updated_away.status_code == 200

        backtest = client.post("/api/v1/intelligence/backtests/run")
        assert backtest.status_code == 200
        assert backtest.json()["sample_size"] == 2
        assert backtest.json()["buckets"]

        provider = client.post(
            "/api/v1/intelligence/providers",
            json={"provider_key": "demo", "name": "Proveedor demo local", "sport_slug": "baloncesto"},
        )
        assert provider.status_code == 200

        sync = client.post("/api/v1/intelligence/sync/demo")
        assert sync.status_code == 200
        assert sync.json()["status"] == "success"

        odds = client.post(
            "/api/v1/odds",
            json={
                "sportsbook_id": sportsbook_id,
                "market_selection_id": selection_id,
                "decimal_odds": "1.91",
                "captured_at": "2026-01-01T12:00:00Z",
            },
        )
        assert odds.status_code == 200
        odds_id = odds.json()["id"]

        assessment = client.post(
            "/api/v1/assessments/stored",
            json={
                "event_id": event_id,
                "market_selection_id": selection_id,
                "odds_snapshot_id": odds_id,
                "estimated_probability": "0.56",
                "bankroll_id": bankroll_id,
                "generated_at": "2026-01-01T12:05:00Z",
            },
        )
        assert assessment.status_code == 200
        assert assessment.json()["expected_value"] > "0"

        bet = client.post(
            "/api/v1/bets",
            json={
                "bankroll_id": bankroll_id,
                "sportsbook_id": sportsbook_id,
                "bet_type": "single",
                "stake": "10.00",
                "legs": [
                    {
                        "event_id": event_id,
                        "market_selection_id": selection_id,
                        "odds_at_placement": "1.91",
                        "line_at_placement": "3.5",
                        "estimated_probability_at_placement": "0.56",
                    }
                ],
            },
        )
        assert bet.status_code == 200
        bet_id = bet.json()["id"]
        assert bet.json()["potential_return"] == "19.10"

        settled = client.post(f"/api/v1/bets/{bet_id}/settle", json={"result": "win"})
        assert settled.status_code == 200
        assert settled.json()["profit_loss"] == "9.10"

        postmortem = client.post(
            "/api/v1/postmortems",
            json={
                "bet_id": bet_id,
                "analysis_quality": "buena_apuesta_gano",
                "result_quality": "ganada",
                "process_followed": True,
                "lessons": "DEMO: se respeto el stake recomendado.",
            },
        )
        assert postmortem.status_code == 200

        filtered = client.get("/api/v1/bets", params={"status": "win", "bet_type": "single"})
        assert filtered.status_code == 200
        assert len(filtered.json()) == 1
        assert filtered.json()[0]["id"] == bet_id

        empty_filtered = client.get("/api/v1/bets", params={"status": "open"})
        assert empty_filtered.status_code == 200
        assert empty_filtered.json() == []

        detail = client.get(f"/api/v1/bets/{bet_id}")
        assert detail.status_code == 200
        assert detail.json()["sportsbook_name"] == "Triunfobet DEMO"
        assert detail.json()["bankroll_name"] == "Principal"
        assert detail.json()["legs"][0]["event_name"] == "DEMO Lakers vs DEMO Suns"
        assert detail.json()["legs"][0]["selection_name"] == "DEMO Lakers +3.5"
        assert detail.json()["postmortems"][0]["analysis_quality"] == "buena_apuesta_gano"

        dashboard = client.get("/api/v1/dashboard")
        assert dashboard.status_code == 200
        assert dashboard.json()["bankroll_balance"] == "2009.10"
        assert dashboard.json()["open_bets"] == 0

        analytics = client.get("/api/v1/analytics/summary")
        assert analytics.status_code == 200
        assert analytics.json()["total_bets"] == 1
        assert analytics.json()["profit_loss"] == "9.10"
        assert analytics.json()["by_status"][0]["label"] == "win"

        export = client.get("/api/v1/exports/bets.csv")
        assert export.status_code == 200
        assert "bet_type,stake,combined_decimal_odds" in export.text
        assert "single,10.00,1.9100" in export.text

        deposit = client.post(
            "/api/v1/bankroll-transactions",
            json={
                "bankroll_id": bankroll_id,
                "transaction_type": "deposit",
                "amount": "50.00",
                "note": "Top up",
            },
        )
        assert deposit.status_code == 200
        assert deposit.json()["balance_after"] == "1059.10"

        withdrawal = client.post(
            "/api/v1/bankroll-transactions",
            json={
                "bankroll_id": bankroll_id,
                "transaction_type": "withdrawal",
                "amount": "9.10",
                "note": "Cash out",
            },
        )
        assert withdrawal.status_code == 200
        assert withdrawal.json()["amount"] == "-9.10"
        assert withdrawal.json()["balance_after"] == "1050.00"

        large_open_bet = client.post(
            "/api/v1/bets",
            json={
                "bankroll_id": bankroll_id,
                "sportsbook_id": sportsbook_id,
                "bet_type": "single",
                "stake": "100.00",
                "legs": [
                    {
                        "event_id": event_id,
                        "market_selection_id": selection_id,
                        "odds_at_placement": "1.91",
                        "estimated_probability_at_placement": "0.56",
                    }
                ],
            },
        )
        assert large_open_bet.status_code == 200

        transactions = client.get("/api/v1/bankroll-transactions", params={"bankroll_id": bankroll_id})
        assert transactions.status_code == 200
        assert transactions.json()[0]["transaction_type"] == "withdrawal"

        control = client.get("/api/v1/bankroll-control")
        assert control.status_code == 200
        assert control.json()["bankrolls"][0]["current_balance"] == "1050.00"
        assert control.json()["exposures"][0]["open_exposure"] == "100.00"
        alert_codes = {alert["code"] for alert in control.json()["alerts"]}
        assert {"open_exposure_limit", "stake_over_limit"}.issubset(alert_codes)

        with testing_session() as verify_db:
            assert verify_db.scalar(select(Sport).where(Sport.slug == "baloncesto")) is not None
    finally:
        app.dependency_overrides.clear()


def test_csv_import_rows_can_be_confirmed() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_db() -> Iterator[Session]:
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[current_user_id] = lambda: "00000000-0000-4000-8000-000000000098"
    client = TestClient(app)

    try:
        csv_payload = (
            "sport,league,event,home_team,away_team,starts_at,market_type,selection,line,odds,"
            "odds_format,sportsbook,captured_at\n"
            "Baloncesto,DEMO NBA,DEMO Lakers vs Suns,DEMO Lakers,DEMO Suns,"
            "2026-01-01T20:00:00Z,spread,DEMO Lakers +3.5,3.5,1.91,decimal,"
            "Triunfobet DEMO,2026-01-01T12:00:00Z\n"
        )
        uploaded = client.post(
            "/api/v1/imports/csv/stored",
            files={"file": ("triunfobet.csv", csv_payload, "text/csv")},
        )
        assert uploaded.status_code == 200
        assert uploaded.json()["rows"] == 1
        assert uploaded.json()["errors"] == 0

        rows = client.get("/api/v1/imports/rows")
        assert rows.status_code == 200
        row = rows.json()[0]
        assert row["status"] == "pending_review"
        assert row["selection"] == "DEMO Lakers +3.5"

        confirmed = client.post(f"/api/v1/imports/rows/{row['id']}/confirm")
        assert confirmed.status_code == 200
        assert confirmed.json()["row"]["status"] == "confirmed"

        events = client.get("/api/v1/events")
        odds = client.get("/api/v1/odds")
        assert events.json()[0]["event_name"] == "DEMO Lakers vs Suns"
        assert odds.json()[0]["source"] == "csv"
    finally:
        app.dependency_overrides.clear()


def test_invalid_csv_import_row_can_be_corrected_before_confirmation() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_db() -> Iterator[Session]:
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[current_user_id] = lambda: "00000000-0000-4000-8000-000000000097"
    client = TestClient(app)

    try:
        csv_payload = (
            "sport,league,event,market_type,selection,odds,odds_format,sportsbook,captured_at\n"
            "Baloncesto,DEMO NBA,DEMO Import con error,spread,DEMO Import +1.5,1.00,decimal,"
            "Triunfobet DEMO,2026-01-01T12:00:00Z\n"
        )
        uploaded = client.post(
            "/api/v1/imports/csv/stored",
            files={"file": ("invalid.csv", csv_payload, "text/csv")},
        )
        assert uploaded.status_code == 200
        assert uploaded.json()["errors"] == 1

        row = client.get("/api/v1/imports/rows").json()[0]
        assert row["status"] == "invalid"
        assert "odds_gt_1" in row["error_message"]

        updated = client.patch(
            f"/api/v1/imports/rows/{row['id']}",
            json={"odds": "1.91", "selection": "DEMO Import +1.5 corregida"},
        )
        assert updated.status_code == 200
        assert updated.json()["status"] == "pending_review"
        assert updated.json()["error_message"] is None

        confirmed = client.post(f"/api/v1/imports/rows/{row['id']}/confirm")
        assert confirmed.status_code == 200
        assert confirmed.json()["row"]["status"] == "confirmed"
    finally:
        app.dependency_overrides.clear()
