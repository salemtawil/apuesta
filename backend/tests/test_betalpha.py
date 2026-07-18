from decimal import Decimal

from app.services.betalpha import BetAlphaInput, assess_value


def test_assessment_positive_value_with_cap() -> None:
    result = assess_value(
        BetAlphaInput(
            estimated_probability=Decimal("0.58"),
            offered_decimal_odds=Decimal("2.05"),
            bankroll=Decimal("1000"),
            data_quality=80,
            model_quality=75,
            market_stability=70,
            uncertainty=25,
        )
    )
    assert result.expected_value > 0
    assert result.recommended_stake <= Decimal("15.00")
    assert result.grade in {"A+", "A", "B+", "B", "C", "No bet"}
    assert result.explanation["disclaimer"] == "Score de calidad de decisión; no es probabilidad de ganar."
