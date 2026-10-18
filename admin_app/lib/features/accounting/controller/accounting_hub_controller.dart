import "package:get/get.dart";

import "package:davos_admin/core/services/api_service/api_service.dart";
import "package:davos_admin/core/utils/fa.dart";
import "package:davos_admin/features/accounting/model/accounting_models.dart";
import "package:davos_admin/shared/controllers/loadable_controller.dart";

/// The financial dashboard at the top of the Finance tab.
class AccountingHubController extends LoadableController {
  final Rxn<AccountingDashboard> dashboard = Rxn<AccountingDashboard>();

  /// Amounts are hidden (dots) when somebody is looking over the owner's shoulder.
  final RxBool hidden = false.obs;

  @override
  Future<void> fetch() async => dashboard.value = await ApiService().getAccountingDashboard();

  /// Rial -> Toman text, or dots while hidden.
  String money(num irr) => hidden.value ? "••••••" : tomanFromIrr(irr);
}
