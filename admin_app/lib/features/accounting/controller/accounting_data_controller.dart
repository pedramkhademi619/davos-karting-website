import "package:get/get.dart";

import "package:davos_admin/core/services/api_service/api_service.dart";
import "package:davos_admin/features/accounting/model/accounting_models.dart";
import "package:davos_admin/shared/controllers/loadable_controller.dart";

/// The chart of accounts and the suppliers, shared by every accounting screen that has to pick one.
class AccountingDataController extends LoadableController {
  final RxList<Account> accounts = <Account>[].obs;
  final RxList<Vendor> vendors = <Vendor>[].obs;

  @override
  Future<void> fetch() async {
    final api = ApiService();
    final loaded = await Future.wait([api.getAccounts(), api.getVendors()]);
    accounts.assignAll(loaded[0] as List<Account>);
    vendors.assignAll(loaded[1] as List<Vendor>);
  }

  /// Accounts a transaction may be booked on (not group headings, not retired), sorted by code.
  List<Account> postable({String? type, bool Function(Account)? where}) =>
      accounts.where((a) => !a.isGroup && a.active && (type == null || a.type == type) && (where?.call(a) ?? true)).toList()
        ..sort((a, b) => a.code.compareTo(b.code));

  List<Account> get moneyAccounts => postable(where: (a) => a.holdsMoney);

  /// Options for a drop-down: id -> "code - name".
  Map<String, String> options(List<Account> list) => {for (final a in list) a.id: a.label};

  Map<String, String> get vendorOptions => {for (final v in vendors.where((v) => v.active)) v.id: v.name};

  Account? byId(String? id) => accounts.where((a) => a.id == id).firstOrNull;
}
