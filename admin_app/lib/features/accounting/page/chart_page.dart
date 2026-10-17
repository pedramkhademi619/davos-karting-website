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

/// The chart of accounts as a tree, with add, edit and delete (an unused account is deactivated, never lost).
class ChartPage extends StatelessWidget {
  const ChartPage({super.key});

  @override
  Widget build(BuildContext context) {
    final data = Get.find<AccountingDataController>();
    return Scaffold(
      appBar: AppBar(title: const Text("سرفصل حساب‌ها")),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _edit(context, data, null),
        icon: const Icon(Icons.add),
        label: const Text("حساب جدید"),
      ),
      body: Obx(() {
        final state = StateView.from(
          loading: data.loading.value,
          isEmpty: data.accounts.isEmpty,
          error: data.error.value,
          emptyMessage: "حسابی ثبت نشده است.",
          onRetry: data.reload,
        );
        if (state != null) return state;
        List<Account> children(String? parent) =>
            data.accounts.where((a) => a.parentId == parent).toList()..sort((a, b) => a.code.compareTo(b.code));
        final rows = <Widget>[];
        void walk(String? parent, int depth) {
          for (final account in children(parent)) {
            rows.add(_row(context, data, account, depth));
            walk(account.id, depth + 1);
          }
        }

        walk(null, 0);
        return RefreshIndicator(
          onRefresh: data.reload,
          child: ListView(padding: const EdgeInsets.fromLTRB(12, 12, 12, 100), children: rows),
        );
      }),
    );
  }

  Widget _row(BuildContext context, AccountingDataController data, Account account, int depth) {
    return Padding(
      padding: EdgeInsetsDirectional.only(start: depth * 16.0, bottom: 6),
      child: AppCard(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        onTap: () => _edit(context, data, account),
        child: Row(
          children: [
            Icon(account.isGroup ? Icons.folder_rounded : Icons.description_outlined, size: 20, color: account.isGroup ? AppColors.accent : null),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text("${fa(account.code)}  ${account.name}", style: TextStyle(fontWeight: account.isGroup ? FontWeight.w800 : FontWeight.w500)),
                  Text(accountTypeLabels[account.type] ?? account.type, style: TextStyle(fontSize: 11, color: Theme.of(context).hintColor)),
                ],
              ),
            ),
            if (account.isSystem) const StatusChip("سیستمی", tone: Tone.info),
            if (!account.active) const Padding(padding: EdgeInsetsDirectional.only(start: 6), child: StatusChip("غیرفعال")),
          ],
        ),
      ),
    );
  }

  void _edit(BuildContext context, AccountingDataController data, Account? account) {
    final code = TextEditingController(text: account?.code ?? "");
    final name = TextEditingController(text: account?.name ?? "");
    var type = account?.type ?? "expense";
    var parent = account?.parentId;
    var isGroup = account?.isGroup ?? false;
    var active = account?.active ?? true;
    var busy = false;
    String? error;
    showFormSheet<void>(
      context,
      title: account == null ? "حساب جدید" : "ویرایش حساب",
      builder: (sheetContext) => StatefulBuilder(
        builder: (context, setState) => Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            LabeledField(label: "کد حساب", controller: code, number: true),
            LabeledField(label: "نام حساب", controller: name),
            ChoiceField<String>(
              label: "نوع",
              value: type,
              options: accountTypeLabels,
              onChanged: (v) => setState(() => type = v ?? type),
            ),
            ChoiceField<String>(
              label: "زیرمجموعهٔ (اختیاری)",
              value: parent ?? "",
              options: {
                "": "— بدون والد —",
                for (final a in data.accounts.where((a) => a.isGroup && a.id != account?.id)) a.id: "${a.code} - ${a.name}",
              },
              onChanged: (v) => setState(() => parent = (v == null || v.isEmpty) ? null : v),
            ),
            SwitchRow(title: "سرفصل گروه است", subtitle: "روی گروه سند ثبت نمی‌شود؛ فقط زیرحساب‌ها را در بر می‌گیرد.", value: isGroup, onChanged: (v) => setState(() => isGroup = v)),
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
                  await ApiService().saveAccount(
                    id: account?.id,
                    code: latin(code.text.trim()),
                    name: name.text.trim(),
                    type: type,
                    parentId: parent,
                    isGroup: isGroup,
                    active: active,
                  );
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
            if (account != null && !account.isSystem) ...[
              const SizedBox(height: 8),
              AppButton(
                label: "حذف حساب",
                outlined: true,
                danger: true,
                onPressed: () async {
                  if (!await confirm(sheetContext, title: "حذف حساب", message: "حساب بدون گردش حذف (غیرفعال) می‌شود. حساب دارای سند حذف نمی‌شود.", danger: true, confirmLabel: "حذف")) return;
                  try {
                    await ApiService().deleteAccount(account.id);
                    await data.reload();
                    if (sheetContext.mounted) Navigator.of(sheetContext).pop();
                    toast("حذف شد.");
                  } catch (e) {
                    setState(() => error = errorMessage(e));
                  }
                },
              ),
            ],
          ],
        ),
      ),
    );
  }
}
