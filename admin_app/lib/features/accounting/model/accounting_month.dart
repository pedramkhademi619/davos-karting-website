import "package:shamsi_date/shamsi_date.dart";

import "package:davos_admin/core/utils/fa.dart";
import "package:davos_admin/core/utils/jalali.dart";

/// A Jalali month the accounting screens step through (‹ مهر ۱۴۰۵ ›).
class AccountingMonth {
  const AccountingMonth(this.year, this.month);

  factory AccountingMonth.current() {
    final j = jalaliOfIso(businessDayIso());
    return AccountingMonth(j.year, j.month);
  }

  final int year;
  final int month;

  AccountingMonth shift(int by) {
    final index = year * 12 + (month - 1) + by;
    return AccountingMonth(index ~/ 12, index % 12 + 1);
  }

  String get from => isoOfJalali(Jalali(year, month, 1));

  String get to => isoOfJalali(Jalali(year, month, Jalali(year, month, 1).monthLength));

  String get label => "${jalaliMonths[month - 1]} ${fa(year)}";

  bool get isCurrent {
    final now = AccountingMonth.current();
    return now.year == year && now.month == month;
  }
}
