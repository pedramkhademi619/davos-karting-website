"""منطقِ جدولِ رکوردها."""

import logging
import secrets
import time
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from .models import LeaderboardEntry
from .schemas import LeaderboardRow

# حداقل فاصلهٔ بین دو ثبتِ امتیاز از یک شماره — جلوی اسپمِ ساده را می‌گیرد.
MIN_SUBMIT_GAP_SECONDS = 2.0
_last_submit: dict[str, float] = {}

# پنجرهٔ «همین الان تو سالن»: هرکس در این بازه بازی کرده، حاضر حساب می‌شود —
# تقریباً یک شیفتِ انتظار و بازی.
LIVE_WINDOW_MINUTES = 180

# هفته به وقتِ تهران از شنبه شروع می‌شود.
_TEHRAN_OFFSET = timezone(timedelta(hours=3, minutes=30))


def _current_week_start(now: datetime | None = None) -> date:
    now = now or datetime.now(timezone.utc)
    local = now.astimezone(_TEHRAN_OFFSET)
    # Python: Monday=0 ... Saturday=5, Sunday=6
    days_since_saturday = (local.weekday() - 5) % 7
    return (local - timedelta(days=days_since_saturday)).date()


def _gregorian_to_jalali(gy: int, gm: int, gd: int) -> tuple[int, int, int]:
    """تبدیلِ میلادی به شمسی (الگوریتمِ استانداردِ jdf) — برای اینکه ماهِ جدول، ماهِ شمسی باشد."""
    cum = (0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334)
    gy2 = gy + 1 if gm > 2 else gy
    days = 355666 + 365 * gy + (gy2 + 3) // 4 - (gy2 + 99) // 100 + (gy2 + 399) // 400 + gd + cum[gm - 1]
    jy = -1595 + 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm, jd = 1 + days // 31, 1 + days % 31
    else:
        jm, jd = 7 + (days - 186) // 30, 1 + (days - 186) % 30
    return jy, jm, jd


def _current_month_key(now: datetime | None = None) -> int:
    """سال*۱۰۰ + ماهِ شمسیِ فعلی به وقتِ تهران؛ مثلاً شهریورِ ۱۴۰۵ → ۱۴۰۵۰۶."""
    now = now or datetime.now(timezone.utc)
    local = now.astimezone(_TEHRAN_OFFSET)
    jy, jm, _ = _gregorian_to_jalali(local.year, local.month, local.day)
    return jy * 100 + jm


class TooFastError(Exception):
    """ثبتِ پشت‌سرهم و خیلی سریع از یک شماره."""


class InvalidRunError(Exception):
    """شناسهٔ دور وجود ندارد، برای این شماره نیست، قبلاً مصرف شده یا منقضی است."""


class ImplausibleScoreError(Exception):
    """امتیاز با مدتِ واقعیِ دور جور درنمی‌آید."""


class RunOwnershipError(Exception):
    """این شماره همین الان یک دورِ فعال و در حالِ بازی دارد که از یک IPِ دیگر شروع شده."""


class RateLimitedError(Exception):
    """این IP بیش از حدِ مجاز درخواست فرستاده."""


class RateLimiter:
    """محدودکنندهٔ نرخِ ساده — پنجرهٔ لغزان، فقط در حافظه (هم‌راستا با بقیهٔ حالتِ این سرویس)."""

    def __init__(self, max_hits: int, window_seconds: float):
        self.max_hits = max_hits
        self.window_seconds = window_seconds
        self._hits: dict[str, list[float]] = {}

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        hits = [t for t in self._hits.get(key, ()) if t > cutoff]
        if len(hits) >= self.max_hits:
            self._hits[key] = hits
            return False
        hits.append(now)
        self._hits[key] = hits
        return True

    def clear(self) -> None:
        self._hits.clear()


