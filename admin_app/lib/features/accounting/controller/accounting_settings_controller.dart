import "package:get/get.dart";

import "package:davos_admin/core/services/api_service/api_service.dart";
import "package:davos_admin/features/accounting/model/accounting_models.dart";
import "package:davos_admin/shared/controllers/loadable_controller.dart";

class AccountingSettingsController extends LoadableController {
  final Rxn<AccountingSettings> settings = Rxn<AccountingSettings>();

  @override
  Future<void> fetch() async => settings.value = await ApiService().getAccountingSettings();

  Future<String?> save(AccountingSettings edited) => guard(() async {
    settings.value = await ApiService().saveAccountingSettings(edited);
  });

  /// Returns the message to show, and whether it is an error.
  Future<(String, bool)> sync(String from, String to) async {
    try {
      final (sales, revenue) = await ApiService().syncAccounting(from, to);
      return ("$sales فروش و $revenue درآمد ثبت شد.", false);
    } catch (e) {
      return (errorMessage(e), true);
    }
  }

  Future<String?> closeYear(int year) => guard(() async {
    await ApiService().closeFiscalYear(year);
    settings.value = await ApiService().getAccountingSettings();
  });

  Future<bool> isYearClosed(int year) => ApiService().isFiscalYearClosed(year);
}
