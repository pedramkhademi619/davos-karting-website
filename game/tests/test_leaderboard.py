import time

from app import service


def _start(client, phone="09121234567"):
    return client.post("/api/run", json={"phone": phone}).json()["run_id"]


def submit(client, name="رضا", phone="09121234567", score=100, run_id=None, age=1000.0):
    """
    اگر run_id داده نشود، اول یک دور شروع می‌کند و مثلِ یک کلاینتِ درست‌رفتار وانمود می‌کند
    که `age` ثانیه پیش شروع شده و همین الان یک ضربان با امتیازِ نهایی فرستاده.
    """
    if run_id is None:
        started = client.post("/api/run", json={"phone": phone})
        run_id = started.json()["run_id"] if started.status_code == 200 else "x" * 16
        run = service._runs.get(phone)
        if run is not None:
            run.started -= age
            run.last_tick_at = time.monotonic()
            run.last_tick_score = score
    return client.post(
        "/api/score", json={"name": name, "phone": phone, "score": score, "run_id": run_id}
    )


def _tick(client, run_id, score, phone="09121234567", after=3.0):
    """بین دو ضربان `after` ثانیه‌ی سرور می‌گذراند (ساعتِ دورِ فعلی را عقب می‌کشد) و ضربان می‌فرستد."""
    run = service._runs[phone]
    run.last_tick_at -= after
    run.started -= after
    return client.post("/api/run/tick", json={"phone": phone, "run_id": run_id, "score": score})


def test_first_submission_creates_entry_and_returns_rank(client):
    res = submit(client, score=420)
    assert res.status_code == 200
    body = res.json()
    assert body["rank"] == 1
    assert body["best_score"] == 420
    assert body["is_record"] is True
    assert body["total_players"] == 1
    assert body["leaderboard"][0]["name"] == "رضا"


def test_same_phone_updates_the_same_row_not_a_new_one(client):
    submit(client, name="رضا", score=300)
    service._last_submit.clear()
    res = submit(client, name="رضا", score=500)
    body = res.json()
    assert body["total_players"] == 1
    assert body["best_score"] == 500
    assert body["leaderboard"][0]["plays"] == 2


def test_weaker_run_does_not_overwrite_best(client):
    submit(client, score=900)
    service._last_submit.clear()
    res = submit(client, score=200)
    body = res.json()
    assert body["best_score"] == 900
    assert body["is_record"] is False


def test_name_change_on_same_phone_replaces_the_name(client):
    submit(client, name="رضا", score=100)
    service._last_submit.clear()
    submit(client, name="رضا کریمی", score=50)
    rows = client.get("/api/leaderboard").json()
    assert len(rows) == 1
    assert rows[0]["name"] == "رضا کریمی"


def test_same_name_different_phones_are_separate_players(client):
    submit(client, name="علی", phone="09120000001", score=100)
    submit(client, name="علی", phone="09120000002", score=200)
    rows = client.get("/api/leaderboard").json()
    assert len(rows) == 2


def test_leaderboard_is_sorted_and_masks_phones(client):
    submit(client, name="الف", phone="09120000001", score=100)
    submit(client, name="ب", phone="09120000002", score=300)
    submit(client, name="پ", phone="09120000003", score=200)
    rows = client.get("/api/leaderboard").json()
    assert [r["name"] for r in rows] == ["ب", "پ", "الف"]
    assert [r["rank"] for r in rows] == [1, 2, 3]
    for r in rows:
        assert "***" in r["phone_masked"]
        assert "phone" not in r
    assert rows[0]["phone_masked"] == "0912***0002"


def test_rank_reported_even_outside_top_ten(client):
    for i in range(12):
        submit(client, name=f"p{i}", phone=f"091200000{i:02d}", score=1000 - i * 10)
    res = submit(client, name="آخر", phone="09129999999", score=5)
    body = res.json()
    assert body["rank"] == 13
    assert len(body["leaderboard"]) == 10


def test_invalid_phone_rejected(client):
    res = submit(client, phone="12345")
    assert res.status_code == 422


def test_empty_name_rejected(client):
    res = submit(client, name="   ")
    assert res.status_code == 422


def test_absurd_score_rejected(client):
    res = submit(client, score=10_000_000)
    assert res.status_code == 422


