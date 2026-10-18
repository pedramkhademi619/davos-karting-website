import "package:get/get.dart";

import "package:davos_admin/core/services/api_service/api_service.dart";
import "package:davos_admin/features/accounting/model/accounting_models.dart";
import "package:davos_admin/features/accounting/model/accounting_month.dart";
import "package:davos_admin/shared/controllers/loadable_controller.dart";

/// One day of the day book: the ticket sales of the day (booked automatically) and the entries recorded by hand.
class DayBookDay {
  DayBookDay(this.date);

  final String date;
  SalesDay? sales;
  final List<Entry> entries = [];
}

/// The month day by day, newest first.
class DayBookController extends LoadableController {
  final Rx<AccountingMonth> month = AccountingMonth.current().obs;
  final RxList<DayBookDay> days = <DayBookDay>[].obs;

  @override
  Future<void> fetch() async {
    final api = ApiService();
    final m = month.value;
    final entries = <Entry>[];
    for (var offset = 0; ; offset += 200) {
      final page = await api.getJournal(from: m.from, to: m.to, sources: dayBookSources, offset: offset);
      entries.addAll(page.items);
      if (offset + 200 >= page.total) break;
    }
    final sales = await api.getSalesReport(m.from, m.to);
    final byDate = <String, DayBookDay>{};
    for (final day in sales.days.where((d) => d.receivedIrr != 0)) {
      byDate[day.date] = DayBookDay(day.date)..sales = day;
    }
    for (final entry in entries) {
      if (entry.source == "cash_close" && entry.totalIrr == 0) continue;
      byDate.putIfAbsent(entry.date, () => DayBookDay(entry.date)).entries.add(entry);
    }
    days.assignAll(byDate.values.toList()..sort((a, b) => b.date.compareTo(a.date)));
  }

  Future<void> step(int by) {
    month.value = month.value.shift(by);
    days.clear();
    return reload();
  }

  Future<String?> remove(Entry entry) => guard(() async {
    await ApiService().reverseEntry(entry.id, "حذف از دفتر روزانه");
    await reload();
  });
}