# محدودیتِ نرخِ per-IP روی مسیرهایی که می‌شود با آن‌ها یا دورِ یکی دیگر را باطل کرد
# (start_run با حدسِ شماره)، یا شماره‌ها را یکی‌یکی امتحان کرد و دید کدام قبلاً
# بازی کرده‌اند (player_lookup). هر سه مسیر یک لیمیترِ جدا دارند تا رفتارِ عادی
# در یکی، سهمیهٔ مسیرِ دیگر را نخورد.
# این سرویس داخلِ سالنِ کارتینگ استفاده می‌شود — خیلی از بازیکن‌ها پشتِ یک
# وای‌فای/NATِ مشترک هستند، پس همه از یک IP دیده می‌شوند. سقف‌ها برای همزمانیِ
# واقعیِ چندین بازیکنِ هم‌زمان از یک IP سخاوتمندند؛ مقابلهٔ اصلی با حدس‌زدنِ
# شمارهٔ یک نفرِ خاص (S1) از طریقِ همین لیمیترها نیست، بلکه با مالکیتِ IPِ خودِ
# دور است (بالاتر، RunOwnershipError) که به‌ازای هر شماره جدا عمل می‌کند.
run_start_limiter = RateLimiter(max_hits=40, window_seconds=60)
run_tick_limiter = RateLimiter(max_hits=150, window_seconds=60)  # هر بازیکن هر ۳ ثانیه یک ضربان (~۲۰/دقیقه)
score_submit_limiter = RateLimiter(max_hits=40, window_seconds=60)
player_lookup_limiter = RateLimiter(max_hits=40, window_seconds=60)

# یک دورِ «در حالِ بازیِ واقعی» (حداقل یک ضربانِ واقعی داشته و به‌تازگی هم فعال
# بوده) را از IPِ دیگری نمی‌شود باطل کرد؛ فقط دورِ رهاشده/تازه‌شروع‌شده جایگزین می‌شود.
RUN_PROTECT_SECONDS = 45.0


