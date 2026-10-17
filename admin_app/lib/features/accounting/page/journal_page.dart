import "package:flutter/material.dart";
import "package:get/get.dart";

import "package:davos_admin/core/theme/app_colors.dart";
import "package:davos_admin/core/utils/fa.dart";
import "package:davos_admin/core/utils/jalali.dart";
import "package:davos_admin/features/accounting/controller/accounting_data_controller.dart";
import "package:davos_admin/features/accounting/controller/journal_controller.dart";
import "package:davos_admin/features/accounting/model/accounting_models.dart";
import "package:davos_admin/features/accounting/widgets/accounting_fields.dart";
import "package:davos_admin/shared/dialog/dialogs.dart";
import "package:davos_admin/shared/widgets/app_button.dart";
import "package:davos_admin/shared/widgets/app_card.dart";
import "package:davos_admin/shared/widgets/form_fields.dart";
import "package:davos_admin/shared/widgets/info_widgets.dart";
import "package:davos_admin/shared/widgets/pager_bar.dart";
import "package:davos_admin/shared/widgets/search_box.dart";
import "package:davos_admin/shared/widgets/state_view.dart";
import "package:davos_admin/shared/widgets/status_chip.dart";

class JournalPage extends GetView<JournalController> {
  const JournalPage({super.key});

