import "package:get/get.dart";

import "package:davos_admin/core/services/api_service/api_service.dart";
import "package:davos_admin/features/accounting/model/accounting_models.dart";
import "package:davos_admin/shared/controllers/loadable_controller.dart";

class AssetsController extends LoadableController {
  final RxList<Asset> assets = <Asset>[].obs;

  @override
  Future<void> fetch() async => assets.assignAll(await ApiService().getAssets());

  Future<String?> disposeAsset(Asset asset) => guard(() async {
    await ApiService().disposeAsset(asset.id);
    await reload();
  });

  /// Books one month's depreciation; returns the message to show (total or error).
  Future<(String, bool)> depreciate(int year, int month) async {
    try {
      final total = await ApiService().runDepreciation(year, month);
      await reload();
      return ("استهلاک ثبت شد؛ جمع: $total", false);
    } catch (e) {
      return (errorMessage(e), true);
    }
  }
}
