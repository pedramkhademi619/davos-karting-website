import "package:get/get.dart";

import "package:davos_admin/core/services/api_service/api_service.dart";
import "package:davos_admin/core/utils/jalali.dart";
import "package:davos_admin/features/accounting/model/accounting_models.dart";
import "package:davos_admin/shared/controllers/loadable_controller.dart";

/// End-of-day till count: what the books say the till holds, what was counted, and the difference.
class CashController extends LoadableController {
  final RxString day = businessDayIso().obs;
  final Rxn<CashState> state = Rxn<CashState>();

  @override
  Future<void> fetch() async => state.value = await ApiService().getCash(day.value);

  Future<void> setDay(String iso) {
    day.value = iso;
    return reload();
  }

  Future<String?> close(int countedToman, String note) => guard(() async {
    await ApiService().closeCash(date: day.value, countedToman: countedToman, note: note);
    await reload();
  });
}
