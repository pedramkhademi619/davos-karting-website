from __future__ import annotations

from collections.abc import Iterable

from davos.modules.administration.domain.enums.admin_permission import AdminPermission as P
from davos.modules.administration.domain.value_objects.permission_entry import PermissionEntry
from davos.modules.administration.domain.value_objects.permission_preset import PermissionPreset


class PermissionCatalog:
    """Every grantable permission with its Persian label, the default set of a staff account, and the presets.

    The owner always has everything and cannot be restricted. Managing staff accounts is deliberately not grantable:
    whoever could grant access could give themselves all of it.
    """

    ENTRIES: tuple[PermissionEntry, ...] = (
        PermissionEntry(P.DASHBOARD, "داشبورد", "خلاصه امروز و فردا، فروش و وضعیت پیامک."),
        PermissionEntry(P.RESERVATIONS, "رزروها و سانس‌ها", "دیدن تابلوی سانس‌ها، ثبت فروش حضوری، لغو و ثبت حضور."),
        PermissionEntry(P.CUSTOMERS, "مشتریان", "فهرست و جست‌وجوی مشتریان و شماره موبایل آن‌ها."),
        PermissionEntry(P.PAYMENTS, "پرداخت‌ها", "فهرست پرداخت‌های آنلاین و شماره پیگیری بانک."),
        PermissionEntry(P.SMS, "پنل پیامک", "دیدن اعتبار و گزارش پیامک‌ها و ارسال پیامک."),
        PermissionEntry(P.ASSISTANT, "دستیار هوشمند (مشاهده)", "دیدن آمار، دانسته‌ها و پاسخ‌های ذخیره‌شده دستیار."),
        PermissionEntry(
            P.ASSISTANT_MANAGE,
            "دستیار هوشمند (ویرایش)",
            "افزودن و ویرایش دانسته‌ها و پاسخ‌های ذخیره‌شده دستیار.",
            implies=P.ASSISTANT,
        ),
        PermissionEntry(P.SETTINGS, "تنظیمات و قیمت‌ها (مشاهده)", "دیدن قیمت‌ها، ظرفیت‌ها و قوانین رزرو."),
        PermissionEntry(
            P.SETTINGS_MANAGE,
            "تنظیمات و قیمت‌ها (تغییر)",
            "تغییر قیمت‌ها، ظرفیت‌ها، روزهای تعطیل و قوانین رزرو.",
            implies=P.SETTINGS,
        ),
        PermissionEntry(P.ACCOUNTING, "حسابداری", "دسترسی کامل به دفاتر مالی، ثبت اسناد و گزارش‌های مالی."),
        PermissionEntry(P.SYSTEM, "وضعیت سرویس‌ها", "دیدن سلامت پایگاه داده، پیامک، درگاه و سایر سرویس‌ها."),
    )

    # What a staff account could already do before permissions existed; a new staff account starts with these.
    STAFF_DEFAULTS: frozenset[P] = frozenset(
        {P.DASHBOARD, P.RESERVATIONS, P.CUSTOMERS, P.PAYMENTS, P.SMS, P.ASSISTANT, P.SETTINGS, P.SYSTEM}
    )

    PRESETS: tuple[PermissionPreset, ...] = (
        PermissionPreset("reception", "پذیرش", frozenset({P.DASHBOARD, P.RESERVATIONS, P.CUSTOMERS})),
        PermissionPreset("accountant", "حسابدار", frozenset({P.DASHBOARD, P.PAYMENTS, P.ACCOUNTING})),
        PermissionPreset(
            "support", "پشتیبان", frozenset({P.DASHBOARD, P.RESERVATIONS, P.CUSTOMERS, P.SMS, P.ASSISTANT})
        ),
        PermissionPreset(
            "manager",
            "مدیر عملیات (همه‌چیز جز مدیریت کاربران)",
            frozenset(entry.permission for entry in ENTRIES),
        ),
    )

    @classmethod
    def everything(cls) -> frozenset[P]:
        return frozenset(entry.permission for entry in cls.ENTRIES)

    @classmethod
    def closure(cls, permissions: Iterable[P]) -> frozenset[P]:
        """The granted permissions plus the lower levels they include (managing a section includes viewing it)."""
        granted = set(permissions)
        for entry in cls.ENTRIES:
            if entry.permission in granted and entry.implies is not None:
                granted.add(entry.implies)
        return frozenset(granted)
