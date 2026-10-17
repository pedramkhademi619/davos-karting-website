/// Keys for persisted values and a few fixed numbers.
class Constants {
  // GetStorage (preferences)
  static const String themeMode = "theme_mode";
  static const String lastUsername = "last_username";

  // FlutterSecureStorage (the staff session)
  static const String sessionCookie = "session_cookie";
  static const String csrfToken = "csrf_token";

  /// Rows per page on every list.
  static const int pageSize = 30;
}
