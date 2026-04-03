from __future__ import annotations

from pathlib import Path

from core.db import init_db
from core.seed_data import seed_demo_data


def main() -> None:
    db_path = Path(__file__).resolve().parent / "app.db"
    init_db(db_path)
    result = seed_demo_data(db_path, replace_existing=True)
    print("Demo data seeded:")
    for key, value in result.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
