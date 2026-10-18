import "package:flutter/material.dart";
import "package:get/get.dart";

import "package:davos_admin/core/services/api_service/api_service.dart";
import "package:davos_admin/core/utils/fa.dart";
import "package:davos_admin/core/utils/jalali.dart";
import "package:davos_admin/features/sms/model/sms_models.dart";
import "package:davos_admin/shared/controllers/loadable_controller.dart";

/// SMS panel: provider and credit, the log of sent messages and the form to send a new text.
class SmsController extends PagedController<SmsLog> {
  final Rxn<SmsAccount> account = Rxn<SmsAccount>();

  // Send form
  final RxString audience = "numbers".obs;
  final TextEditingController numbers = TextEditingController();
  final TextEditingController text = TextEditingController();
  final RxnString day = RxnString();
  final RxBool sending = false.obs;
  final RxBool confirming = false.obs;
  final Rxn<String> sendMessage = Rxn<String>();
  final RxBool sendFailed = false.obs;

  @override
  Future<void> fetchPage(int offset) async {
    final api = ApiService();
    account.value = await api.getSmsAccount();
    final page = await api.getSmsMessages(offset: offset, limit: pageSize);
    items.assignAll(page.items);
    total.value = page.total;
  }

  /// Typed numbers split on spaces, commas and new lines; digits turned to Latin.
  List<String> get numberList => latin(numbers.text)
      .split(RegExp(r"[\s,;،]+"))
      .map((e) => e.trim())
      .where((e) => e.isNotEmpty)
      .toList();

  int get recipientCount => audience.value == "numbers" ? numberList.length : 0;

  String get audienceLabel => switch (audience.value) {
    "numbers" => "${fa(numberList.length)} شماره",
    "subscribers" => "همه مشترکان خبرنامه",
    _ => "مشتریان روز ${jalaliText(day.value ?? todayIso())}",
  };

  bool get canSend =>
      text.text.trim().isNotEmpty &&
      (audience.value != "numbers" || numberList.isNotEmpty);

  /// First tap asks to confirm; the second one sends.
  Future<void> send() async {
    sendMessage.value = null;
    if (!confirming.value) {
      confirming.value = true;
      return;
    }
    sending.value = true;
    try {
      final result = await ApiService().sendSms(
        audience: audience.value,
        numbers: audience.value == "numbers" ? numberList : const [],
        day: audience.value == "day" ? (day.value ?? todayIso()) : null,
        text: text.text.trim(),
      );
      final invalid = result.invalidNumbers.isEmpty ? "" : " شماره‌های نامعتبر: ${result.invalidNumbers.join("، ")}";
      sendMessage.value = "${fa(result.accepted)} پیامک پذیرفته شد، ${fa(result.failed)} ناموفق.$invalid";
      sendFailed.value = false;
      text.clear();
      await reload();
    } catch (e) {
      sendMessage.value = errorMessage(e);
      sendFailed.value = true;
    } finally {
      sending.value = false;
      confirming.value = false;
    }
  }

  void cancelConfirm() => confirming.value = false;

  @override
  void onClose() {
    numbers.dispose();
    text.dispose();
    super.onClose();
  }
}
