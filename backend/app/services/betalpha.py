from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field

from app.services.odds import (
    expected_value,
    fair_odds,
    full_kelly,
    implied_probability,
    recommended_stake,
)


class BetAlphaInput(BaseModel):
    estimated_probability: Decimal = Field(gt=0, le=1)
    offered_decimal_odds: Decimal = Field(gt=1)
    bankroll: Decimal = Field(gt=0)
    data_quality: int = Field(default=75, ge=0, le=100)
    model_quality: int = Field(default=65, ge=0, le=100)
    market_stability: int = Field(default=65, ge=0, le=100)
    uncertainty: int = Field(default=35, ge=0, le=100)
    correlation_risk: int = Field(default=0, ge=0, le=100)
    sport_risk: int = Field(default=15, ge=0, le=100)
    fractional_kelly_value: Decimal = Field(default=Decimal("0.25"), ge=0, le=1)
    max_stake_pct: Decimal = Field(default=Decimal("0.015"), gt=0, le=1)


class BetAlphaAssessment(BaseModel):
    implied_probability: Decimal
    fair_odds: Decimal
    edge: Decimal
    expected_value: Decimal
    full_kelly_fraction: Decimal
    applied_kelly_fraction: Decimal
    recommended_stake: Decimal
    score: int
    grade: str
    warnings: list[str]
    explanation: dict[str, int | str]


def grade_for(score: int, ev: Decimal) -> str:
    if ev <= 0 or score < 65:
        return "No bet"
    if score >= 90:
        return "A+"
    if score >= 85:
        return "A"
    if score >= 80:
        return "B+"
    if score >= 75:
        return "B"
    return "C"


def assess_value(data: BetAlphaInput) -> BetAlphaAssessment:
    imp = implied_probability(data.offered_decimal_odds)
    fair = fair_odds(data.estimated_probability)
    ev = expected_value(data.estimated_probability, data.offered_decimal_odds)
    edge = data.estimated_probability - imp
    full = full_kelly(data.estimated_probability, data.offered_decimal_odds)
    applied = max(Decimal("0"), full * data.fractional_kelly_value)
    stake = recommended_stake(
        data.bankroll,
        data.estimated_probability,
        data.offered_decimal_odds,
        data.fractional_kelly_value,
        data.max_stake_pct,
    )

    ev_points = max(0, min(30, int(ev * 300)))
    model_points = int(data.model_quality * 0.20)
    data_points = int(data.data_quality * 0.15)
    market_points = int(data.market_stability * 0.10)
    uncertainty_points = max(0, int((100 - data.uncertainty) * 0.10))
    sport_points = max(0, int((100 - data.sport_risk) * 0.10))
    penalty = int(data.correlation_risk * 0.20)
    score = max(0, min(100, ev_points + model_points + data_points + market_points + uncertainty_points + sport_points - penalty))

    warnings: list[str] = []
    if ev <= 0:
        warnings.append("EV no positivo: no se recomienda stake.")
    if full <= 0:
        warnings.append("Kelly negativo o nulo: stake recomendado 0.")
    if data.correlation_risk >= 50:
        warnings.append("Riesgo de correlación alto; no asumir independencia.")
    if data.uncertainty >= 70:
        warnings.append("Incertidumbre alta; revisar fuente de probabilidad.")

    return BetAlphaAssessment(
        implied_probability=imp,
        fair_odds=fair,
        edge=edge,
        expected_value=ev,
        full_kelly_fraction=full,
        applied_kelly_fraction=applied,
        recommended_stake=stake,
        score=score,
        grade=grade_for(score, ev),
        warnings=warnings,
        explanation={
            "ev_points": ev_points,
            "model_points": model_points,
            "data_points": data_points,
            "market_points": market_points,
            "uncertainty_points": uncertainty_points,
            "sport_points": sport_points,
            "correlation_penalty": penalty,
            "disclaimer": "Score de calidad de decisión; no es probabilidad de ganar.",
        },
    )
