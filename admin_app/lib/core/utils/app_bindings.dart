import "package:get/get.dart";

import "package:davos_admin/core/services/api_service/api_service.dart";
import "package:davos_admin/features/auth/controller/session_controller.dart";

/// What lives for the whole run of the app: the HTTP client and who is signed in.
class AppBindings extends Bindings {
  @override
  void dependencies() {
    ApiService();
    Get.put<SessionController>(SessionController(), permanent: true);
  }
}