# امتیازِ بازی در سمتِ کلاینت ساخته می‌شود، پس سرور نمی‌تواند خودِ عدد را باور کند.
# به‌جایش سرور «مسیرِ دور» را با ساعتِ خودش می‌سنجد (نه ساعتِ کلاینت):
#  ۱) هر دور با یک شناسهٔ یک‌بارمصرف از /api/run شروع می‌شود؛
#  ۲) کلاینت هر ~۳ ثانیه یک ضربان (امتیازِ لحظه‌ای) می‌فرستد و سرور هر ضربان را با
#     زمانِ واقعیِ سپری‌شده از ضربانِ قبلی می‌سنجد؛
#  ۳) امتیازِ نهایی فقط وقتی پذیرفته می‌شود که ضربانِ تازه (≤ TICK_STALE_SECONDS پیش)
#     پشتش باشد و از آن ضربان به بعد هم با زمان بخواند.
# پس «۱۰ دقیقه صبر کن، بعد هر عددی بفرست» کار نمی‌کند: امتیاز فقط با گذشتنِ واقعیِ
# زمان و ضربان‌های پیوسته بالا می‌رود.
# سقف از خودِ بازی درآمده — ولی حواس‌جمع: این مقادیر باید هر بار که موتورِ
# بازی/اقتصادِ سکه عوض می‌شود، دوباره حساب شوند؛ یک بارِ قبلی (۲۵۰) بر اساسِ
# نسخهٔ سخت‌ترِ بازی بسته شده بود و یک دورِ واقعیِ ۵۰هزاری را همین‌جا رد کرده بود.
# حساب با تنظیماتِ فعلی: پایه (نیترو+حداکثرِ سرعت) ≈ ۱۲۸/ثانیه + اسلیپ‌استریم
# ≈ ۱۴۳/ثانیه؛ سکه‌ها با مگنتِ ماکس + کمبوِ ۵× + آیتمِ x2 هر سکه تا ۱۰۰ امتیاز و
# رشته‌ای هر ~۲.۴ ثانیه می‌آیند (تا ۶ تایی) → می‌تواند تا ~۲۵۰/ثانیهٔ دیگر اضافه
# کند. جمعِ واقع‌بینانه برایِ یک بازیکنِ خیلی حرفه‌ای و آپگریدشده در اوجِ شانس
# ≈ ۴۰۰/ثانیه؛ سقف و حاشیه‌ها با فاصلهٔ امن از این عدد تنظیم شده‌اند.
MAX_SCORE_PER_SECOND = 500
SCORE_SLACK = 1000
TICK_BURST = 700           # جهشِ مجاز در یک پنجره (رشتهٔ سکه با ضریبِ بالا)
MIN_TICK_GAP_SECONDS = 2.0  # ضربانِ سریع‌تر نادیده گرفته می‌شود
TICK_STALE_SECONDS = 15.0
RUN_MAX_AGE_SECONDS = 2 * 60 * 60
MAX_OPEN_RUNS = 5000
# دورهای مشکوک (میانگینِ امتیازِ بالا در مدتِ طولانی، یا سرعتِ غیرطبیعی یکنواخت) در
# لاگ ثبت می‌شوند تا مالک قبل از تأییدِ جایزه ببیند — این یک قضاوتِ نرم است، نه ردِ
# خودکار: بازیِ واقعی هم می‌تواند به‌طورِ اتفاقی چند ضربانِ نزدیک‌به‌هم بدهد، پس
# رد کردنِ خودکارِ آن ریسکِ مثبتِ کاذب دارد. تأییدِ نهاییِ جایزهٔ ماهانه باید حضوری
# باشد (نکته: این حدِ سرور فقط «یکنواختیِ مشکوک» را نشان می‌دهد، جلوی یک ربات
# صبور و باتغییرِ عمدیِ سرعت را نمی‌گیرد — S2 در گزارش امنیتی).
SUSPICIOUS_RATE = 340
SUSPICIOUS_MIN_SECONDS = 20
SUSPICIOUS_FLAT_SAMPLES = 5     # حداقل تعداد ضربان برای قضاوت دربارهٔ یکنواختی
SUSPICIOUS_FLAT_CV = 0.04       # ضریبِ تغییراتِ (انحرافِ‌معیار/میانگین) زیرِ این یعنی «خیلی صاف»
SUSPICIOUS_FLAT_MIN_RATE = SUSPICIOUS_RATE * 0.6
_log = logging.getLogger("landing.antiabuse")


class _Run:
    __slots__ = (
        "run_id",
        "started",
        "last_tick_at",
        "last_tick_score",
        "owner_ip",
        "tick_count",
        "rate_samples",
    )

    def __init__(self, run_id: str, now: float, owner_ip: str):
        self.run_id = run_id
        self.started = now
        self.last_tick_at = now
        self.last_tick_score = 0
        self.owner_ip = owner_ip
        self.tick_count = 0
        self.rate_samples: list[float] = []


def _looks_bot_flat(samples: list[float]) -> bool:
    """
    آیا رشتهٔ سرعت‌های امتیازگیری غیرطبیعی یکنواخت است؟ بازیِ واقعی پر از سکه/جاخالی/
    برخورد است، پس سرعتش نوسان دارد؛ اسکریپتی که ساده «elapsed × نرخ» حساب کند، نه.
    """
    if len(samples) < SUSPICIOUS_FLAT_SAMPLES:
        return False
    mean = sum(samples) / len(samples)
    if mean < SUSPICIOUS_FLAT_MIN_RATE:
        return False
    variance = sum((s - mean) ** 2 for s in samples) / len(samples)
    cv = (variance**0.5) / mean if mean else 0.0
    return cv < SUSPICIOUS_FLAT_CV


# شماره → دورِ فعلی. فقط در حافظه است، پس سرویس باید تک‌پردازه اجرا شود
# (همین‌طور که الان با یک uvicorn اجرا می‌شود).
_runs: dict[str, _Run] = {}


