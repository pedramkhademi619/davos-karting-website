"""Writes .env for the client demo from .env.example: a small footprint (1 GB server), the site served over HTTPS at one
host (main site, booking at /booking and the panel at /admin), fresh random secrets, and a sign-in code shown on the
page because SMS is not live yet. Nothing here prints a secret; read the panel password with
``grep ADMIN_BOOTSTRAP_PASSWORD .env`` on the server.

    python3 deploy/demo/make_env.py test.davoskarting.ir
"""

from __future__ import annotations

import re
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main(host: str) -> None:
    target = ROOT / ".env"
    if target.exists():
        raise SystemExit(".env already exists; remove it first if you really want a new one (it holds the database password).")
    url = f"https://{host}"
    values = {
        "APP_ENV": "development",  # not production: allows the on-screen sign-in code below
        "PUBLIC_BASE_URL": url,
        "BOOKING_BASE_URL": "",
        "ADMIN_BASE_URL": "",
        "CORS_ALLOWED_ORIGINS": f'["{url}"]',
        "COOKIE_SECURE": "true",
        "DEV_SMS_ECHO_ENABLED": "true",
        "SMS_PROVIDER": "recording",
        "PAYMENTS_ENABLED": "false",
        "HTTP_PORT": "8090",
        "API_WORKERS": "1",
        "FRONTEND_REPLICAS": "1",
        "DAVOS_VERSION": "demo",
        "SEMANTIC_CACHE_ENABLED": "false",
        "PROXY_MEMORY_LIMIT": "64m",
        "FRONTEND_MEMORY_LIMIT": "256m",
        "API_MEMORY_LIMIT": "320m",
        "WORKER_MEMORY_LIMIT": "256m",
        "SCHEDULER_MEMORY_LIMIT": "160m",
        "POSTGRES_MEMORY_LIMIT": "256m",
        "REDIS_MEMORY_LIMIT": "64m",
        "GAME_MEMORY_LIMIT": "128m",
        "DB_POOL_SIZE": "4",
        "DB_MAX_OVERFLOW": "2",
        "POSTGRES_PASSWORD": secrets.token_hex(24),
        "GAME_DB_PASSWORD": secrets.token_hex(24),
        "REDIS_PASSWORD": secrets.token_hex(24),
        "OTP_HMAC_SECRET": secrets.token_hex(32),
        "SESSION_CSRF_SECRET": secrets.token_hex(32),
        "BOOKING_WEBHOOK_SECRET": secrets.token_hex(32),
        "ADMIN_BOOTSTRAP_USERNAME": "owner",
        "ADMIN_BOOTSTRAP_PASSWORD": secrets.token_urlsafe(18),
    }
    text = (ROOT / ".env.example").read_text(encoding="utf-8")
    for key, value in values.items():
        text, count = re.subn(rf"^{key}=.*$", lambda _m, k=key, v=value: f"{k}={v}", text, flags=re.M)
        if count != 1:
            raise SystemExit(f"{key} is not exactly once in .env.example")
    target.write_text(text, encoding="utf-8")
    target.chmod(0o600)
    print(f".env written for {url} (mode 600). Panel user: owner; password: grep ADMIN_BOOTSTRAP_PASSWORD .env")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
