"""قراردادهای ورودی/خروجیِ API."""

import re

from pydantic import BaseModel, Field, field_validator

PHONE_PATTERN = re.compile(r"^09\d{9}$")

# سقفِ منطقیِ امتیاز، فقط برای جلوگیری از مقادیرِ بی‌معنا در ورودی.
MAX_SCORE = 100_000


def _check_phone(value: str) -> str:
    if not PHONE_PATTERN.match(value):
        raise ValueError("شماره تماس باید یک شماره موبایل معتبر ایرانی باشد (مثال: 09123456789)")
    return value


class RunRequest(BaseModel):
    phone: str = Field(..., min_length=11, max_length=11)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return _check_phone(value)


class RunStart(BaseModel):
    run_id: str


class RunTick(BaseModel):
    """ضربانِ حینِ بازی: امتیازِ لحظه‌ایِ همین دور."""

    phone: str = Field(..., min_length=11, max_length=11)
    run_id: str = Field(..., pattern=r"^[A-Za-z0-9_-]{16,64}$")
    score: int = Field(..., ge=0, le=MAX_SCORE)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return _check_phone(value)


class ScoreSubmit(BaseModel):
    name: str = Field(..., min_length=1, max_length=40)
    phone: str = Field(..., min_length=11, max_length=11)
    score: int = Field(..., ge=0, le=MAX_SCORE)
    # شناسهٔ یک‌بارمصرفِ دور که سرور در شروعِ بازی داده؛ بدونِ آن امتیاز پذیرفته نمی‌شود.
    run_id: str = Field(..., pattern=r"^[A-Za-z0-9_-]{16,64}$")

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        stripped = " ".join(value.split())
        if not stripped:
            raise ValueError("نام نمی‌تواند خالی باشد")
        return stripped

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return _check_phone(value)


class LeaderboardRow(BaseModel):
    rank: int
    name: str
    # شمارهٔ کامل هرگز به بیرون داده نمی‌شود؛ فقط نسخهٔ ماسک‌شده برای اینکه
    # بازیکن ردیفِ خودش را بشناسد.
    phone_masked: str
    score: int
    plays: int


class SubmitResult(BaseModel):
    rank: int
    best_score: int
    is_record: bool
    total_players: int
    leaderboard: list[LeaderboardRow]


class LiveBoard(BaseModel):
    """جدولِ «همین الان تو سالن» — فقط کسانی که به‌تازگی بازی کرده‌اند."""

    count: int
    rows: list[LeaderboardRow]


class PlayerLookup(BaseModel):
    name: str
