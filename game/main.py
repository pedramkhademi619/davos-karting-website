"""
سرویسِ صفحهٔ «به‌زودی» کارتینگ داووس.

کاملاً مستقل از سامانهٔ رزروِ داخلی است: دیتابیس، پورت و استقرارِ خودش را
دارد و هیچ وابستگی‌ای به آن ندارد.

جدول‌ها با Alembic ساخته می‌شوند، نه اینجا — قبل از اولین اجرا:
       alembic upgrade head

اجرا:  python main.py          (پیش‌فرض روی پورت ۸۰۹۰)
       HOST=0.0.0.0 PORT=80 python main.py
"""

import os
import sys

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes import STATIC_DIR, router

for _stream in (sys.stdout, sys.stderr):
    if _stream is not None and hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


def _refuse_multi_worker() -> None:
    """
    حالتِ دور/ضدِ‌جعل و لیمیترهای نرخ فقط در حافظهٔ همین پردازش‌اند (app/service.py)؛
    با بیش از یک worker هر کدام state جدا می‌گیرند و رفتارِ ضدِ‌جعل خراب می‌شود
    (بی‌سروصدا، نه با خطا) — پس همین‌جا صریح جلوی بالا‌آمدن را می‌گیریم.
    برای اسکیل‌کردنِ واقعی، این state باید به Redis (یا مشابه) منتقل شود.
    """
    workers = os.environ.get("WEB_CONCURRENCY") or os.environ.get("UVICORN_WORKERS")
    if workers and int(workers) > 1:
        raise RuntimeError(
            "این سرویس فقط با یک worker درست کار می‌کند (state ضدِ‌جعل در حافظه است). "
            f"WEB_CONCURRENCY={workers} را بردار یا روی ۱ بگذار."
        )
    # uvicorn --workers N خودش هیچ متغیرِ محیطی‌ای نمی‌گذارد، پس آرگومان‌های اجرا را هم چک می‌کنیم
    # (این فقط برای اجرای مستقیمِ uvicorn با این پرچم اثر دارد، نه برای هر روشِ دیگرِ چندپردازه‌ای).
    argv = " ".join(sys.argv)
    if "--workers" in argv and "--workers 1" not in argv and "--workers=1" not in argv:
        raise RuntimeError(
            "این سرویس فقط با یک worker درست کار می‌کند (state ضدِ‌جعل در حافظه است). "
            "پرچمِ --workers را از دستورِ اجرا بردار."
        )


def create_app() -> FastAPI:
    _refuse_multi_worker()
    app = FastAPI(title="Davoos Karting — Coming Soon")
    app.include_router(router)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8090"))
    print(f"\n  صفحهٔ «به‌زودی» روی http://localhost:{port} بالا آمد.\n")
    uvicorn.run(app, host=host, port=port)
