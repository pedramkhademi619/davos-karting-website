/// Every backend endpoint the app talks to.
///
/// Same convention as the Vesta admin app: Dio has no baseUrl configured, so everything here is a full URL, and this
/// file is the only place that says which server the app talks to. Point a build at another server (a local one while
/// developing, for example) without touching the code:
///
///     flutter run --dart-define=API_DOMAIN=http://10.0.2.2:8088
///
/// Paths that carry an id end in a slash and are completed by the caller: "${Urls.reservationItem}$id/cancel".
class Urls {
  static const String domain = String.fromEnvironment(
    "API_DOMAIN",
    defaultValue: "https://davoskarting.ir",
  );
  static const String baseUrl = "$domain/api/v1";

  /// Everything staff-only lives under /admin; the session cookie is scoped to this path as well.
  static const String adminBase = "$baseUrl/admin";

  // ---- auth ----
  static const String login = "$adminBase/auth/login";
  static const String logout = "$adminBase/auth/logout";
  static const String me = "$adminBase/auth/me";
  static const String changePassword = "$adminBase/auth/password";

  // ---- dashboard ----
  static const String dashboard = "$adminBase/dashboard";

  // ---- reservations ----
  static const String reservations = "$adminBase/reservations";
  static const String reservationBoard = "$adminBase/reservations/board";

  /// "$reservationItem$id/cancel" and "$reservationItem$id/attended".
  static const String reservationItem = "$adminBase/reservations/";

  // ---- customers ----
  static const String customers = "$adminBase/customers";

  /// "$customerItem$userId/status".
  static const String customerItem = "$adminBase/customers/";

  // ---- payments ----
  static const String payments = "$adminBase/payments";

  // ---- sms ----
  static const String smsAccount = "$adminBase/sms/account";
  static const String smsMessages = "$adminBase/sms/messages";
  static const String smsSend = "$adminBase/sms/send";

  // ---- assistant ----
  static const String assistantOverview = "$adminBase/assistant/overview";
  static const String assistantInteractions =
      "$adminBase/assistant/interactions";
  static const String assistantCache = "$adminBase/assistant/cache";

  /// "$assistantCacheItem$id" and "$assistantCacheItem$id/active".
  static const String assistantCacheItem = "$adminBase/assistant/cache/";
  static const String assistantKnowledge = "$adminBase/assistant/knowledge";

  /// "$assistantKnowledgeItem$id".
  static const String assistantKnowledgeItem =
      "$adminBase/assistant/knowledge/";

  // ---- settings ----
  static const String scheduleSettings = "$adminBase/settings/schedule";

  // ---- system status ----
  static const String systemStatus = "$adminBase/system/status";

  // ---- panel users ----
  static const String users = "$adminBase/users";
  static const String usersCatalog = "$adminBase/users/catalog";

  /// "$userItem$adminId/active" and "$userItem$adminId/permissions".
  static const String userItem = "$adminBase/users/";

  // ---- accounting ----
  static const String accounting = "$adminBase/accounting";
  static const String accounts = "$accounting/accounts";

  /// "$accountItem$id".
  static const String accountItem = "$accounting/accounts/";
  static const String accountingSettings = "$accounting/settings";
  static const String journal = "$accounting/journal";

  /// "$journalItem$id" and "$journalItem$id/reverse".
  static const String journalItem = "$accounting/journal/";
  static const String expenses = "$accounting/expenses";
  static const String income = "$accounting/income";
  static const String transfers = "$accounting/transfers";
  static const String vendorPayments = "$accounting/payments";
  static const String vendors = "$accounting/vendors";

  /// "$vendorItem$id".
  static const String vendorItem = "$accounting/vendors/";
  static const String assets = "$accounting/assets";

  /// "$assetItem$id/dispose".
  static const String assetItem = "$accounting/assets/";
  static const String depreciation = "$accounting/depreciation";
  static const String budget = "$accounting/budget";
  static const String cash = "$accounting/cash";

  /// "$fiscalYearItem$year" and "$fiscalYearItem$year/close".
  static const String fiscalYearItem = "$accounting/fiscal-years/";
  static const String accountingSync = "$accounting/sync";

  // ---- accounting reports ----
  static const String reportDashboard = "$accounting/reports/dashboard";
  static const String reportTrialBalance = "$accounting/reports/trial-balance";
  static const String reportLedger = "$accounting/reports/ledger";
  static const String reportIncomeStatement =
      "$accounting/reports/income-statement";
  static const String reportBalanceSheet = "$accounting/reports/balance-sheet";
  static const String reportSales = "$accounting/reports/sales";
  static const String reportVat = "$accounting/reports/vat";
  static const String reportCashPosition = "$accounting/reports/cash-position";
}
