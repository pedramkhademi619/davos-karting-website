import "package:get/get.dart";

import "package:davos_admin/core/services/api_service/api_service.dart";
import "package:davos_admin/core/utils/jalali.dart";
import "package:davos_admin/features/accounting/model/accounting_models.dart";
import "package:davos_admin/shared/controllers/loadable_controller.dart";

/// Budget against actual for a range of months of one Jalali year.
class BudgetController extends LoadableController {
  final RxInt year = currentJalaliYear().obs;
  final RxInt monthFrom = 1.obs;
  final RxInt monthTo = 12.obs;
  final RxList<BudgetRow> rows = <BudgetRow>[].obs;

  @override
  Future<void> fetch() async => rows.assignAll(await ApiService().getBudget(year.value, monthFrom.value, monthTo.value));

  Future<void> setRange({int? y, int? from, int? to}) {
    if (y != null) year.value = y;
    if (from != null) monthFrom.value = from;
    if (to != null) monthTo.value = to;
    if (monthTo.value < monthFrom.value) monthTo.value = monthFrom.value;
    return reload();
  }

  Future<String?> setBudget({required String accountId, int? month, required int amountToman}) => guard(() async {
    await ApiService().setBudget(accountId: accountId, year: year.value, month: month, amountToman: amountToman);
    await reload();
  });
}
