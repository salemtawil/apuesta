from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, getcontext
from fractions import Fraction

getcontext().prec = 28

D = Decimal


def _d(value: float | int | str | Decimal) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def quantize_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def american_to_decimal(american_odds: int) -> Decimal:
    if american_odds == 0:
        raise ValueError("American odds cannot be zero")
    if american_odds > 0:
        return Decimal("1") + (Decimal(american_odds) / Decimal("100"))
    return Decimal("1") + (Decimal("100") / abs(Decimal(american_odds)))


def decimal_to_american(decimal_odds: float | Decimal) -> int:
    odds = _d(decimal_odds)
    if odds <= 1:
        raise ValueError("Decimal odds must be greater than 1")
    if odds >= 2:
        return int(((odds - 1) * 100).to_integral_value(rounding=ROUND_HALF_UP))
    return int((-100 / (odds - 1)).to_integral_value(rounding=ROUND_HALF_UP))


def decimal_to_fractional(decimal_odds: float | Decimal, max_denominator: int = 100) -> str:
    odds = _d(decimal_odds)
    if odds <= 1:
        raise ValueError("Decimal odds must be greater than 1")
    frac = Fraction(float(odds - 1)).limit_denominator(max_denominator)
    return f"{frac.numerator}/{frac.denominator}"


def implied_probability(decimal_odds: float | Decimal) -> Decimal:
    odds = _d(decimal_odds)
    if odds <= 1:
        raise ValueError("Decimal odds must be greater than 1")
    return Decimal("1") / odds


def fair_odds(probability: float | Decimal) -> Decimal:
    p = _d(probability)
    if p <= 0 or p > 1:
        raise ValueError("Probability must be in (0, 1]")
    return Decimal("1") / p


def expected_value(probability: float | Decimal, decimal_odds: float | Decimal) -> Decimal:
    p = _d(probability)
    odds = _d(decimal_odds)
    if p < 0 or p > 1:
        raise ValueError("Probability must be in [0, 1]")
    if odds <= 1:
        raise ValueError("Decimal odds must be greater than 1")
    return (p * odds) - Decimal("1")


def remove_vig_two_way(decimal_a: float | Decimal, decimal_b: float | Decimal) -> tuple[Decimal, Decimal]:
    pa = implied_probability(decimal_a)
    pb = implied_probability(decimal_b)
    total = pa + pb
    return pa / total, pb / total


def remove_vig_three_way(
    decimal_a: float | Decimal, decimal_b: float | Decimal, decimal_c: float | Decimal
) -> tuple[Decimal, Decimal, Decimal]:
    pa = implied_probability(decimal_a)
    pb = implied_probability(decimal_b)
    pc = implied_probability(decimal_c)
    total = pa + pb + pc
    return pa / total, pb / total, pc / total


def full_kelly(probability: float | Decimal, decimal_odds: float | Decimal) -> Decimal:
    p = _d(probability)
    odds = _d(decimal_odds)
    if p <= 0 or p >= 1:
        return Decimal("0") if p <= 0 else Decimal("1")
    b = odds - Decimal("1")
    if b <= 0:
        raise ValueError("Decimal odds must be greater than 1")
    q = Decimal("1") - p
    return ((b * p) - q) / b


def fractional_kelly(
    probability: float | Decimal,
    decimal_odds: float | Decimal,
    fraction: float | Decimal = Decimal("0.25"),
) -> Decimal:
    kelly = full_kelly(probability, decimal_odds)
    if kelly <= 0:
        return Decimal("0")
    return kelly * _d(fraction)


def recommended_stake(
    bankroll: float | Decimal,
    probability: float | Decimal,
    decimal_odds: float | Decimal,
    fraction: float | Decimal = Decimal("0.25"),
    max_stake_pct: float | Decimal = Decimal("0.015"),
) -> Decimal:
    roll = _d(bankroll)
    if roll <= 0:
        return Decimal("0")
    raw_fraction = fractional_kelly(probability, decimal_odds, fraction)
    capped_fraction = min(raw_fraction, _d(max_stake_pct))
    return quantize_money(roll * capped_fraction)


def parlay_decimal_odds(legs: list[float | Decimal]) -> Decimal:
    if not legs:
        raise ValueError("At least one leg is required")
    total = Decimal("1")
    for leg in legs:
        odds = _d(leg)
        if odds <= 1:
            raise ValueError("Each decimal odd must be greater than 1")
        total *= odds
    return total


def parlay_implied_probability(legs: list[float | Decimal]) -> Decimal:
    return implied_probability(parlay_decimal_odds(legs))


def parlay_expected_value(
    probabilities: list[float | Decimal],
    odds: list[float | Decimal],
    joint_probability: float | Decimal | None = None,
) -> Decimal:
    if len(probabilities) != len(odds):
        raise ValueError("Probabilities and odds length mismatch")
    p = _d(joint_probability) if joint_probability is not None else Decimal("1")
    if joint_probability is None:
        for probability in probabilities:
            p *= _d(probability)
    return expected_value(p, parlay_decimal_odds(odds))


def clv_by_odds(odds_at_placement: float | Decimal, closing_odds: float | Decimal) -> Decimal:
    return (_d(odds_at_placement) / _d(closing_odds)) - Decimal("1")


def clv_by_probability(odds_at_placement: float | Decimal, closing_odds: float | Decimal) -> Decimal:
    return implied_probability(closing_odds) - implied_probability(odds_at_placement)