def start_run(phone: str, owner_ip: str) -> str:
    """
    شروعِ یک دور؛ هر شماره فقط یک دورِ بازِ فعال دارد. اگر دورِ قبلیِ همین شماره
    واقعاً در حالِ بازی باشد (ضربانِ واقعی داشته و به‌تازگی فعال بوده) و این
    درخواست از IPِ دیگری بیاید، رد می‌شود — وگرنه هر کسی با حدسِ یک شماره
    می‌توانست دورِ در حالِ بازیِ آن شخص را همین‌جا بترکاند.
    """
    now = time.monotonic()
    for stale in [p for p, r in _runs.items() if now - r.started > RUN_MAX_AGE_SECONDS]:
        del _runs[stale]

    existing = _runs.get(phone)
    if existing is not None and existing.owner_ip != owner_ip:
        actively_playing = existing.tick_count > 0 and (now - existing.last_tick_at) < RUN_PROTECT_SECONDS
        if actively_playing:
            raise RunOwnershipError()

    _runs.pop(phone, None)
    while len(_runs) >= MAX_OPEN_RUNS:
        del _runs[next(iter(_runs))]
    run_id = secrets.token_urlsafe(16)
    _runs[phone] = _Run(run_id, now, owner_ip)
    return run_id


def _find_run(phone: str, run_id: str) -> _Run:
    run = _runs.get(phone)
    # با شناسهٔ غلط، دورِ واقعیِ آن شماره نباید سوخت (وگرنه هر کسی می‌توانست دورِ دیگری را خراب کند).
    if run is None or not secrets.compare_digest(run.run_id, run_id):
        raise InvalidRunError()
    return run


def tick_run(phone: str, run_id: str, score: int) -> None:
    """ضربانِ حینِ بازی: امتیازِ لحظه‌ای را با ساعتِ سرور می‌سنجد و ثبت می‌کند."""
    run = _find_run(phone, run_id)
    now = time.monotonic()
    if now - run.started > RUN_MAX_AGE_SECONDS:
        del _runs[phone]
        raise InvalidRunError()
    dt = now - run.last_tick_at
    if dt < MIN_TICK_GAP_SECONDS:
        return  # تندتر از حدِ مجاز؛ نادیده، بدونِ اثر
    elapsed = now - run.started
    if (
        score < run.last_tick_score
        or score - run.last_tick_score > dt * MAX_SCORE_PER_SECOND + TICK_BURST
        or score > elapsed * MAX_SCORE_PER_SECOND + SCORE_SLACK
    ):
        del _runs[phone]  # جعل؛ دور می‌سوزد
        raise ImplausibleScoreError()
    if dt > 0:
        run.rate_samples.append((score - run.last_tick_score) / dt)
        del run.rate_samples[:-12]  # فقط چند نمونهٔ اخیر کافی‌ست
    run.last_tick_at = now
    run.last_tick_score = score
    run.tick_count += 1


def _consume_run(phone: str, run_id: str, score: int) -> None:
    run = _find_run(phone, run_id)
    del _runs[phone]
    now = time.monotonic()
    elapsed = now - run.started
    if elapsed > RUN_MAX_AGE_SECONDS:
        raise InvalidRunError()
    since_tick = now - run.last_tick_at
    if since_tick > TICK_STALE_SECONDS:
        raise ImplausibleScoreError()  
    if (
        score < run.last_tick_score
        or score - run.last_tick_score > since_tick * MAX_SCORE_PER_SECOND + TICK_BURST
        or score > elapsed * MAX_SCORE_PER_SECOND + SCORE_SLACK
    ):
        raise ImplausibleScoreError()
    if elapsed >= SUSPICIOUS_MIN_SECONDS and score / elapsed > SUSPICIOUS_RATE:
        _log.warning("suspicious run: phone=%s score=%s seconds=%.0f rate=%.0f/s", phone, score, elapsed, score / elapsed)
    if _looks_bot_flat(run.rate_samples):
        _log.warning(
            "suspicious run: phone=%s score=%s seconds=%.0f rate_samples=%s (unnaturally steady pace)",
            phone, score, elapsed, ["%.0f" % s for s in run.rate_samples],
        )


