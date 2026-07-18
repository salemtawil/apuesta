from decimal import Decimal

import pytest

from app.services.odds import (
    american_to_decimal,
    clv_by_odds,
    clv_by_probability,
    decimal_to_american,
    expected_value,
    fractional_kelly,
    full_kelly,
    implied_probability,
    parlay_decimal_odds,
    parlay_expected_value,
    recommended_stake,
    remove_vig_three_way,
    remove_vig_two_way,
)


def test_decimal_american_conversions() -> None:
    assert american_to_decimal(150) == Decimal("2.5")
    assert american_to_decimal(-200) == Decimal("1.5")
    assert decimal_to_american(Decimal("2.5")) == 150
    assert decimal_to_american(Decimal("1.5")) == -200


def test_implied_probability_ev_and_kelly() -> None:
    assert implied_probability(Decimal("2.0")) == Decimal("0.5")
    assert expected_value(Decimal("0.55"), Decimal("2.0")) == Decimal("0.100")
    assert full_kelly(Decimal("0.55"), Decimal("2.0")) == Decimal("0.10")
    assert fractional_kelly(Decimal("0.55"), Decimal("2.0"), Decimal("0.25")) == Decimal("0.0250")


def test_negative_kelly_recommends_zero() -> None:
    assert full_kelly(Decimal("0.45"), Decimal("2.0")) == Decimal("-0.10")
    assert fractional_kelly(Decimal("0.45"), Decimal("2.0"), Decimal("0.25")) == Decimal("0")
    assert recommended_stake(1000, Decimal("0.45"), Decimal("2.0")) == Decimal("0.00")


def test_remove_vig() -> None:
    a, b = remove_vig_two_way(Decimal("1.91"), Decimal("1.91"))
    assert a.quantize(Decimal("0.001")) == Decimal("0.500")
    assert b.quantize(Decimal("0.001")) == Decimal("0.500")
    probs = remove_vig_three_way(Decimal("2.4"), Decimal("3.2"), Decimal("3.1"))
    assert sum(probs).quantize(Decimal("0.001")) == Decimal("1.000")


def test_parlay_and_clv() -> None:
    assert parlay_decimal_odds([Decimal("1.8"), Decimal("2.0")]) == Decimal("3.60")
    assert parlay_expected_value(
        [Decimal("0.58"), Decimal("0.52")],
        [Decimal("1.8"), Decimal("2.0")],
    ) == Decimal("0.085760")
    assert clv_by_odds(Decimal("2.1"), Decimal("1.95")) > 0
    assert clv_by_probability(Decimal("2.1"), Decimal("1.95")) > 0


def test_invalid_odds() -> None:
    with pytest.raises(ValueError):
        implied_probability(Decimal("1"))
