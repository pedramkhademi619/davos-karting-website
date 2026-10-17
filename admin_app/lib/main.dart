import "package:flutter/material.dart";
import "package:get_storage/get_storage.dart";

import "package:davos_admin/core/utils/admin_app.dart";

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await GetStorage.init();
  runApp(const AdminApp());
}
