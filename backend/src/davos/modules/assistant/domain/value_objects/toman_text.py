from __future__ import annotations

_PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


class TomanText:
    """An amount of Toman the way it is said in Persian: 790000 -> "۷۹۰ هزار تومان", 1200000 -> "یک میلیون و ۲۰۰ هزار
    تومان", 7110000 -> "۷ میلیون و ۱۱۰ هزار تومان"."""

    @staticmethod
    def say(amount: int) -> str:
        millions, rest = divmod(amount, 1_000_000)
        thousands, units = divmod(rest, 1_000)
        parts = []
        if millions:
            parts.append("یک میلیون" if millions == 1 else f"{TomanText._fa(millions)} میلیون")
        if thousands:
            parts.append(f"{TomanText._fa(thousands)} هزار")
        if units or not parts:
            parts.append(TomanText._fa(units))
        return " و ".join(parts) + " تومان"

    @staticmethod
    def _fa(value: int) -> str:
        return str(value).translate(_PERSIAN_DIGITS)