def get_name_by_phone(db: Session, phone: str) -> str | None:
    """
    اسمِ ثبت‌شده برای این شماره، اگر قبلاً بازی کرده باشد — برای پرشدنِ
    خودکارِ فرمِ ورود، دقیقاً مثلِ auto-fillِ نامِ مشتری در سامانهٔ نوبت‌دهی؛
    یک شماره نباید هر بار زیرِ اسمِ متفاوتی ظاهر شود.
    """
    entry = db.query(LeaderboardEntry).filter(LeaderboardEntry.phone == phone).first()
    return entry.name if entry else None


def mask_phone(phone: str) -> str:
    """۰۹۱۲۱۲۳۴۵۶۷ → ۰۹۱۲***۴۵۶۷ — بازیکن ردیفِ خودش را می‌شناسد، بقیه شماره را نمی‌بینند."""
    if len(phone) != 11:
        return "***"
    return f"{phone[:4]}***{phone[-4:]}"


def _rank_of(db: Session, entry: LeaderboardEntry) -> int:
    better = (
        db.query(LeaderboardEntry)
        .filter(LeaderboardEntry.best_score > entry.best_score)
        .count()
    )
    return better + 1


def top_rows(db: Session, limit: int = 10) -> list[LeaderboardRow]:
    """
    ردیف‌های صدرِ جدول. مرتب‌سازی: امتیازِ بیشتر جلوتر، و در امتیازِ برابر
    هرکس زودتر به آن رکورد رسیده جلوتر است.
    """
    entries = (
        db.query(LeaderboardEntry)
        .order_by(LeaderboardEntry.best_score.desc(), LeaderboardEntry.updated_at.asc())
        .limit(limit)
        .all()
    )
    return [
        LeaderboardRow(
            rank=index + 1,
            name=entry.name,
            phone_masked=mask_phone(entry.phone),
            score=entry.best_score,
            plays=entry.plays,
        )
        for index, entry in enumerate(entries)
    ]


def submit_score(db: Session, name: str, phone: str, score: int, run_id: str):
    """
    ثبتِ نتیجهٔ یک دور. شناسایی بر اساسِ شماره است: اگر این شماره قبلاً بازی
    کرده باشد همان ردیف به‌روز می‌شود (و نامش با نامِ تازه جایگزین می‌شود، چون
    شاید بار اول اشتباه نوشته باشد)؛ رکورد فقط وقتی عوض می‌شود که بهتر باشد.
    """
    now = time.monotonic()
    previous = _last_submit.get(phone)
    if previous is not None and now - previous < MIN_SUBMIT_GAP_SECONDS:
        raise TooFastError()
    _consume_run(phone, run_id, score)
    _last_submit[phone] = now

    entry = db.query(LeaderboardEntry).filter(LeaderboardEntry.phone == phone).first()

    if entry is None:
        entry = LeaderboardEntry(
            phone=phone,
            name=name,
            best_score=score,
            plays=1,
            weekly_best_score=score,
            week_start=_current_week_start(),
            monthly_best_score=score,
            month_key=_current_month_key(),
        )
        db.add(entry)
        try:
            db.commit()
        except IntegrityError:
            # همان شماره در فاصلهٔ بینِ خواندن و نوشتن ساخته شده — دوباره می‌خوانیم.
            db.rollback()
            entry = db.query(LeaderboardEntry).filter(LeaderboardEntry.phone == phone).first()
            if entry is None:
                raise
            return _update_existing(db, entry, name, score)
        db.refresh(entry)
        return entry, True

    return _update_existing(db, entry, name, score)


def _update_existing(db: Session, entry: LeaderboardEntry, name: str, score: int):
    is_record = score > entry.best_score
    entry.name = name
    entry.plays = (entry.plays or 0) + 1
    if is_record:
        entry.best_score = score

    week_start = _current_week_start()
    if entry.week_start != week_start:
        # هفتهٔ تازه شروع شده — رکوردِ هفتگیِ قبلی دیگر معتبر نیست.
        entry.week_start = week_start
        entry.weekly_best_score = score
    elif score > entry.weekly_best_score:
        entry.weekly_best_score = score

    month_key = _current_month_key()
    if entry.month_key != month_key:
        # ماهِ شمسیِ تازه شروع شده — رکوردِ ماهانهٔ قبلی دیگر معتبر نیست.
        entry.month_key = month_key
        entry.monthly_best_score = score
    elif score > entry.monthly_best_score:
        entry.monthly_best_score = score

    entry.updated_at = func.now()
    db.commit()
    db.refresh(entry)
    return entry, is_record


