from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Bankroll, BankrollTransaction, Sport, Sportsbook

DEMO_USER_ID = "00000000-0000-4000-8000-000000000001"


def seed_demo_data(db: Session, user_id: str = DEMO_USER_ID) -> dict[str, int]:
    created = 0
    for name, slug in [
        ("Futbol", "futbol"),
        ("Baloncesto", "baloncesto"),
        ("Beisbol", "beisbol"),
        ("Tenis", "tenis"),
        ("MMA/UFC", "mma-ufc"),
    ]:
        if db.scalar(select(Sport).where(Sport.slug == slug)) is None:
            db.add(Sport(name=name, slug=slug))
            created += 1

    if db.scalar(select(Sportsbook).where(Sportsbook.user_id == user_id, Sportsbook.name == "Triunfobet DEMO")) is None:
        db.add(Sportsbook(user_id=user_id, name="Triunfobet DEMO", country="VE"))
        created += 1

    bankroll_exists = db.scalar(select(Bankroll).where(Bankroll.user_id == user_id, Bankroll.name == "Banca DEMO"))
    if bankroll_exists is None:
        bankroll = Bankroll(
            user_id=user_id,
            name="Banca DEMO",
            currency="USD",
            starting_balance=Decimal("1000.00"),
            current_balance=Decimal("1000.00"),
            unit_size=Decimal("10.00"),
            max_stake_pct=Decimal("0.0150"),
            daily_stop_pct=Decimal("0.0500"),
        )
        db.add(bankroll)
        db.flush()
        db.add(
            BankrollTransaction(
                user_id=user_id,
                bankroll_id=bankroll.id,
                transaction_type="initial",
                amount=Decimal("1000.00"),
                balance_after=Decimal("1000.00"),
                note="DEMO initial bankroll",
            )
        )
        created += 2

    db.commit()
    return {"created": created}
