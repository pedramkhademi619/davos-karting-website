import "package:flutter/material.dart";
import "package:get/get.dart";

import "package:davos_admin/core/services/api_service/api_service.dart";
import "package:davos_admin/core/theme/app_colors.dart";
import "package:davos_admin/core/utils/fa.dart";
import "package:davos_admin/features/accounting/controller/accounting_data_controller.dart";
import "package:davos_admin/features/accounting/model/accounting_models.dart";
import "package:davos_admin/shared/dialog/dialogs.dart";
import "package:davos_admin/shared/widgets/app_button.dart";
import "package:davos_admin/shared/widgets/app_card.dart";
import "package:davos_admin/shared/widgets/form_fields.dart";
import "package:davos_admin/shared/widgets/info_widgets.dart";
import "package:davos_admin/shared/widgets/state_view.dart";
import "package:davos_admin/shared/widgets/status_chip.dart";

/// Suppliers with what is owed to each and how old the debt is.
class VendorsPage extends StatelessWidget {
  const VendorsPage({super.key});

  @override
  Widget build(BuildContext context) {
    final data = Get.find<AccountingDataController>();
    return Scaffold(
      appBar: AppBar(title: const Text("تامین‌کنندگان")),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _edit(context, data, null),
        icon: const Icon(Icons.add),
        label: const Text("تامین‌کنندهٔ جدید"),
      ),
      body: Obx(() {
        final state = StateView.from(
          loading: data.loading.value,
          isEmpty: data.vendors.isEmpty,
          error: data.error.value,
          emptyMessage: "تامین‌کننده‌ای ثبت نشده است.",
          onRetry: data.reload,
        );
        if (state != null) return state;
        final totalOwed = data.vendors.fold<int>(0, (s, v) => s + v.owedIrr);
        return RefreshIndicator(
          onRefresh: data.reload,
          child: ListView(
            padding: const EdgeInsets.fromLTRB(12, 12, 12, 100),
            children: [
              AppCard(child: InfoRow("جمع بدهی به تامین‌کنندگان (تومان)", tomanFromIrr(totalOwed), bold: true, valueColor: totalOwed > 0 ? AppColors.danger : null)),
              const SizedBox(height: 8),
              for (final v in data.vendors)
                Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: AppCard(
                    onTap: () => _edit(context, data, v),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Expanded(child: Text(v.name, style: const TextStyle(fontWeight: FontWeight.w800))),
                            if (!v.active) const StatusChip("غیرفعال"),
                          ],
                        ),
                        if (v.phone.isNotEmpty) Text(fa(v.phone), textDirection: TextDirection.ltr, style: TextStyle(color: Theme.of(context).hintColor)),
                        const SizedBox(height: 6),
                        InfoRow("بدهی (تومان)", tomanFromIrr(v.owedIrr), bold: true, valueColor: v.owedIrr > 0 ? AppColors.danger : null),
                        if (v.owedIrr > 0) ...[
                          InfoRow("تا ۳۰ روز", tomanOrDash(v.age0to30Irr)),
                          InfoRow("۳۱ تا ۶۰ روز", tomanOrDash(v.age31to60Irr)),
                          InfoRow("۶۱ تا ۹۰ روز", tomanOrDash(v.age61to90Irr)),
                          InfoRow("بیش از ۹۰ روز", tomanOrDash(v.ageOver90Irr), valueColor: v.ageOver90Irr > 0 ? AppColors.danger : null),
                        ],
                        if (v.advanceIrr > 0) InfoRow("پیش‌پرداخت به او", tomanFromIrr(v.advanceIrr)),
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

  void _edit(BuildContext context, AccountingDataController data, Vendor? vendor) {
    final name = TextEditingController(text: vendor?.name ?? "");
    final phone = TextEditingController(text: vendor?.phone ?? "");
    final note = TextEditingController(text: vendor?.note ?? "");
    var active = vendor?.active ?? true;
    var busy = false;
    String? error;
    showFormSheet<void>(
      context,
      title: vendor == null ? "تامین‌کنندهٔ جدید" : "ویرایش تامین‌کننده",
      builder: (sheetContext) => StatefulBuilder(
        builder: (context, setState) => Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            LabeledField(label: "نام", controller: name),
            LabeledField(label: "تلفن", controller: phone, phone: true),
            LabeledField(label: "یادداشت", controller: note, lines: 2),
            SwitchRow(title: "فعال", value: active, onChanged: (v) => setState(() => active = v)),
            if (error != null) MessageBar(error!, error: true),
            AppButton(
              label: "ذخیره",
              busy: busy,
              onPressed: () async {
                setState(() {
                  busy = true;
                  error = null;
                });
                try {
                  await ApiService().saveVendor(id: vendor?.id, name: name.text.trim(), phone: latin(phone.text.trim()), note: note.text.trim(), active: active);
                  await data.reload();
                  if (sheetContext.mounted) Navigator.of(sheetContext).pop();
                  toast("ذخیره شد.");
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
