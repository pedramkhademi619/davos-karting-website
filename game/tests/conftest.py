import os
import sys
import uuid
from pathlib import Path

import pytest

SERVICE_DIR = Path(__file__).resolve().parent.parent
if str(SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICE_DIR))

# باید پیش از importِ لایهٔ دیتابیس تنظیم شود؛ هر اجرای تست یک فایلِ جدا
# می‌گیرد تا هرگز با landing.db واقعی تداخل نکند.
TEST_DB_PATH = SERVICE_DIR / f"landing_test_{uuid.uuid4().hex}.db"
os.environ["LANDING_DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"

from app.db import Base, engine  # noqa: E402
from app import service  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from main import app  # noqa: E402


def pytest_sessionfinish(session, exitstatus):
    engine.dispose()
    if TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink()
        except OSError:
            pass


@pytest.fixture(autouse=True)
def _fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    # محدودیتِ ضدِ اسپم بین تست‌ها نباید نشت کند.
    service._last_submit.clear()
    service._runs.clear()
    service.run_start_limiter.clear()
    service.run_tick_limiter.clear()
    service.score_submit_limiter.clear()
    service.player_lookup_limiter.clear()
    yield


@pytest.fixture()
def client():
    return TestClient(app)
