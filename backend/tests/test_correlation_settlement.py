from decimal import Decimal

from app.services.correlation import TicketLeg, assess_correlation
from app.services.settlement import profit_loss, settle_single


def test_same_game_correlation_warning() -> None:
    result = assess_correlation(
        [
            TicketLeg(event_id="game-1", market_type="moneyline", selection="Lakers"),
            TicketLeg(event_id="game-1", market_type="spread", selection="Lakers +3.5"),
        ]
    )
    assert result.same_game is True
    assert result.risk_score >= 50
    assert result.warnings


def test_settlement_variants() -> None:
    assert settle_single(Decimal("10"), Decimal("2.5"), "win") == Decimal("25.0")
    assert settle_single(Decimal("10"), Decimal("2.5"), "loss") == Decimal("0")
    assert settle_single(Decimal("10"), Decimal("2.5"), "void") == Decimal("10")
    assert settle_single(Decimal("10"), Decimal("2.5"), "push") == Decimal("10")
    assert settle_single(Decimal("10"), Decimal("2.5"), "half_win") == Decimal("17.50")
    assert settle_single(Decimal("10"), Decimal("2.5"), "half_loss") == Decimal("5")
    assert profit_loss(Decimal("10"), Decimal("25")) == Decimal("15")
