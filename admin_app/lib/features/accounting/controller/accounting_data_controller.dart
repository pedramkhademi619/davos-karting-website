import "package:get/get.dart";

import "package:davos_admin/core/services/api_service/api_service.dart";
import "package:davos_admin/features/accounting/model/accounting_models.dart";
import "package:davos_admin/shared/controllers/loadable_controller.dart";

/// The accounts every accounting screen needs: the till, the bank, and the income and expense categories.
class AccountingDataController extends LoadableController {
  final RxList<Account> accounts = <Account>[].obs;

  @override
  Future<void> fetch() async => accounts.assignAll(await ApiService().getAccounts());

  /// Categories of one kind ("expense" or "revenue") in code order; hidden ones only when asked for.
  List<Account> categories(String kind, {bool includeHidden = false}) =>
      accounts.where((a) => a.isCategory(kind) && (includeHidden || a.active)).toList()..sort((a, b) => a.code.compareTo(b.code));

  Account? wallet(Wallet wallet) => accounts.firstWhereOrNull((a) => a.role == (wallet == Wallet.cash ? "cash" : "bank"));

  Account? get capital => accounts.firstWhereOrNull((a) => a.role == "capital");

  Map<String, Account> get byId => {for (final a in accounts) a.id: a};

  /// The top heading a new category goes under (the "درآمدها" or "هزینه‌ها" group).
  Account? parentFor(String kind) => accounts.firstWhereOrNull((a) => a.isGroup && a.type == kind && a.parentId == null);

  /// The next free four-digit code of a kind (5xxx for expenses, 4xxx for income), so the owner never deals with codes.
  String nextCode(String kind) {
    final lead = kind == "expense" ? "5" : "4";
    final used = accounts.map((a) => a.code).where((c) => c.length == 4 && c.startsWith(lead)).map(int.parse);
    return "${[int.parse("${lead}000"), ...used].reduce((a, b) => a > b ? a : b) + 1}";
  }
}