def test_rapid_repeat_submission_is_throttled(client):
    assert submit(client, score=10).status_code == 200
    assert submit(client, score=20).status_code == 429


def test_live_leaderboard_includes_recent_players(client):
    submit(client, name="نوید", phone="09121112233", score=300)
    service._last_submit.clear()
    submit(client, name="سارا", phone="09121112244", score=500)
    res = client.get("/api/leaderboard/live")
    assert res.status_code == 200
    body = res.json()
    assert body["count"] == 2
    assert [r["name"] for r in body["rows"]] == ["سارا", "نوید"]


def test_live_leaderboard_excludes_stale_players(client):
    from datetime import datetime, timedelta, timezone

    from app.db import SessionLocal
    from app.models import LeaderboardEntry

    submit(client, name="قدیمی", phone="09121112255", score=999)
    db = SessionLocal()
    entry = db.query(LeaderboardEntry).filter(LeaderboardEntry.phone == "09121112255").first()
    entry.updated_at = datetime.now(timezone.utc) - timedelta(hours=5)
    db.commit()
    db.close()

    res = client.get("/api/leaderboard/live")
    body = res.json()
    assert body["count"] == 0
    assert body["rows"] == []


def test_player_lookup_returns_known_name(client):
    submit(client, name="محمد", phone="09121112266", score=50)
    res = client.get("/api/player/09121112266")
    assert res.status_code == 200
    assert res.json()["name"] == "محمد"


def test_player_lookup_unknown_phone_is_404(client):
    res = client.get("/api/player/09129999999")
    assert res.status_code == 404


def test_player_lookup_invalid_phone_is_422(client):
    res = client.get("/api/player/12345")
    assert res.status_code == 422


def test_weekly_leaderboard_includes_this_weeks_score(client):
    submit(client, name="نگین", phone="09121112277", score=650)
    res = client.get("/api/leaderboard?scope=weekly")
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 1
    assert body[0]["name"] == "نگین"
    assert body[0]["score"] == 650

    # جدولِ همیشگی هم باید بی‌اثر از پارامترِ scope همین رکورد را نشان بدهد.
    all_time = client.get("/api/leaderboard").json()
    assert all_time[0]["score"] == 650


def test_weekly_leaderboard_excludes_a_previous_weeks_entry(client):
    from datetime import date, timedelta

    from app.db import SessionLocal
    from app.models import LeaderboardEntry

    submit(client, name="قدیمی۲", phone="09121112288", score=900)
    db = SessionLocal()
    entry = db.query(LeaderboardEntry).filter(LeaderboardEntry.phone == "09121112288").first()
    entry.week_start = date.today() - timedelta(days=14)
    db.commit()
    db.close()

    weekly = client.get("/api/leaderboard?scope=weekly").json()
    assert weekly == []

    # ولی رکوردِ همیشگی همچنان دیده می‌شود — چیزی حذف نشده، فقط از جدولِ هفتگی بیرون است.
    all_time = client.get("/api/leaderboard").json()
    assert any(r["name"] == "قدیمی۲" for r in all_time)


def test_weekly_score_resets_even_if_new_score_is_lower(client):
    from datetime import date, timedelta

    from app.db import SessionLocal
    from app.models import LeaderboardEntry

    submit(client, name="آرش", phone="09121112299", score=800)
    db = SessionLocal()
    entry = db.query(LeaderboardEntry).filter(LeaderboardEntry.phone == "09121112299").first()
    entry.week_start = date.today() - timedelta(days=7)
    db.commit()
    db.close()

    service._last_submit.clear()
    submit(client, name="آرش", phone="09121112299", score=50)

    weekly = client.get("/api/leaderboard?scope=weekly").json()
    assert weekly[0]["score"] == 50
    # ولی رکوردِ همیشگی (۸۰۰) دست‌نخورده می‌ماند.
    all_time = client.get("/api/leaderboard").json()
    assert all_time[0]["score"] == 800


def test_score_without_run_id_is_rejected(client):
    res = client.post(
        "/api/score", json={"name": "رضا", "phone": "09121234567", "score": 100}
    )
    assert res.status_code == 422


def test_forged_run_id_is_rejected(client):
    assert submit(client, run_id="a" * 22).status_code == 400


