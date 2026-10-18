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
  static const String journal = "$accounting/journal";

  /// "$journalItem$id/reverse".
  static const String journalItem = "$accounting/journal/";
  static const String expenses = "$accounting/expenses";
  static const String income = "$accounting/income";
  static const String transfers = "$accounting/transfers";
  static const String refundPayments = "$accounting/payments";
  static const String cash = "$accounting/cash";

  // ---- accounting reports ----
  static const String reportDashboard = "$accounting/reports/dashboard";
  static const String reportIncomeStatement = "$accounting/reports/income-statement";
  static const String reportSales = "$accounting/reports/sales";
}
