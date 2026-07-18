from app.db.seeds import seed_demo_data
from app.db.session import SessionLocal


def main() -> None:
    with SessionLocal() as db:
        result = seed_demo_data(db)
    print(result)


if __name__ == "__main__":
    main()
