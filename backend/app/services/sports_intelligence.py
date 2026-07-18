from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel


class IntelligenceFactor(BaseModel):
    label: str
    direction: str
    impact: Decimal
    detail: str


class IntelligenceResult(BaseModel):
    home_probability: Decimal
    away_probability: Decimal
    confidence_score: Decimal
    summary: str
    factors: list[IntelligenceFactor]
    risks: list[str]


def _value(value: Decimal | None, fallback: Decimal) -> Decimal:
    return value if value is not None else fallback


def _clamp(value: Decimal, lower: Decimal, upper: Decimal) -> Decimal:
    return max(lower, min(upper, value))


def _team_strength(stats) -> Decimal:
    offense = _value(stats.offensive_rating, Decimal("100"))
    defense = _value(stats.defensive_rating, Decimal("100"))
    form = _value(stats.recent_form, Decimal("0.5"))
    rest = Decimal(stats.rest_days or 0)
    injury = _value(stats.injury_impact, Decimal("0"))
    return (offense - defense) + ((form - Decimal("0.5")) * Decimal("12")) + (rest * Decimal("0.35")) - (injury * Decimal("10"))


def analyze_matchup(home_stats, away_stats, home_team: str, away_team: str) -> IntelligenceResult:
    home_strength = _team_strength(home_stats)
    away_strength = _team_strength(away_stats)
    strength_delta = home_strength - away_strength
    home_probability = _clamp(
        Decimal("0.50") + (strength_delta / Decimal("100")) + Decimal("0.025"),
        Decimal("0.30"),
        Decimal("0.70"),
    )
    away_probability = Decimal("1") - home_probability

    factors = [
        IntelligenceFactor(
            label="Diferencial estadistico",
            direction="home" if strength_delta >= 0 else "away",
            impact=abs(strength_delta / Decimal("100")),
            detail=f"{home_team} fuerza {home_strength:.2f} vs {away_team} fuerza {away_strength:.2f}.",
        ),
        IntelligenceFactor(
            label="Ventaja local",
            direction="home",
            impact=Decimal("0.025"),
            detail="Se aplica una ventaja base por localia.",
        ),
    ]

    rest_delta = Decimal(home_stats.rest_days or 0) - Decimal(away_stats.rest_days or 0)
    if rest_delta:
        factors.append(
            IntelligenceFactor(
                label="Descanso",
                direction="home" if rest_delta > 0 else "away",
                impact=abs(rest_delta) * Decimal("0.0035"),
                detail=f"Diferencia de descanso: {rest_delta} dia(s).",
            )
        )

    injury_delta = _value(home_stats.injury_impact, Decimal("0")) - _value(away_stats.injury_impact, Decimal("0"))
    if injury_delta:
        factors.append(
            IntelligenceFactor(
                label="Impacto de lesiones",
                direction="away" if injury_delta > 0 else "home",
                impact=abs(injury_delta) * Decimal("0.10"),
                detail="Mayor impacto de bajas reduce la proyeccion del equipo afectado.",
            )
        )

    risks = []
    if home_stats.games_played < 5 or away_stats.games_played < 5:
        risks.append("Muestra estadistica pequeña; baja confianza.")
    if home_stats.offensive_rating is None or away_stats.offensive_rating is None:
        risks.append("Faltan ratings ofensivos completos.")
    if home_stats.defensive_rating is None or away_stats.defensive_rating is None:
        risks.append("Faltan ratings defensivos completos.")
    if _value(home_stats.injury_impact, Decimal("0")) > Decimal("0.25") or _value(
        away_stats.injury_impact, Decimal("0")
    ) > Decimal("0.25"):
        risks.append("Lesiones con impacto alto; revisar noticias antes de apostar.")

    completeness = Decimal("1") - (Decimal(len(risks)) * Decimal("0.12"))
    sample_quality = _clamp(Decimal(min(home_stats.games_played, away_stats.games_played)) / Decimal("20"), Decimal("0"), Decimal("1"))
    confidence = _clamp((completeness + sample_quality) / Decimal("2"), Decimal("0.20"), Decimal("0.92"))

    lean = home_team if home_probability >= away_probability else away_team
    summary = (
        f"El modelo explicable inclina el juego hacia {lean}: "
        f"{home_team} {home_probability * 100:.1f}% vs {away_team} {away_probability * 100:.1f}%."
    )
    return IntelligenceResult(
        home_probability=home_probability.quantize(Decimal("0.00000001")),
        away_probability=away_probability.quantize(Decimal("0.00000001")),
        confidence_score=confidence.quantize(Decimal("0.0001")),
        summary=summary,
        factors=factors,
        risks=risks,
    )
