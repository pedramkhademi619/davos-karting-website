import "package:flutter_secure_storage/flutter_secure_storage.dart";
import "package:get_storage/get_storage.dart";

import "package:davos_admin/core/constants/constants.dart";

/// All persisted state, split across two backends (same split as the Vesta app): GetStorage for preferences,
/// FlutterSecureStorage for the staff session (cookie and CSRF token are credentials).
class StorageService {
  // A getter, so building a StorageService (the API client does) never touches the plugin until a preference is read.
  GetStorage get _box => GetStorage();
  static const FlutterSecureStorage _secure = FlutterSecureStorage();

  // ---- preferences ----
  String readThemeMode() => _box.read<String>(Constants.themeMode) ?? "system";
  Future<void> writeThemeMode(String mode) =>
      _box.write(Constants.themeMode, mode);

  String readLastUsername() => _box.read<String>(Constants.lastUsername) ?? "";
  Future<void> writeLastUsername(String name) =>
      _box.write(Constants.lastUsername, name);

  // ---- session ----
  Future<String?> readSessionCookie() async {
    try {
      return await _secure.read(key: Constants.sessionCookie);
    } catch (_) {
      return null;
    }
  }

  Future<String?> readCsrfToken() async {
    try {
      return await _secure.read(key: Constants.csrfToken);
    } catch (_) {
      return null;
    }
  }

  Future<void> writeSession({String? cookie, String? csrf}) async {
    try {
      if (cookie != null) {
        await _secure.write(key: Constants.sessionCookie, value: cookie);
      }
      if (csrf != null) {
        await _secure.write(key: Constants.csrfToken, value: csrf);
      }
    } catch (_) {
      // A device without a keystore still works for this run; the user just signs in again next time.
    }
  }

  Future<void> clearSession() async {
    try {
      await _secure.delete(key: Constants.sessionCookie);
      await _secure.delete(key: Constants.csrfToken);
    } catch (_) {}
  }
}
