"""مسیرهای HTTP — هم API و هم خودِ صفحه."""

from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from . import service
from .db import get_db
from .schemas import (
    PHONE_PATTERN,
    LeaderboardRow,
    LiveBoard,
    PlayerLookup,
    RunRequest,
    RunStart,
    RunTick,
    ScoreSubmit,
    SubmitResult,
)

STATIC_DIR = Path(__file__).resolve().parents[1] / "static"

# تعدادِ ردیف‌هایی که روی صفحه نشان داده می‌شود.
BOARD_SIZE = 10

router = APIRouter()


def _client_ip(request: Request) -> str:
    """
    IPِ واقعیِ کلاینت. سرور همیشه پشتِ nginx است، پس اولین حلقهٔ X-Forwarded-For
    (که nginx خودش می‌سازد) معتبر است؛ بدونِ آن (مثلاً تستِ محلی) به آدرسِ اتصال برمی‌گردیم.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.get("/api/health")
def health():
    return {"status": "ok"}


@router.get("/api/leaderboard", response_model=list[LeaderboardRow])
def leaderboard(
    limit: int = Query(BOARD_SIZE, ge=1, le=50),
    scope: Literal["all_time", "weekly", "monthly"] = "all_time",
    db: Session = Depends(get_db),
):
    if scope == "weekly":
        return service.weekly_rows(db, limit)
    if scope == "monthly":
        return service.monthly_rows(db, limit)
    return service.top_rows(db, limit)


@router.get("/api/leaderboard/live", response_model=LiveBoard)
def live_leaderboard(limit: int = Query(15, ge=1, le=50), db: Session = Depends(get_db)):
    return LiveBoard(count=service.live_count(db), rows=service.live_rows(db, limit))


@router.get("/api/player/{phone}", response_model=PlayerLookup)
def player_lookup(phone: str, request: Request, db: Session = Depends(get_db)):
    if not service.player_lookup_limiter.allow(_client_ip(request)):
        raise HTTPException(status_code=429, detail="کمی صبر کنید و دوباره تلاش کنید")
    if not PHONE_PATTERN.match(phone):
        raise HTTPException(status_code=422, detail="شماره تماس نامعتبر است")
    name = service.get_name_by_phone(db, phone)
    if name is None:
        raise HTTPException(status_code=404, detail="این شماره قبلاً بازی نکرده است")
    return PlayerLookup(name=name)


@router.post("/api/run", response_model=RunStart)
def start_run(payload: RunRequest, request: Request):
    ip = _client_ip(request)
    if not service.run_start_limiter.allow(ip):
        raise HTTPException(status_code=429, detail="کمی صبر کنید و دوباره تلاش کنید")
    try:
        return RunStart(run_id=service.start_run(payload.phone, ip))
    except service.RunOwnershipError:
        raise HTTPException(
            status_code=409, detail="این شماره همین الان در حالِ بازی از یک دستگاهِ دیگر است"
        )


@router.post("/api/run/tick")
def tick_run(payload: RunTick, request: Request):
    if not service.run_tick_limiter.allow(_client_ip(request)):
        raise HTTPException(status_code=429, detail="کمی صبر کنید و دوباره تلاش کنید")
    try:
        service.tick_run(payload.phone, payload.run_id, payload.score)
    except service.InvalidRunError:
        raise HTTPException(status_code=400, detail="این دور نامعتبر یا تمام‌شده است")
    except service.ImplausibleScoreError:
        raise HTTPException(status_code=422, detail="امتیاز با مدتِ دور نمی‌خواند")
    return {"ok": True}


@router.post("/api/score", response_model=SubmitResult)
def submit_score(payload: ScoreSubmit, request: Request, db: Session = Depends(get_db)):
    if not service.score_submit_limiter.allow(_client_ip(request)):
        raise HTTPException(status_code=429, detail="کمی صبر کنید و دوباره تلاش کنید")
    try:
        entry, is_record = service.submit_score(
            db, payload.name, payload.phone, payload.score, payload.run_id
        )
    except service.TooFastError:
        raise HTTPException(status_code=429, detail="کمی صبر کنید و دوباره تلاش کنید")
    except service.InvalidRunError:
        raise HTTPException(status_code=400, detail="این دور نامعتبر یا تمام‌شده است")
    except service.ImplausibleScoreError:
        raise HTTPException(status_code=422, detail="امتیاز با مدتِ دور نمی‌خواند")

    rank, total = service.rank_and_total(db, entry)
    return SubmitResult(
        rank=rank,
        best_score=entry.best_score,
        is_record=is_record,
        total_players=total,
        leaderboard=service.top_rows(db, BOARD_SIZE),
    )


@router.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")
