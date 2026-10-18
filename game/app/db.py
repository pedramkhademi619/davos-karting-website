"""اتصال به دیتابیس — یک فایلِ sqlite کنارِ خودِ سرویس."""

import os
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


def service_dir() -> Path:
    """محلِ واقعیِ سرویس: کنارِ فایلِ اجرایی در حالتِ بسته‌بندی‌شده، وگرنه ریشهٔ landing/."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


SERVICE_DIR = service_dir()

# با DATABASE_URL می‌شود به هر دیتابیسِ دیگری وصل شد (مثلاً postgres روی سرور)؛
# پیش‌فرض یک sqlite کنارِ خودِ سرویس است تا بدون هیچ تنظیمی بالا بیاید.
DATABASE_URL = os.environ.get(
    "LANDING_DATABASE_URL",
    f"sqlite:///{(SERVICE_DIR / 'landing.db').as_posix()}",
)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
