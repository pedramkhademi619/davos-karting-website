import "package:flutter/material.dart";
import "package:get/get.dart";

import "package:davos_admin/core/theme/app_colors.dart";
import "package:davos_admin/core/utils/fa.dart";
import "package:davos_admin/core/utils/jalali.dart";
import "package:davos_admin/features/accounting/controller/cash_controller.dart";
import "package:davos_admin/shared/dialog/dialogs.dart";
import "package:davos_admin/shared/widgets/app_button.dart";
import "package:davos_admin/shared/widgets/app_card.dart";
import "package:davos_admin/shared/widgets/form_fields.dart";
import "package:davos_admin/shared/widgets/info_widgets.dart";
import "package:davos_admin/shared/widgets/state_view.dart";

class CashPage extends StatefulWidget {
  const CashPage({super.key});

  @override
  State<CashPage> createState() => _CashPageState();
}

class _CashPageState extends State<CashPage> {
  final controller = Get.find<CashController>();
  final _counted = TextEditingController();
  final _note = TextEditingController();
  bool _busy = false;

  @override
  void dispose() {
    _counted.dispose();
    _note.dispose();
    super.dispose();
  }

  Future<void> _close() async {
    final counted = moneyValue(_counted);
    final expected = irrToToman(controller.state.value?.expectedIrr ?? 0);
    final difference = counted - expected;
    final ok = await confirm(
      context,
      title: "بستن صندوق",
      message: difference == 0
          ? "مبلغ شمارش‌شده با دفتر برابر است."
          : "اختلاف ${tomanText(difference.abs())} ${difference > 0 ? "اضافه" : "کسر"} است و به‌عنوان ${difference > 0 ? "اضافی" : "کسری"} صندوق در دفتر ثبت می‌شود.",
      confirmLabel: "بستن صندوق",
    );
    if (!ok) return;
    setState(() => _busy = true);
    final message = await controller.close(counted, _note.text.trim());
    if (!mounted) return;
    setState(() => _busy = false);
    if (message == null) {
      _counted.clear();
      _note.clear();
      toast("صندوق بسته شد.");
    } else {
      toast(message, error: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("صندوق‌گردانی")),
      body: Obx(() {
        final s = controller.state.value;
        final state = StateView.from(
          loading: controller.loading.value,
          isEmpty: s == null,
          error: controller.error.value,
          emptyMessage: "اطلاعاتی نیست.",
          onRetry: controller.reload,
        );
        if (state != null) return state;
        final data = s!;
        return RefreshIndicator(
          onRefresh: controller.reload,
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              DateField(label: "روز", value: controller.day.value, onChanged: (v) => controller.setDay(v ?? controller.day.value)),
              AppCard(child: InfoRow("موجودی صندوق طبق دفتر (تومان)", tomanFromIrr(data.expectedIrr), bold: true)),
              const SizedBox(height: 12),
              LabeledField(label: "مبلغ شمارش‌شده (تومان)", controller: _counted, money: true),
              LabeledField(label: "یادداشت", controller: _note, lines: 2),
              AppButton(label: "بستن صندوق این روز", onPressed: _close, busy: _busy),
              const SectionTitle("بستن‌های اخیر"),
              if (data.closings.isEmpty) const AppCard(child: Text("هنوز صندوقی بسته نشده است.")),
              for (final c in data.closings)
                Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: AppCard(
                    child: Column(
                      children: [
                        InfoRow("روز", jalaliText(c.date), bold: true),
                        InfoRow("طبق دفتر", tomanFromIrr(c.expectedIrr)),
                        InfoRow("شمارش‌شده", tomanFromIrr(c.countedIrr)),
                        InfoRow(
                          "اختلاف",
                          c.differenceIrr == 0 ? "ندارد" : tomanFromIrr(c.differenceIrr),
                          valueColor: c.differenceIrr == 0 ? AppColors.success : AppColors.danger,
                        ),
                        if (c.note.isNotEmpty) InfoRow("یادداشت", c.note),
                        InfoRow("بسته‌کننده", c.closedBy),
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
}
