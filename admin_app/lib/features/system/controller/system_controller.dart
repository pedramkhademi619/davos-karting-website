import "dart:async";

import "package:get/get.dart";

import "package:davos_admin/core/services/api_service/api_service.dart";
import "package:davos_admin/features/system/model/system_status.dart";
import "package:davos_admin/shared/controllers/loadable_controller.dart";

/// Health of every service the site depends on. Re-checks itself every 15 seconds while the screen is open.
class SystemController extends LoadableController {
  final Rxn<SystemStatus> status = Rxn<SystemStatus>();
  Timer? _timer;

  @override
  Future<void> fetch() async => status.value = await ApiService().getSystemStatus();

  @override
  void onReady() {
    super.onReady();
    _timer = Timer.periodic(const Duration(seconds: 15), (_) => _quietRefresh());
  }

  /// Refreshes without flashing the spinner; a failure keeps the last good picture and shows the error above it.
  Future<void> _quietRefresh() async {
    try {
      status.value = await ApiService().getSystemStatus();
      error.value = null;
    } on ApiError catch (e) {
      error.value = e.message;
    } catch (_) {}
  }

  @override
  void onClose() {
    _timer?.cancel();
    super.onClose();
  }
}
