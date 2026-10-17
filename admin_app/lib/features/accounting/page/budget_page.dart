import "package:flutter/material.dart";
import "package:get/get.dart";

import "package:davos_admin/core/theme/app_colors.dart";
import "package:davos_admin/core/utils/fa.dart";
import "package:davos_admin/core/utils/jalali.dart";
import "package:davos_admin/features/accounting/controller/budget_controller.dart";
import "package:davos_admin/features/accounting/model/accounting_models.dart";
import "package:davos_admin/features/accounting/widgets/accounting_fields.dart";
import "package:davos_admin/shared/dialog/dialogs.dart";
import "package:davos_admin/shared/widgets/app_button.dart";
import "package:davos_admin/shared/widgets/app_card.dart";
import "package:davos_admin/shared/widgets/form_fields.dart";
import "package:davos_admin/shared/widgets/info_widgets.dart";
import "package:davos_admin/shared/widgets/state_view.dart";

class BudgetPage extends GetView<BudgetController> {
  const BudgetPage({super.key});

  @override
  Widget build(BuildContext context) {
    final months = {for (var i = 0; i < 12; i++) i + 1: jalaliMonths[i]};
    return Scaffold(
      appBar: AppBar(title: const Text("بودجه")),
      floatingActionButton: FloatingActionButton.extended(onPressed: () => _set(context), icon: const Icon(Icons.edit_rounded), label: const Text("تعیین بودجه")),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 12, 12, 0),
            child: Obx(
              () => Row(
                children: [
                  Expanded(
                    child: ChoiceField<int>(
                      label: "سال",
                      value: controller.year.value,
                      options: {for (var y = currentJalaliYear() - 3; y <= currentJalaliYear() + 1; y++) y: fa(y)},
                      onChanged: (v) => controller.setRange(y: v),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(child: ChoiceField<int>(label: "از ماه", value: controller.monthFrom.value, options: months, onChanged: (v) => controller.setRange(from: v))),
                  const SizedBox(width: 8),
                  Expanded(child: ChoiceField<int>(label: "تا ماه", value: controller.monthTo.value, options: months, onChanged: (v) => controller.setRange(to: v))),
                ],
              ),
            ),
          ),
          Expanded(
            child: Obx(() {
              final state = StateView.from(
                loading: controller.loading.value,
                isEmpty: controller.rows.isEmpty,
                error: controller.error.value,
                emptyMessage: "بودجه‌ای تعریف نشده است.",
                onRetry: controller.reload,
              );
              if (state != null) return state;
              return RefreshIndicator(
                onRefresh: controller.reload,
                child: ListView(
                  padding: const EdgeInsets.fromLTRB(12, 0, 12, 100),
                  children: [
                    for (final r in controller.rows)
                      Padding(
                        padding: const EdgeInsets.only(bottom: 8),
                        child: AppCard(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text("${fa(r.code)}  ${r.name}", style: const TextStyle(fontWeight: FontWeight.w800)),
                              Text(accountTypeLabels[r.type] ?? r.type, style: TextStyle(fontSize: 11, color: Theme.of(context).hintColor)),
                              const SizedBox(height: 4),
                              InfoRow("بودجه", tomanFromIrr(r.budgetIrr)),
                              InfoRow("واقعی", tomanFromIrr(r.actualIrr)),
                              InfoRow(
                                "اختلاف",
                                tomanFromIrr(r.varianceIrr),
                                valueColor: r.varianceIrr == 0 ? null : _goodWhenPositive(r) ? AppColors.success : AppColors.danger,
                              ),
                              if (r.budgetIrr > 0)
                                LinearProgressIndicator(
                                  value: (r.actualIrr / r.budgetIrr).clamp(0, 1).toDouble(),
                                  color: r.type == "expense" && r.actualIrr > r.budgetIrr ? AppColors.danger : AppColors.success,
                                  minHeight: 6,
                                  borderRadius: BorderRadius.circular(3),
                                ),
                            ],
                          ),
                        ),
                      ),
                  ],
                ),
              );
            }),
          ),
        ],
      ),
    );
  }

  /// Revenue above budget is good; expenses above budget are not.
  bool _goodWhenPositive(BudgetRow r) => r.type == "expense" ? r.varianceIrr >= 0 : r.varianceIrr >= 0;

  void _set(BuildContext context) {
    String? account;
    int? month;
    final amount = TextEditingController();
    var busy = false;
    String? error;
    showFormSheet<void>(
      context,
      title: "تعیین بودجه سال ${fa(controller.year.value)}",
      builder: (sheetContext) => StatefulBuilder(
        builder: (context, setState) => Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            AccountField(label: "حساب", value: account, where: (a) => a.type == "expense" || a.type == "revenue", onChanged: (v) => setState(() => account = v)),
            ChoiceField<int>(
              label: "ماه",
              value: month ?? 0,
              options: {0: "کل سال (به‌طور مساوی بین ماه‌ها)", for (var i = 0; i < 12; i++) i + 1: jalaliMonths[i]},
              onChanged: (v) => setState(() => month = (v == null || v == 0) ? null : v),
            ),
            LabeledField(label: "مبلغ بودجه (تومان)", controller: amount, money: true),
            if (error != null) MessageBar(error!, error: true),
            AppButton(
              label: "ذخیره",
              busy: busy,
              onPressed: () async {
                setState(() {
                  busy = true;
                  error = null;
                });
                final m = await controller.setBudget(accountId: account ?? "", month: month, amountToman: moneyValue(amount));
                if (!sheetContext.mounted) return;
                if (m == null) {
                  Navigator.of(sheetContext).pop();
                  toast("بودجه ذخیره شد.");
                } else {
                  setState(() {
                    busy = false;
                    error = m;
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