def test_run_id_is_single_use(client):
    run_id = _start(client)
    assert submit(client, run_id=run_id, score=100).status_code == 200
    service._last_submit.clear()
    assert submit(client, run_id=run_id, score=100).status_code == 400


def test_run_id_is_bound_to_its_phone(client):
    run_id = _start(client, "09120000001")
    assert submit(client, phone="09120000002", run_id=run_id, score=100).status_code == 400


def test_score_impossible_for_elapsed_time_is_rejected_and_burns_the_run(client):
    run_id = _start(client)
    assert submit(client, run_id=run_id, score=99_999).status_code == 422
    service._last_submit.clear()
    # امتیازِ جعلی دورِ او را سوزانده؛ با همان شناسه دیگر نمی‌شود امتیازِ درست فرستاد.
    assert submit(client, run_id=run_id, score=100).status_code == 400


def test_score_within_the_time_budget_is_accepted(client):
    run_id = _start(client)
    run = service._runs["09121234567"]
    run.started -= 100
    run.last_tick_at = time.monotonic()
    run.last_tick_score = 19_900
    assert submit(client, run_id=run_id, score=20_000).status_code == 200


def test_wrong_run_id_does_not_burn_the_real_run(client):
    run_id = _start(client)
    assert submit(client, run_id="b" * 22, score=10).status_code == 400
    service._last_submit.clear()
    assert submit(client, run_id=run_id, score=10).status_code == 200


def test_gregorian_to_jalali_reference_dates():
    j = service._gregorian_to_jalali
    assert j(2024, 3, 20) == (1403, 1, 1)     # اولِ فروردینِ سالِ کبیسه
    assert j(2025, 3, 21) == (1404, 1, 1)
    assert j(2026, 3, 20) == (1404, 12, 29)   # آخرِ اسفندِ ۱۴۰۴ (۲۹ روزه)
    assert j(2026, 3, 21) == (1405, 1, 1)
    assert j(2026, 9, 22) == (1405, 6, 31)    # آخرِ شهریور
    assert j(2026, 9, 23) == (1405, 7, 1)     # اولِ مهر


def test_month_key_uses_tehran_time_at_the_boundary():
    from datetime import datetime, timezone

    # ۲۲ سپتامبر ۲۰۲۶، ۲۰:۴۵ UTC = ۲۳ سپتامبر ۰۰:۱۵ تهران → اولِ مهر
    assert service._current_month_key(datetime(2026, 9, 22, 20, 45, tzinfo=timezone.utc)) == 140507
    # نیم‌ساعت زودتر هنوز شهریور است
    assert service._current_month_key(datetime(2026, 9, 22, 20, 15, tzinfo=timezone.utc)) == 140506


def test_monthly_leaderboard_includes_this_months_score(client):
    submit(client, name="مینا", phone="09121113301", score=700)
    body = client.get("/api/leaderboard?scope=monthly").json()
    assert [r["name"] for r in body] == ["مینا"]
    assert body[0]["score"] == 700


def test_monthly_leaderboard_excludes_a_previous_month_but_keeps_all_time(client):
    from app.db import SessionLocal
    from app.models import LeaderboardEntry

    submit(client, name="ماهِ پیش", phone="09121113302", score=900)
    db = SessionLocal()
    entry = db.query(LeaderboardEntry).filter(LeaderboardEntry.phone == "09121113302").first()
    entry.month_key = service._current_month_key() - 1
    db.commit()
    db.close()

    assert client.get("/api/leaderboard?scope=monthly").json() == []
    assert any(r["name"] == "ماهِ پیش" for r in client.get("/api/leaderboard").json())


def test_monthly_score_resets_in_a_new_month_even_if_lower(client):
    from app.db import SessionLocal
    from app.models import LeaderboardEntry

    submit(client, name="ساره", phone="09121113303", score=800)
    db = SessionLocal()
    entry = db.query(LeaderboardEntry).filter(LeaderboardEntry.phone == "09121113303").first()
    entry.month_key = service._current_month_key() - 1
    db.commit()
    db.close()

    service._last_submit.clear()
    submit(client, name="ساره", phone="09121113303", score=60)
    assert client.get("/api/leaderboard?scope=monthly").json()[0]["score"] == 60
    assert client.get("/api/leaderboard").json()[0]["score"] == 800


