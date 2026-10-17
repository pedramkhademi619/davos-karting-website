import "package:get/get.dart";

import "package:davos_admin/core/constants/named_routs.dart";
import "package:davos_admin/core/interceptors/session_interceptor.dart";
import "package:davos_admin/core/services/api_service/api_service.dart";
import "package:davos_admin/core/services/storage_service/storage_service.dart";
import "package:davos_admin/features/auth/model/admin_me.dart";

/// Who is signed in. Lives for the whole run of the app; screens ask it what the staff member may open.
class SessionController extends GetxController {
  final ApiService _api = ApiService();
  final StorageService _storage = StorageService();

  final Rxn<AdminMe> me = Rxn<AdminMe>();

  bool get signedIn => me.value != null;
  bool get isOwner => me.value?.isOwner ?? false;

  /// The owner may open everything; staff only what they were given.
  bool can(String permission) {
    final current = me.value;
    if (current == null) return false;
    if (permission == "owner") return current.isOwner;
    return current.isOwner || current.permissions.contains(permission);
  }

  @override
  void onInit() {
    super.onInit();
    SessionHolder.onExpired = _expired;
  }

  /// Reads the stored session and asks the server whether it is still good. Returns true when signed in.
  Future<bool> restore() async {
    SessionHolder.restore(await _storage.readSessionCookie(), await _storage.readCsrfToken());
    if (!SessionHolder.hasSession) return false;
    try {
      await _applyMe(await _api.getMe());
      return true;
    } on ApiError catch (e) {
      // A network failure is not a sign-out: keep the stored session and let the user retry from the login screen.
      if (!e.isUnauthenticated) return false;
      await _forget();
      return false;
    }
  }

  Future<void> signIn(String username, String password) async {
    final admin = await _api.signIn(username.trim(), password);
    await _applyMe(admin);
    await _storage.writeLastUsername(username.trim());
  }

  Future<void> signOut() async {
    try {
      await _api.signOut();
    } catch (_) {
      // Signing out on this device must work even when the server cannot be reached.
    }
    await _forget();
    Get.offAllNamed(NamedRouts.login);
  }

  Future<void> _applyMe(AdminMe admin) async {
    me.value = admin;
    SessionHolder.csrfToken = admin.csrfToken;
    await _storage.writeSession(cookie: SessionHolder.cookieHeader, csrf: admin.csrfToken);
  }

  Future<void> _forget() async {
    me.value = null;
    SessionHolder.clear();
    await _storage.clearSession();
  }

  void _expired() {
    if (me.value == null) return;
    _forget();
    Get.offAllNamed(NamedRouts.login);
    Get.snackbar("نشست تمام شد", "دوباره وارد شوید.", snackPosition: SnackPosition.BOTTOM);
  }
}
