import "package:flutter_test/flutter_test.dart";

import "package:davos_admin/core/constants/urls.dart";
import "package:davos_admin/core/utils/fa.dart";
import "package:davos_admin/core/utils/jalali.dart";
import "package:davos_admin/features/settings/model/schedule_settings.dart";
import "package:davos_admin/shared/models/json_read.dart";

void main() {
  group("Urls", () {
    test("every endpoint hangs off the API base", () {
      expect(Urls.baseUrl, endsWith("/api/v1"));
      expect(Urls.login, "${Urls.baseUrl}/admin/auth/login");
      expect("${Urls.reservationItem}abc/cancel", "${Urls.baseUrl}/admin/reservations/abc/cancel");
      expect("${Urls.userItem}7/permissions", "${Urls.baseUrl}/admin/users/7/permissions");
    });
  });

  group("digits and money", () {
    test("Latin digits become Persian and back", () {
      expect(fa(1405), "۱۴۰۵");
      expect(latin("۱۲۳٤٥"), "12345");
      expect(parseInt("۱٬۲۵۰"), 1250);
    });

    test("amounts are grouped", () {
      expect(grouped(1250000), "۱٬۲۵۰٬۰۰۰");
      expect(grouped(-5000), "−۵٬۰۰۰");
    });

    test("Rial to Toman keeps a hidden digit visible", () {
      expect(tomanFromIrr(12500000), "۱٬۲۵۰٬۰۰۰");
      expect(tomanFromIrr(15), "۱٫۵");
      expect(tomanOrDash(0), "—");
    });
  });

  group("Jalali dates", () {
    test("ISO to Jalali text", () {
      expect(jalaliText("2026-03-21"), "۱۴۰۵/۰۱/۰۱");
      expect(jalaliLong("2026-03-21"), "۱ فروردین ۱۴۰۵");
    });

    test("before 06:00 in Tehran it is still the previous business day", () {
      // 02:00 Tehran on 2026-03-21 is 22:30 UTC on 2026-03-20.
      expect(businessDayIso(DateTime.utc(2026, 3, 20, 22, 30)), "2026-03-20");
      expect(businessDayIso(DateTime.utc(2026, 3, 21, 8)), "2026-03-21");
    });

    test("month range", () {
      final (first, last) = jalaliMonthRange(1405, 1);
      expect(first, "2026-03-21");
      expect(last, "2026-04-20");
    });
  });

  group("tolerant JSON", () {
    test("missing fields fall back instead of throwing", () {
      final json = <String, dynamic>{"a": "5", "b": null};
      expect(json.integer("a"), 5);
      expect(json.integer("missing", 7), 7);
      expect(json.str("b"), "");
      expect(json.list("nope"), isEmpty);
    });

    test("pages read items and total", () {
      final page = PageResult.parse<String>({"items": [{"id": "x"}], "total": 9}, (j) => j.str("id"));
      expect(page.items, ["x"]);
      expect(page.total, 9);
    });
  });

  group("schedule settings", () {
    test("an older server without shifts gets the owner's defaults", () {
      final s = ScheduleSettings.fromJson(const {"shift_start": "15:00"});
      expect(s.morningShiftEnabled, isTrue);
      expect([s.morningStart, s.morningEnd], ["10:00", "14:00"]);
      expect(s.juniorWeekdays, [5, 6, 0, 1, 2]);
      expect([s.juniorFrom, s.juniorUntil, s.juniorScope], ["15:00", "18:00", "drivers"]);
    });

    test("shifts and under-15 hours go back to the server as they came", () {
      final json = ScheduleSettings.fromJson(const {
        "morning_shift_enabled": false,
        "morning_start": "09:30",
        "morning_end": "13:00",
        "junior_weekdays": [5, 6],
        "junior_from": "16:00",
        "junior_until": "19:00",
        "junior_scope": "everyone",
      }).toJson();
      expect(json["morning_shift_enabled"], isFalse);
      expect([json["morning_start"], json["morning_end"]], ["09:30", "13:00"]);
      expect(json["junior_weekdays"], [5, 6]);
      expect([json["junior_from"], json["junior_until"], json["junior_scope"]], ["16:00", "19:00", "everyone"]);
    });
  });
}
