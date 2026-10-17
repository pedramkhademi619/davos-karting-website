import "package:flutter/material.dart";
import "package:get/get.dart";

import "package:davos_admin/core/services/api_service/api_service.dart";
import "package:davos_admin/core/utils/fa.dart";
import "package:davos_admin/core/utils/jalali.dart";
import "package:davos_admin/features/accounting/controller/assets_controller.dart";
import "package:davos_admin/features/accounting/widgets/accounting_fields.dart";
import "package:davos_admin/shared/dialog/dialogs.dart";
import "package:davos_admin/shared/widgets/app_button.dart";
import "package:davos_admin/shared/widgets/app_card.dart";
import "package:davos_admin/shared/widgets/form_fields.dart";
import "package:davos_admin/shared/widgets/info_widgets.dart";
import "package:davos_admin/shared/widgets/state_view.dart";
import "package:davos_admin/shared/widgets/status_chip.dart";

/// Fixed assets with straight-line depreciation: add one, book a month's depreciation, mark one sold or scrapped.
class AssetsPage extends GetView<AssetsController> {
  const AssetsPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("دارایی‌های ثابت"),
        actions: [IconButton(tooltip: "ثبت استهلاک ماهانه", icon: const Icon(Icons.timelapse_rounded), onPressed: () => _depreciation(context))],
      ),
      floatingActionButton: FloatingActionButton.extended(onPressed: () => _add(context), icon: const Icon(Icons.add), label: const Text("دارایی جدید")),
      body: Obx(() {
        final state = StateView.from(
          loading: controller.loading.value,
          isEmpty: controller.assets.isEmpty,
          error: controller.error.value,
          emptyMessage: "دارایی ثابتی ثبت نشده است.",
          onRetry: controller.reload,
        );
        if (state != null) return state;
        return RefreshIndicator(
          onRefresh: controller.reload,
          child: ListView(
            padding: const EdgeInsets.fromLTRB(12, 12, 12, 100),
            children: [
              for (final a in controller.assets)
                Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: AppCard(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Expanded(child: Text(a.name, style: const TextStyle(fontWeight: FontWeight.w800))),
                            StatusChip(a.disposed ? "فروخته/اسقاط" : "در خدمت", tone: a.disposed ? Tone.neutral : Tone.success),
                          ],
                        ),
                        const SizedBox(height: 4),
                        InfoRow("بهای تمام‌شده (تومان)", tomanFromIrr(a.costIrr)),
                        InfoRow("ارزش اسقاط (تومان)", tomanFromIrr(a.salvageIrr)),
                        InfoRow("استهلاک انباشته (تومان)", tomanFromIrr(a.accumulatedIrr)),
                        InfoRow("ارزش دفتری (تومان)", tomanFromIrr(a.bookValueIrr), bold: true),
                        InfoRow("شروع بهره‌برداری", jalaliText(a.inServiceDate)),
                        InfoRow("عمر مفید", "${fa(a.lifeMonths)} ماه"),
                        if (!a.disposed)
                          TextButton(
                            onPressed: () async {
                              if (!await confirm(context, title: "فروش یا اسقاط", message: "«${a.name}» دیگر استهلاک نمی‌خورد.", confirmLabel: "تایید")) return;
                              final m = await controller.disposeAsset(a);
                              toast(m ?? "ثبت شد.", error: m != null);
                            },
                            child: const Text("فروخته یا اسقاط شد"),
                          ),
                      ],
                    ),
                  ),
                ),
            ],
          ),
        );
      }),
    );
  }

  void _depreciation(BuildContext context) {
    final year = TextEditingController(text: fa(currentJalaliYear()));
    var month = jalaliOfIso(todayIso()).month;
    var busy = false;
    String? message;
    var isError = false;
    showFormSheet<void>(
      context,
      title: "ثبت استهلاک ماهانه",
      builder: (sheetContext) => StatefulBuilder(
        builder: (context, setState) => Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text("استهلاک یک ماه برای همهٔ دارایی‌های در خدمت ثبت می‌شود. ثبت دوباره برای همان ماه انجام نمی‌شود.", style: TextStyle(height: 1.7)),
            const SizedBox(height: 12),
            LabeledField(label: "سال شمسی", controller: year, number: true),
            ChoiceField<int>(label: "ماه", value: month, options: {for (var i = 0; i < 12; i++) i + 1: jalaliMonths[i]}, onChanged: (v) => setState(() => month = v ?? month)),
            if (message != null) MessageBar(message!, error: isError),
            AppButton(
              label: "ثبت استهلاک",
              busy: busy,
              onPressed: () async {
                setState(() => busy = true);
                final r = await controller.depreciate(parseInt(year.text), month);
                setState(() {
                  busy = false;
                  isError = r.$2;
                  message = r.$2 ? r.$1 : "استهلاک ثبت شد.";
                });
              },
            ),
          ],
        ),
      ),
    );
  }

  void _add(BuildContext context) {
    final name = TextEditingController();
    final cost = TextEditingController();
    final salvage = TextEditingController();
    final life = TextEditingController(text: fa(60));
    String? account;
    String? paidFrom;
    String? vendor;
    var day = businessDayIso();
    var post = true;
    var busy = false;
    String? error;
    showFormSheet<void>(
      context,
      title: "دارایی جدید",
      builder: (sheetContext) => StatefulBuilder(
        builder: (context, setState) => Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            LabeledField(label: "نام دارایی", controller: name),
            AccountField(label: "حساب دارایی", value: account, type: "asset", where: (a) => !a.holdsMoney, onChanged: (v) => setState(() => account = v)),
            LabeledField(label: "بهای تمام‌شده (تومان)", controller: cost, money: true),
            LabeledField(label: "ارزش اسقاط (تومان)", controller: salvage, money: true),
            DateField(label: "شروع بهره‌برداری", value: day, onChanged: (v) => setState(() => day = v ?? day)),
            LabeledField(label: "عمر مفید (ماه)", controller: life, number: true),
            SwitchRow(title: "خرید همین حالا در دفتر ثبت شود", subtitle: "اگر دارایی از قبل در افتتاحیه آمده، خاموش کنید.", value: post, onChanged: (v) => setState(() => post = v)),
            if (post) ...[
              AccountField(label: "پرداخت از", value: paidFrom, where: (a) => a.holdsMoney, optional: true, onChanged: (v) => setState(() => paidFrom = v)),
              VendorField(value: vendor, onChanged: (v) => setState(() => vendor = v)),
            ],
            if (error != null) MessageBar(error!, error: true),
            AppButton(
              label: "ثبت دارایی",
              busy: busy,
              onPressed: () async {
                setState(() {
                  busy = true;
                  error = null;
                });
                try {
                  await ApiService().addAsset(
                    name: name.text.trim(),
                    assetAccountId: account ?? "",
                    costToman: moneyValue(cost),
                    salvageToman: moneyValue(salvage),
                    inServiceDate: day,
                    lifeMonths: parseInt(life.text),
                    postPurchase: post,
                    paidFromAccountId: post ? paidFrom : null,
                    vendorId: post ? vendor : null,
                  );
                  await controller.reload();
                  if (sheetContext.mounted) Navigator.of(sheetContext).pop();
                  toast("دارایی ثبت شد.");
                } catch (e) {
                  setState(() {
                    busy = false;
                    error = errorMessage(e);
                  });
                }
              },
            ),
          ],
        ),
      ),
    );
  }
}
