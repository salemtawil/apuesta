from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

os.environ.setdefault("BETALPHA_ENVIRONMENT", "production")
temp_db = Path(tempfile.gettempdir()) / "betalpha_vercel.db"
os.environ.setdefault("BETALPHA_DATABASE_URL", f"sqlite:///{temp_db.as_posix()}")
os.environ.setdefault("BETALPHA_CORS_ORIGINS", '["*"]')

from app.db.base import Base  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.main import app  # noqa: E402
from app import models as _models  # noqa: E402,F401

Base.metadata.create_all(bind=engine)