def test_steady_ticks_then_submit_is_accepted(client):
    run_id = _start(client)
    total = 0
    for _ in range(10):
        total += 600
        assert _tick(client, run_id, total).status_code == 200
    service._runs["09121234567"].last_tick_at = time.monotonic() - 1
    assert submit(client, run_id=run_id, score=total + 100).status_code == 200


def test_waiting_ten_minutes_then_claiming_a_huge_score_is_rejected(client):
    run_id = _start(client)
    run = service._runs["09121234567"]
    run.started -= 600        # ده دقیقه صبر، بدونِ هیچ ضربانی
    run.last_tick_at -= 600
    res = submit(client, run_id=run_id, score=90_000)
    assert res.status_code == 422


def test_tick_that_jumps_too_far_burns_the_run(client):
    run_id = _start(client)
    assert _tick(client, run_id, 5_000).status_code == 422
    assert client.post(
        "/api/run/tick", json={"phone": "09121234567", "run_id": run_id, "score": 10}
    ).status_code == 400


def test_score_going_backwards_burns_the_run(client):
    run_id = _start(client)
    assert _tick(client, run_id, 600).status_code == 200
    assert _tick(client, run_id, 100).status_code == 422


def test_ticks_faster_than_the_pace_are_ignored(client):
    run_id = _start(client)
    res = client.post("/api/run/tick", json={"phone": "09121234567", "run_id": run_id, "score": 5_000})
    assert res.status_code == 200
    assert service._runs["09121234567"].last_tick_score == 0


def test_final_score_far_above_the_last_tick_is_rejected(client):
    run_id = _start(client)
    assert _tick(client, run_id, 600).status_code == 200
    service._runs["09121234567"].last_tick_at = time.monotonic() - 2
    assert submit(client, run_id=run_id, score=4_000).status_code == 422


# ---------------- مالکیتِ دور بر اساسِ IP (S1) ----------------

def test_run_cannot_be_hijacked_by_a_different_ip_while_actively_playing(client):
    phone = "09121119001"
    run_id = client.post("/api/run", json={"phone": phone}).json()["run_id"]
    assert _tick(client, run_id, 100, phone=phone).status_code == 200  # حالا واقعاً "در حالِ بازی" است

    attacker = client.post(
        "/api/run", json={"phone": phone}, headers={"X-Forwarded-For": "203.0.113.9"}
    )
    assert attacker.status_code == 409
    # و دورِ صاحبِ اصلی هم دست‌نخورده مانده — با همون run_id قبلی هنوز می‌شود ضربان زد.
    assert _tick(client, run_id, 200, phone=phone).status_code == 200


def test_run_can_be_restarted_from_a_different_ip_if_not_actively_playing(client):
    phone = "09121119002"
    client.post("/api/run", json={"phone": phone})  # هیچ ضربانی نمی‌فرستیم — یعنی واقعاً بازی نشده
    other = client.post(
        "/api/run", json={"phone": phone}, headers={"X-Forwarded-For": "203.0.113.9"}
    )
    assert other.status_code == 200


def test_run_can_be_restarted_from_the_same_ip(client):
    phone = "09121119003"
    run_id = client.post("/api/run", json={"phone": phone}).json()["run_id"]
    assert _tick(client, run_id, 100, phone=phone).status_code == 200
    again = client.post("/api/run", json={"phone": phone})  # همون کلاینت (بدونِ XFF)، مثلاً رفرشِ صفحه
    assert again.status_code == 200


# ---------------- محدودیتِ نرخ per-IP (S1/S5) ----------------

def test_run_start_is_rate_limited_per_ip(client):
    for i in range(service.run_start_limiter.max_hits):
        assert client.post("/api/run", json={"phone": f"0912111910{i:01d}"[:11]}).status_code == 200
    res = client.post("/api/run", json={"phone": "09121119099"})
    assert res.status_code == 429


def test_player_lookup_is_rate_limited_per_ip(client):
    for _ in range(service.player_lookup_limiter.max_hits):
        client.get("/api/player/09121119999")
    res = client.get("/api/player/09121119999")
    assert res.status_code == 429


