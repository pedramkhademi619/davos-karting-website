"""A lighter chart of accounts for books that started with the old, long default chart.

The admin panel now shows the books as a few plain income and expense categories. On an existing installation this:

* hides the old default categories nobody has posted to (supplies inventory, buildings, loans, sponsorship, tyres,
  staff bonuses, ...): ``active = false``, so the owner can bring any of them back from the categories page;
* gives the remaining default categories their shorter names, but only where the owner never renamed them.

Accounts with entries, accounts the owner added and system accounts are never touched. A new installation gets the
short chart directly (domain/services/default_chart.py), so there is nothing to do there.
"""

from collections.abc import Sequence
from typing import Union

from alembic import op
import sqlalchemy as sa

revision: str = "0018"
down_revision: Union[str, Sequence[str], None] = "0017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# code -> name in the old default chart, for the categories that are hidden when unused
_HIDDEN = {
    "1150": "پیش‌پرداخت‌ها",
    "1170": "موجودی ملزومات و قطعات",
    "1202": "ساختمان و تاسیسات",
    "1203": "تجهیزات و ماشین‌آلات",
    "1204": "اثاثیه و تجهیزات اداری",
    "2106": "مالیات و عوارض پرداختنی",
    "2201": "وام‌های دریافتی",
    "3102": "برداشت صاحب سرمایه",
    "4103": "درآمد اسپانسر و تبلیغات",
    "5103": "لاستیک و قطعات یدکی",
    "5202": "بیمه و مزایای پرسنل",
    "5203": "پاداش و اضافه‌کار",
    "5303": "اینترنت، سرور و نرم‌افزار",
    "5304": "نظافت و ملزومات مصرفی",
    "5503": "سود و کارمزد وام",
}

# code -> (old default name, new name)
_RENAMED = {
    "1110": ("بانک (حساب جاری اصلی)", "بانک"),
    "4101": ("درآمد فروش بلیت", "فروش بلیت"),
    "4102": ("درآمد بوفه و خدمات جانبی", "بوفه"),
    "4104": ("درآمد باشگاه و برگزاری مسابقه", "رویداد و مسابقه"),
    "5101": ("هزینه سوخت", "سوخت"),
    "5102": ("تعمیر و نگهداری خودروها", "تعمیر و قطعات"),
    "5104": ("بیمه خودروها و پیست", "بیمه"),
    "5105": ("لباس، کلاه و تجهیزات ایمنی", "کلاه، لباس و تجهیزات ایمنی"),
    "5201": ("حقوق و دستمزد", "حقوق و بیمه پرسنل"),
    "5302": ("آب، برق، گاز و تلفن", "قبض‌ها (آب، برق، گاز، تلفن، اینترنت)"),
    "5305": ("هزینه‌های اداری و متفرقه", "متفرقه"),
    "5401": ("تبلیغات و بازاریابی", "تبلیغات"),
    "5402": ("کارمزد درگاه پرداخت و بانک", "کارمزد بانک"),
    "5501": ("هزینه استهلاک", "استهلاک"),
    "5504": ("اضافه و کسری صندوق", "کسری و اضافه صندوق"),
}

_UNUSED = "NOT EXISTS (SELECT 1 FROM accounting_journal_lines l WHERE l.account_id = accounting_accounts.id)"


def _set_active(active: bool) -> None:
    for code, name in _HIDDEN.items():
        op.get_bind().execute(
            sa.text(
                "UPDATE accounting_accounts SET active = :active"
                f" WHERE code = :code AND name = :name AND NOT is_system AND NOT is_group AND {_UNUSED}"
            ),
            {"active": active, "code": code, "name": name},
        )


def _rename(forward: bool) -> None:
    for code, (old, new) in _RENAMED.items():
        before, after = (old, new) if forward else (new, old)
        op.get_bind().execute(
            sa.text("UPDATE accounting_accounts SET name = :after WHERE code = :code AND name = :before"),
            {"code": code, "before": before, "after": after},
        )


def upgrade() -> None:
    _set_active(False)
    _rename(True)


def downgrade() -> None:
    _rename(False)
    _set_active(True)
