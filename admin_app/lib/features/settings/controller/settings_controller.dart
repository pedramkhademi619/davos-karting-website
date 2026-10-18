import "package:get/get.dart";

import "package:davos_admin/core/services/api_service/api_service.dart";
import "package:davos_admin/features/settings/model/schedule_settings.dart";
import "package:davos_admin/shared/controllers/loadable_controller.dart";

class SettingsController extends LoadableController {
  final Rxn<ScheduleSettings> settings = Rxn<ScheduleSettings>();

  @override
  Future<void> fetch() async => settings.value = await ApiService().getScheduleSettings();

  /// Saves and returns null, or the message to show.
  Future<String?> save(ScheduleSettings edited) => guard(() async {
    settings.value = await ApiService().saveScheduleSettings(edited);
  });
}
