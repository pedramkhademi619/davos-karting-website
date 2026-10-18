import "package:shamsi_date/shamsi_date.dart";

import "package:davos_admin/core/utils/fa.dart";

/// Jalali calendar helpers. The API speaks ISO dates ("2026-09-26"); everything the staff reads or types is Jalali.
const jalaliMonths = [
  "فروردین",
  "اردیبهشت",
  "خرداد",
  "تیر",
  "مرداد",
  "شهریور",
  "مهر",
  "آبان",
  "آذر",
  "دی",
  "بهمن",
  "اسفند",
];

/// Saturday first, as the Iranian week runs.
const jalaliWeekdays = [
  "شنبه",
  "یکشنبه",
  "دوشنبه",
  "سه‌شنبه",
  "چهارشنبه",
  "پنجشنبه",
  "جمعه",
];

String isoOf(DateTime date) =>
    "${date.year.toString().padLeft(4, "0")}-${date.month.toString().padLeft(2, "0")}-${date.day.toString().padLeft(2, "0")}";

DateTime dateOfIso(String iso) {
  final p = iso.split("-").map(int.parse).toList();
  return DateTime(p[0], p[1], p[2]);
}

Jalali jalaliOfIso(String iso) => Jalali.fromDateTime(dateOfIso(iso));

String isoOfJalali(Jalali j) => isoOf(j.toDateTime());

/// "2026-09-26" -> "۱۴۰۵/۰۷/۰۴"
String jalaliText(String? iso) {
  if (iso == null || iso.length < 10) return "";
  final j = jalaliOfIso(iso.substring(0, 10));
  return fa("${j.year}/${j.month.toString().padLeft(2, "0")}/${j.day.toString().padLeft(2, "0")}");
}

/// "2026-09-26" -> "۴ مهر ۱۴۰۵"
String jalaliLong(String? iso) {
  if (iso == null || iso.length < 10) return "";
  final j = jalaliOfIso(iso.substring(0, 10));
  return "${fa(j.day)} ${jalaliMonths[j.month - 1]} ${fa(j.year)}";
}

/// "2026-09-26" -> "شنبه ۴ مهر"
String jalaliWithWeekday(String iso) {
  final j = jalaliOfIso(iso);
  return "${jalaliWeekdays[j.weekDay - 1]} ${fa(j.day)} ${jalaliMonths[j.month - 1]}";
}

/// An ISO timestamp from the API ("2026-09-26T14:30:00+03:30" or UTC) as Tehran date and time: ۱۴۰۵/۰۷/۰۴ ۱۴:۳۰.
String jalaliDateTime(String? timestamp) {
  if (timestamp == null || timestamp.isEmpty) return "—";
  final parsed = DateTime.tryParse(timestamp);
  if (parsed == null) return timestamp;
  final tehran = parsed.toUtc().add(const Duration(hours: 3, minutes: 30));
  final iso = isoOf(DateTime(tehran.year, tehran.month, tehran.day));
  final time =
      "${tehran.hour.toString().padLeft(2, "0")}:${tehran.minute.toString().padLeft(2, "0")}";
  return "${jalaliText(iso)} ${fa(time)}";
}

DateTime _tehranNow([DateTime? now]) =>
    (now ?? DateTime.now()).toUtc().add(const Duration(hours: 3, minutes: 30));

/// Today in Tehran (ISO).
String todayIso([DateTime? now]) {
  final t = _tehranNow(now);
  return isoOf(DateTime(t.year, t.month, t.day));
}

/// The business day: before 06:00 in Tehran it is still the previous evening's sessions (matches the backend).
String businessDayIso([DateTime? now]) {
  final t = _tehranNow(now);
  final day = DateTime(t.year, t.month, t.day);
  return isoOf(t.hour < 6 ? day.subtract(const Duration(days: 1)) : day);
}

String addDaysIso(String iso, int days) =>
    isoOf(dateOfIso(iso).add(Duration(days: days)));

/// Current Jalali year in Tehran.
int currentJalaliYear([DateTime? now]) => jalaliOfIso(todayIso(now)).year;

/// First and last ISO day of a Jalali month.
(String, String) jalaliMonthRange(int year, int month) {
  final first = Jalali(year, month, 1);
  final last = Jalali(year, month, first.monthLength);
  return (isoOfJalali(first), isoOfJalali(last));
}
