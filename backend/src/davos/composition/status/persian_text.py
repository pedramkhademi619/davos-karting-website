from __future__ import annotations

_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def fa(value: object) -> str:
    return str(value).translate(_DIGITS)


def duration(seconds: float) -> str:
    """90 -> "۱ دقیقه"; 7300 -> "۲ ساعت"; short spans are "کمتر از یک دقیقه"."""
    seconds = max(0, int(seconds))
    if seconds < 60:
        return f"{fa(seconds)} ثانیه"
    if seconds < 3600:
        return f"{fa(seconds // 60)} دقیقه"
    if seconds < 86400:
        return f"{fa(seconds // 3600)} ساعت"
    return f"{fa(seconds // 86400)} روز"
