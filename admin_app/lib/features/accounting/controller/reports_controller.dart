import "package:get/get.dart";
import "package:shamsi_date/shamsi_date.dart";

import "package:davos_admin/core/services/api_service/api_service.dart";
import "package:davos_admin/core/utils/jalali.dart";
import "package:davos_admin/shared/controllers/loadable_controller.dart";

enum ReportKind {
  trialBalance("تراز آزمایشی"),
  incomeStatement("سود و زیان"),
  balanceSheet("ترازنامه"),
  sales("فروش"),
  vat("مالیات"),
  ledger("دفتر کل"),
  cashPosition("موجودی نقد");

  const ReportKind(this.label);
  final String label;
}

/// One report at a time over a date range; the range starts at the beginning of the Jalali year.
class ReportsController extends LoadableController {
  final Rx<ReportKind> kind = ReportKind.incomeStatement.obs;
  final RxString from = _yearStart().obs;
  final RxString to = todayIso().obs;
  final RxnString ledgerAccount = RxnString();

  /// The loaded report: the type depends on [kind].
  final Rxn<Object> result = Rxn<Object>();

  static String _yearStart() => isoOfJalali(Jalali(currentJalaliYear(), 1, 1));

  @override
  void onReady() {
    // Nothing to fetch until the user has chosen a report that needs no account.
    super.onReady();
  }

  @override
  Future<void> fetch() async {
    final api = ApiService();
    result.value = null;
    switch (kind.value) {
      case ReportKind.trialBalance:
        result.value = await api.getTrialBalance(from.value, to.value);
      case ReportKind.incomeStatement:
        result.value = await api.getIncomeStatement(from.value, to.value);
      case ReportKind.balanceSheet:
        result.value = await api.getBalanceSheet(to.value);
      case ReportKind.sales:
        result.value = await api.getSalesReport(from.value, to.value);
      case ReportKind.vat:
        result.value = await api.getVatReport(from.value, to.value);
      case ReportKind.ledger:
        final account = ledgerAccount.value;
        if (account != null) result.value = await api.getLedger(account, from.value, to.value);
      case ReportKind.cashPosition:
        result.value = await api.getCashPosition(to.value);
    }
  }

  Future<void> choose(ReportKind value) {
    kind.value = value;
    return reload();
  }

  Future<void> setRange({String? start, String? end}) {
    if (start != null) from.value = start;
    if (end != null) to.value = end;
    return reload();
  }

  Future<void> setLedgerAccount(String? id) {
    ledgerAccount.value = id;
    return reload();
  }
}
