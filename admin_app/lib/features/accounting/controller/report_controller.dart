import "package:get/get.dart";

import "package:davos_admin/core/services/api_service/api_service.dart";
import "package:davos_admin/features/accounting/model/accounting_models.dart";
import "package:davos_admin/features/accounting/model/accounting_month.dart";
import "package:davos_admin/shared/controllers/loadable_controller.dart";

/// One month's profit and loss in categories, compared with the month before, and where ticket money came from.
class ReportController extends LoadableController {
  final Rx<AccountingMonth> month = AccountingMonth.current().obs;
  final Rxn<IncomeStatement> statement = Rxn<IncomeStatement>();
  final Rxn<SalesReport> sales = Rxn<SalesReport>();

  @override
  Future<void> fetch() async {
    final m = month.value;
    final api = ApiService();
    final results = await Future.wait([api.getIncomeStatement(m.from, m.to), api.getSalesReport(m.from, m.to)]);
    statement.value = results[0] as IncomeStatement;
    sales.value = results[1] as SalesReport;
  }

  Future<void> step(int by) {
    month.value = month.value.shift(by);
    statement.value = null;
    sales.value = null;
    return reload();
  }
}
