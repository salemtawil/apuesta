from decimal import Decimal


def settle_single(stake: Decimal, decimal_odds: Decimal, result: str) -> Decimal:
    result = result.lower()
    if result == "win":
        return stake * decimal_odds
    if result == "loss":
        return Decimal("0")
    if result in {"void", "push"}:
        return stake
    if result == "half_win":
        return (stake / 2) * decimal_odds + (stake / 2)
    if result == "half_loss":
        return stake / 2
    raise ValueError(f"Unsupported settlement result: {result}")


def profit_loss(stake: Decimal, actual_return: Decimal) -> Decimal:
    return actual_return - stake
