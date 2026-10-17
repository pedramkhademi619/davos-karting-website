/// Route names for Get.toNamed.
///
/// These have to line up with the getPages list in AdminApp - a name that isn't registered there fails at runtime, not
/// compile time.
class NamedRouts {
  static const String splash = "/";
  static const String login = "/login";
  static const String home = "/home";

  static const String newReservation = "/reservations/new";
  static const String search = "/search";
  static const String customers = "/customers";
  static const String payments = "/payments";
  static const String sms = "/sms";
  static const String assistant = "/assistant";
  static const String settings = "/settings";
  static const String system = "/system";
  static const String users = "/users";
  static const String changePassword = "/change-password";

  // ---- accounting ----
  static const String accountingJournal = "/accounting/journal";
  static const String accountingQuickEntry = "/accounting/quick-entry";
  static const String accountingChart = "/accounting/chart";
  static const String accountingVendors = "/accounting/vendors";
  static const String accountingAssets = "/accounting/assets";
  static const String accountingCash = "/accounting/cash";
  static const String accountingBudget = "/accounting/budget";
  static const String accountingReports = "/accounting/reports";
  static const String accountingSettings = "/accounting/settings";
}
