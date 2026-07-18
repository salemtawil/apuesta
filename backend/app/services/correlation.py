from pydantic import BaseModel


class TicketLeg(BaseModel):
    event_id: str
    market_type: str
    selection: str
    participant: str | None = None
    line: float | None = None


class CorrelationResult(BaseModel):
    same_game: bool
    risk_score: int
    warnings: list[str]


def assess_correlation(legs: list[TicketLeg]) -> CorrelationResult:
    warnings: list[str] = []
    event_counts: dict[str, int] = {}
    for leg in legs:
        event_counts[leg.event_id] = event_counts.get(leg.event_id, 0) + 1

    same_game = any(count > 1 for count in event_counts.values())
    risk = 0
    if same_game:
        risk += 45
        warnings.append("Hay selecciones del mismo evento; posible same-game parlay.")

    for left in legs:
        for right in legs:
            if left is right or left.event_id != right.event_id:
                continue
            left_market = left.market_type.lower()
            right_market = right.market_type.lower()
            if "moneyline" in left_market and "spread" in right_market:
                risk += 20
                warnings.append("Ganador y handicap del mismo evento pueden estar correlacionados.")
            if "total" in left_market and "team_total" in right_market:
                risk += 20
                warnings.append("Total del partido y team total pueden estar correlacionados.")
            if "over" in left.selection.lower() and "over" in right.selection.lower():
                risk += 10

    risk = min(100, risk)
    if risk >= 50:
        warnings.append("No se debe multiplicar probabilidades sin validar independencia.")
    return CorrelationResult(same_game=same_game, risk_score=risk, warnings=sorted(set(warnings)))