def test_run_tick_is_rate_limited_per_ip(client):
    phone = "09121119004"
    run_id = client.post("/api/run", json={"phone": phone}).json()["run_id"]
    for _ in range(service.run_tick_limiter.max_hits):
        client.post("/api/run/tick", json={"phone": phone, "run_id": run_id, "score": 0})
    res = client.post("/api/run/tick", json={"phone": phone, "run_id": run_id, "score": 0})
    assert res.status_code == 429


# ---------------- تشخیصِ سرعتِ غیرطبیعی‌یکنواخت (S2) ----------------

def test_looks_bot_flat_flags_a_perfectly_steady_rate():
    assert service._looks_bot_flat([250.0] * 6) is True


def test_looks_bot_flat_ignores_bursty_human_like_play():
    assert service._looks_bot_flat([40, 180, 20, 250, 60, 150]) is False


def test_looks_bot_flat_ignores_a_slow_steady_pace():
    # یکنواخت است ولی آن‌قدر کند که مشکوک نیست (زیرِ SUSPICIOUS_FLAT_MIN_RATE).
    assert service._looks_bot_flat([30.0] * 6) is False


def test_looks_bot_flat_needs_enough_samples():
    assert service._looks_bot_flat([200.0, 200.0]) is False


def test_steady_paced_ticks_are_logged_as_suspicious(client, caplog):
    phone = "09121119005"
    run_id = client.post("/api/run", json={"phone": phone}).json()["run_id"]
    with caplog.at_level("WARNING", logger="landing.antiabuse"):
        score = 0
        for _ in range(6):
            score += 750  # هر بار دقیقاً ۳ ثانیه بعد، دقیقاً همون مقدار — خیلی صاف
            assert _tick(client, run_id, score, phone=phone).status_code == 200
        service._runs[phone].last_tick_at = time.monotonic() - 2
        submit(client, phone=phone, score=score, run_id=run_id)
    assert any("unnaturally steady pace" in r.message for r in caplog.records)


def test_a_real_high_skill_run_with_bursty_ticks_is_accepted(client):
    """
    رگرسیونِ واقعی: یه دورِ ۵۰هزاری با نیتروی مداوم + رشته‌سکه‌های پرمگنت پیش
    اومد ولی سرور بهش ۴۲۲ داد چون MAX_SCORE_PER_SECOND برای نسخهٔ سخت‌ترِ قبلیِ
    بازی تنظیم شده بود. بازی نوسانی امتیاز می‌ده (سکه‌های جهشی + پایهٔ پیوسته)،
    نه یکنواخت — همینو شبیه‌سازی می‌کنیم: میانگین ~۳۸۰/ثانیه با نوسانِ واقعی.
    """
    phone = "09121119006"
    run_id = client.post("/api/run", json={"phone": phone}).json()["run_id"]
    score = 0
    # ۱۲ ضربان، هر ۳ ثانیه؛ افزایشِ هر ضربان بینِ ۹۰۰ تا ۱۵۰۰ (میانگین ~۱۲۰۰ در ۳ ثانیه = ۴۰۰/ثانیه)
    deltas = [900, 1500, 1000, 1400, 950, 1300, 1100, 1450, 1000, 1350, 1050, 1200]
    for d in deltas:
        score += d
        assert _tick(client, run_id, score, phone=phone).status_code == 200
    assert score > 13_000
    service._runs[phone].last_tick_at = time.monotonic() - 2
    res = submit(client, phone=phone, score=score, run_id=run_id)
    assert res.status_code == 200
    assert res.json()["best_score"] == score


def test_a_50k_run_over_a_realistic_duration_is_accepted(client):
    """همون رگرسیون، ولی مستقیماً عددِ گزارش‌شده (۵۰,۵۸۲) روی یه دورِ به‌اندازه‌کافی‌طولانی."""
    phone = "09121119007"
    run_id = client.post("/api/run", json={"phone": phone}).json()["run_id"]
    run = service._runs[phone]
    run.started -= 140  # ~۲.۳ دقیقه دورِ واقعی — با سقفِ فعلی (۵۰۰/ثانیه) کاملاً منطقی
    run.last_tick_at = time.monotonic() - 2
    run.last_tick_score = 50_000
    run.tick_count = 40
    res = submit(client, phone=phone, score=50_582, run_id=run_id)
    assert res.status_code == 200
    assert res.json()["best_score"] == 50_582


def test_index_page_served(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "خط استارت داووس" in res.text