def weekly_rows(db: Session, limit: int = 10) -> list[LeaderboardRow]:
    """
    جدولِ همین هفته (از شنبه). کسی که این هفته بازی نکرده باشد اینجا دیده
    نمی‌شود، حتی اگر رکوردِ هفتهٔ قبل را داشته باشد — این خودِ «ریست‌شدن» است،
    بدون نیاز به هیچ کارِ زمان‌بندی‌شده‌ای.
    """
    week_start = _current_week_start()
    entries = (
        db.query(LeaderboardEntry)
        .filter(LeaderboardEntry.week_start == week_start)
        .order_by(LeaderboardEntry.weekly_best_score.desc(), LeaderboardEntry.updated_at.asc())
        .limit(limit)
        .all()
    )
    return [
        LeaderboardRow(
            rank=index + 1,
            name=entry.name,
            phone_masked=mask_phone(entry.phone),
            score=entry.weekly_best_score,
            plays=entry.plays,
        )
        for index, entry in enumerate(entries)
    ]


def monthly_rows(db: Session, limit: int = 10) -> list[LeaderboardRow]:
    """
    جدولِ همین ماهِ شمسی — همان جدولی که جایزهٔ آخرِ ماه از آن داده می‌شود. مثلِ
    هفتگی، ریست‌شدنش بدونِ کارِ زمان‌بندی‌شده است: کسی که این ماه بازی نکرده اینجا نیست.
    """
    month_key = _current_month_key()
    entries = (
        db.query(LeaderboardEntry)
        .filter(LeaderboardEntry.month_key == month_key)
        .order_by(LeaderboardEntry.monthly_best_score.desc(), LeaderboardEntry.updated_at.asc())
        .limit(limit)
        .all()
    )
    return [
        LeaderboardRow(
            rank=index + 1,
            name=entry.name,
            phone_masked=mask_phone(entry.phone),
            score=entry.monthly_best_score,
            plays=entry.plays,
        )
        for index, entry in enumerate(entries)
    ]


def rank_and_total(db: Session, entry: LeaderboardEntry) -> tuple[int, int]:
    return _rank_of(db, entry), db.query(LeaderboardEntry).count()


def _live_query(db: Session):
    # cutoff در پایتون محاسبه می‌شود، نه با تابعِ datetime(...) که مخصوصِ SQLite
    # است و روی Postgres (دیتابیسِ واقعیِ production) خطای ۵۰۰ می‌داد. updated_at
    # از نوعِ DateTime(timezone=True) است و با func.now() پر می‌شود، پس یک
    # datetime آگاه‌به‌تایم‌زونِ UTC همان چیزی‌ست که باید با آن مقایسه شود.
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=LIVE_WINDOW_MINUTES)
    return db.query(LeaderboardEntry).filter(LeaderboardEntry.updated_at >= cutoff)


def live_rows(db: Session, limit: int = 15) -> list[LeaderboardRow]:
    """رانندگانی که به‌تازگی بازی کرده‌اند — یعنی همین الان تو سالن هستند."""
    entries = (
        _live_query(db)
        .order_by(LeaderboardEntry.best_score.desc(), LeaderboardEntry.updated_at.asc())
        .limit(limit)
        .all()
    )
    return [
        LeaderboardRow(
            rank=index + 1,
            name=entry.name,
            phone_masked=mask_phone(entry.phone),
            score=entry.best_score,
            plays=entry.plays,
        )
        for index, entry in enumerate(entries)
    ]


def live_count(db: Session) -> int:
    return _live_query(db).count()
