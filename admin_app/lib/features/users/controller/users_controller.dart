import "package:get/get.dart";

import "package:davos_admin/core/services/api_service/api_service.dart";
import "package:davos_admin/features/users/model/panel_user.dart";
import "package:davos_admin/shared/controllers/loadable_controller.dart";

/// Staff accounts and what each person may open (owner only).
class UsersController extends LoadableController {
  final RxList<PanelUser> users = <PanelUser>[].obs;
  final Rxn<PermissionCatalog> catalog = Rxn<PermissionCatalog>();

  @override
  Future<void> fetch() async {
    final api = ApiService();
    catalog.value = await api.getPermissionCatalog();
    users.assignAll(await api.getPanelUsers());
  }

  Future<String?> setActive(PanelUser user, bool active) => guard(() async {
    await ApiService().setPanelUserActive(user.adminId, active);
    await reload();
  });

  /// [permissions] null means "the staff defaults".
  Future<String?> savePermissions(PanelUser user, List<String>? permissions) => guard(() async {
    await ApiService().setPanelUserPermissions(user.adminId, permissions);
    await reload();
  });

  Future<String?> create({
    required String username,
    required String displayName,
    required String password,
    required String role,
    List<String>? permissions,
  }) => guard(() async {
    await ApiService().addPanelUser(
      username: username,
      displayName: displayName,
      password: password,
      role: role,
      permissions: role == "staff" ? permissions : null,
    );
    await reload();
  });
}