  @override
  Widget build(BuildContext context) {
    final data = Get.find<AccountingDataController>();
    return Scaffold(
      appBar: AppBar(title: const Text("دفتر روزنامه")),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _manualEntry(context),
        icon: const Icon(Icons.edit_note_rounded),
        label: const Text("سند دستی"),
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 12, 12, 6),
            child: SearchBox(controller: controller.search, onSearch: controller.submitSearch, hint: "شرح سند یا شماره"),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12),
            child: Obx(
              () => PillSelector<String>(
                options: {"": "همه", ...entrySourceLabels},
                value: controller.source.value,
                onChanged: controller.setSource,
              ),
            ),
          ),
          Expanded(
            child: Obx(() {
              final state = StateView.from(
                loading: controller.loading.value,
                isEmpty: controller.items.isEmpty,
                error: controller.error.value,
                emptyMessage: "سندی پیدا نشد.",
                onRetry: controller.reload,
              );
              if (state != null) return state;
              return RefreshIndicator(
                onRefresh: controller.reload,
                child: ListView(
                  padding: const EdgeInsets.fromLTRB(12, 8, 12, 100),
                  children: [
                    for (final entry in controller.items)
                      Padding(
                        padding: const EdgeInsets.only(bottom: 8),
                        child: AppCard(
                          onTap: () => _show(context, entry),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  Text("سند ${fa(entry.number)}", style: const TextStyle(fontWeight: FontWeight.w800)),
                                  Text("  سال ${fa(entry.fiscalYear)}", style: TextStyle(color: Theme.of(context).hintColor, fontSize: 12)),
                                  const Spacer(),
                                  if (entry.reversed) const StatusChip("باطل شده", tone: Tone.danger) else StatusChip(entry.sourceLabel),
                                ],
                              ),
                              const SizedBox(height: 4),
                              Text(entry.description, style: const TextStyle(height: 1.6)),
                              const SizedBox(height: 4),
                              Row(
                                children: [
                                  Text(jalaliText(entry.date), style: TextStyle(fontSize: 12, color: Theme.of(context).hintColor)),
                                  const Spacer(),
                                  Text("${tomanFromIrr(entry.totalIrr)} تومان", style: const TextStyle(fontWeight: FontWeight.w700)),
                                ],
                              ),
                            ],
                          ),
                        ),
                      ),
                    PagerBar(controller: controller),
                  ],
                ),
              );
            }),
          ),
        ],
      ),
      bottomNavigationBar: Obx(
        () => data.accounts.isEmpty
            ? const SizedBox.shrink()
            : SafeArea(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(12, 0, 12, 4),
                  child: AccountField(
                    label: "فیلتر بر اساس حساب",
                    value: controller.accountId.value,
                    optional: true,
                    onChanged: controller.setAccount,
                  ),
                ),
              ),
      ),
    );
  }

  void _show(BuildContext context, Entry entry) {
    showFormSheet<void>(
      context,
      title: "سند ${fa(entry.number)} • ${jalaliText(entry.date)}",
      builder: (sheetContext) => Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(entry.description, style: const TextStyle(height: 1.7)),
          const SizedBox(height: 4),
          Text("${entry.sourceLabel} • ثبت‌کننده: ${entry.createdBy}", style: TextStyle(fontSize: 12, color: Theme.of(context).hintColor)),
          const SizedBox(height: 10),
          for (final line in entry.lines)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 5),
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text("${fa(line.accountCode)} - ${line.accountName}", style: const TextStyle(fontWeight: FontWeight.w600)),
                        if (line.memo.isNotEmpty || line.vendorName.isNotEmpty)
                          Text([line.vendorName, line.memo].where((e) => e.isNotEmpty).join(" • "), style: const TextStyle(fontSize: 12)),
                      ],
                    ),
                  ),
                  Text(
                    line.debitIrr > 0 ? "بدهکار ${tomanFromIrr(line.debitIrr)}" : "بستانکار ${tomanFromIrr(line.creditIrr)}",
                    style: TextStyle(color: line.debitIrr > 0 ? AppColors.success : AppColors.danger, fontWeight: FontWeight.w700),
                  ),
                ],
              ),
            ),
          const Divider(height: 24),
          InfoRow("جمع (تومان)", tomanFromIrr(entry.totalIrr), bold: true),
          if (!entry.reversed && entry.source != "reversal")
            AppButton(
              label: "ابطال سند",
              outlined: true,
              danger: true,
              onPressed: () async {
                final reason = TextEditingController();
                final yes = await showDialog<bool>(
                  context: sheetContext,
                  builder: (d) => AlertDialog(
                    title: const Text("ابطال سند"),
                    content: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Text("برای این سند یک سند معکوس ثبت می‌شود و سند اصلی باطل علامت می‌خورد. حذف نمی‌شود.", style: TextStyle(height: 1.7)),
                        const SizedBox(height: 8),
                        TextField(controller: reason, decoration: const InputDecoration(hintText: "دلیل ابطال")),
                      ],
                    ),
                    actions: [
                      TextButton(onPressed: () => Navigator.of(d).pop(false), child: const Text("انصراف")),
                      FilledButton(onPressed: () => Navigator.of(d).pop(true), child: const Text("ابطال")),
                    ],
                  ),
                );
                final text = reason.text.trim();
                reason.dispose();
                if (yes != true) return;
                final m = await controller.reverse(entry, text);
                if (!sheetContext.mounted) return;
                if (m == null) {
                  Navigator.of(sheetContext).pop();
                  toast("سند باطل شد.");
                } else {
                  toast(m, error: true);
                }
              },
            ),
        ],
      ),
    );
  }

  void _manualEntry(BuildContext context) {
    final lines = <_Line>[_Line(), _Line()];
    final description = TextEditingController();
    var day = businessDayIso();
    var opening = false;
    var busy = false;
    String? error;
    showFormSheet<void>(
      context,
      title: "سند دستی",
      builder: (sheetContext) => StatefulBuilder(
        builder: (context, setState) {
          final debit = lines.fold<int>(0, (s, l) => s + parseInt(l.debit.text));
          final credit = lines.fold<int>(0, (s, l) => s + parseInt(l.credit.text));
          return Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              DateField(label: "تاریخ", value: day, onChanged: (v) => setState(() => day = v ?? day)),
              LabeledField(label: "شرح سند", controller: description, lines: 2),
              SwitchRow(title: "سند افتتاحیه", subtitle: "برای ثبت مانده‌های ابتدای کار.", value: opening, onChanged: (v) => setState(() => opening = v)),
              for (var i = 0; i < lines.length; i++)
                AppCard(
                  padding: const EdgeInsets.all(10),
                  child: Column(
                    children: [
                      AccountField(label: "حساب ${fa(i + 1)}", value: lines[i].account, onChanged: (v) => setState(() => lines[i].account = v)),
                      Row(
                        children: [
                          Expanded(child: LabeledField(label: "بدهکار (تومان)", controller: lines[i].debit, money: true, onChanged: (_) => setState(() {}))),
                          const SizedBox(width: 8),
                          Expanded(child: LabeledField(label: "بستانکار (تومان)", controller: lines[i].credit, money: true, onChanged: (_) => setState(() {}))),
                        ],
                      ),
                      LabeledField(label: "توضیح ردیف", controller: lines[i].memo),
                      if (lines.length > 2) TextButton(onPressed: () => setState(() => lines.removeAt(i)), child: const Text("حذف ردیف")),
                    ],
                  ),
                ),
              TextButton.icon(onPressed: () => setState(() => lines.add(_Line())), icon: const Icon(Icons.add), label: const Text("افزودن ردیف")),
              InfoRow("جمع بدهکار", grouped(debit)),
              InfoRow("جمع بستانکار", grouped(credit)),
              if (debit != credit) const MessageBar("جمع بدهکار و بستانکار باید برابر باشد.", error: true),
              if (error != null) MessageBar(error!, error: true),
              AppButton(
                label: "ثبت سند",
                busy: busy,
                onPressed: debit == 0 || debit != credit
                    ? null
                    : () async {
                        setState(() {
                          busy = true;
                          error = null;
                        });
                        final m = await controller.postManual(
                          date: day,
                          description: description.text.trim(),
                          opening: opening,
                          lines: [
                            for (final l in lines.where((l) => l.account != null && (parseInt(l.debit.text) > 0 || parseInt(l.credit.text) > 0)))
                              {
                                "account_id": l.account,
                                "debit_toman": parseInt(l.debit.text),
                                "credit_toman": parseInt(l.credit.text),
                                "memo": l.memo.text.trim(),
                                "vendor_id": null,
                              },
                          ],
                        );
                        if (!sheetContext.mounted) return;
                        if (m == null) {
                          Navigator.of(sheetContext).pop();
                          toast("سند ثبت شد.");
                        } else {
                          setState(() {
                            busy = false;
                            error = m;
                          });
                        }
                      },
              ),
            ],
          );
        },
      ),
    );
  }
}

class _Line {
  String? account;
  final TextEditingController debit = TextEditingController();
  final TextEditingController credit = TextEditingController();
  final TextEditingController memo = TextEditingController();
}
