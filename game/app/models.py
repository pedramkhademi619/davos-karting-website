"""جدول‌های سرویسِ صفحهٔ «به‌زودی»."""

from sqlalchemy import Column, Date, DateTime, Integer, String, func

from .db import Base


class LeaderboardEntry(Base):
    """
    یک ردیف به ازای هر بازیکن. شناسهٔ بازیکن شمارهٔ تلفن است (نه نام)، چون
    نام تکراری می‌شود ولی شماره یکتاست؛ پس هر بار همان شماره دوباره بازی کند،
    همین ردیف به‌روز می‌شود و ردیفِ تازه‌ای ساخته نمی‌شود.
    """

    __tablename__ = "leaderboard_entries"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False)
    # فقط بهترین رکورد نگه داشته می‌شود؛ دورهای ضعیف‌تر رکورد را خراب نمی‌کنند.
    best_score = Column(Integer, nullable=False, default=0, server_default="0")
    plays = Column(Integer, nullable=False, default=0, server_default="0")
    # بهترین رکوردِ همین هفته — با شروعِ هفتهٔ تازه (شنبه) صفر می‌شود؛
    # week_start همان شنبه‌ای‌ست که weekly_best_score متعلق به آن است.
    weekly_best_score = Column(Integer, nullable=False, default=0, server_default="0")
    week_start = Column(Date, nullable=True)
    # بهترین رکوردِ همین ماهِ شمسی؛ month_key = سال*۱۰۰ + ماه (مثلاً ۱۴۰۵۰۶ = شهریورِ ۱۴۰۵).
    monthly_best_score = Column(Integer, nullable=False, default=0, server_default="0")
    month_key = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
