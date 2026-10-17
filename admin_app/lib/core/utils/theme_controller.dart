import "package:flutter/material.dart";
import "package:get/get.dart";

import "package:davos_admin/core/services/storage_service/storage_service.dart";

/// Light, dark or follow the phone. Remembered between runs.
class ThemeController extends GetxController {
  final StorageService _storage = StorageService();
  final Rx<ThemeMode> mode = ThemeMode.system.obs;

  static const _order = [ThemeMode.system, ThemeMode.light, ThemeMode.dark];

  @override
  void onInit() {
    super.onInit();
    mode.value = switch (_storage.readThemeMode()) {
      "light" => ThemeMode.light,
      "dark" => ThemeMode.dark,
      _ => ThemeMode.system,
    };
  }

  String get label => switch (mode.value) {
    ThemeMode.light => "روشن",
    ThemeMode.dark => "تیره",
    ThemeMode.system => "مطابق گوشی",
  };

  void cycle() {
    final next = _order[(_order.indexOf(mode.value) + 1) % _order.length];
    mode.value = next;
    Get.changeThemeMode(next);
    _storage.writeThemeMode(next.name);
  }
}
