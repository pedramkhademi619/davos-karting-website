import "package:flutter/material.dart";
import "package:get/get.dart";

import "package:davos_admin/core/services/api_service/api_service.dart";
import "package:davos_admin/core/theme/pit.dart";
import "package:davos_admin/core/utils/fa.dart";
import "package:davos_admin/features/accounting/controller/accounting_data_controller.dart";
import "package:davos_admin/features/accounting/model/accounting_models.dart";
import "package:davos_admin/shared/dialog/dialogs.dart";
import "package:davos_admin/shared/widgets/app_card.dart";
import "package:davos_admin/shared/widgets/form_fields.dart";
import "package:davos_admin/shared/widgets/state_view.dart";

/// The income and expense categories the owner picks from when recording money: add, rename, hide or bring back.
class CategoriesPage extends StatelessWidget {
  const CategoriesPage({super.key});

  @override
  Widget build(BuildContext context) {
    final data = Get.find<AccountingDataController>();
    return Scaffold(
      appBar: AppBar(title: const Text("دسته‌ها")),
      body: Obx(() {
        if (data.loading.value && data.accounts.isEmpty) return StateView.loading();
        if (data.error.value != null && data.accounts.isEmpty) return StateView.error(data.error.value!, onRetry: data.reload);
        return RefreshIndicator(
          onRefresh: data.reload,
          child: ListView(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 40),
            children: [
              _Section(kind: "expense", title: "دسته‌های هزینه", data: data),
              const SizedBox(height: 14),
              _Section(kind: "revenue", title: "دسته‌های درآمد", data: data),
              Padding(
                padding: const EdgeInsets.only(top: 14),
                child: Text(
                  "فروش بلیت، استرداد، کارمزد بانک و کسری صندوق خودکار ثبت می‌شوند و اینجا نمی‌آیند. دسته‌ای که پنهان کنید در فرم ثبت دیده نمی‌شود، ولی گزارش‌های قبلی‌اش سر جایش می‌ماند.",
                  style: TextStyle(color: context.pit.mid, fontSize: 12.5, height: 1.8),
                ),
              ),
            ],
          ),
        );
      }),
    );
  }
}

class _Section extends StatefulWidget {
  const _Section({required this.kind, required this.title, required this.data});

  final String kind;
  final String title;
  final AccountingDataController data;

  @override
  State<_Section> createState() => _SectionState();
}

class _SectionState extends State<_Section> {
  final _name = TextEditingController();
  bool _busy = false;

  @override
  void dispose() {
    _name.dispose();
    super.dispose();
  }

  Future<void> _run(Future<void> Function() action) async {
    setState(() => _busy = true);
    try {
      await action();
      await widget.data.reload();
    } catch (e) {
      toast(errorMessage(e), error: true);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _save(Account a, {String? name, bool? active}) => ApiService().saveAccount(
    id: a.id,
    code: a.code,
    name: name ?? a.name,
    type: a.type,
    parentId: a.parentId,
    active: active ?? a.active,
  );

  Future<void> _rename(Account a) async {
    final controller = TextEditingController(text: a.name);
    final ok = await showFormSheet<bool>(
      context,
      title: "تغییر نام دسته",
      builder: (sheet) => Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          LabeledField(label: "نام", controller: controller, autofocus: true, maxLength: 120),
          FilledButton(onPressed: () => Navigator.of(sheet).pop(true), child: const Text("ذخیره")),
        ],
      ),
    );
    final name = controller.text.trim();
    controller.dispose();
    if (ok == true && name.isNotEmpty) await _run(() => _save(a, name: name));
  }

  Future<void> _add() async {
    final name = _name.text.trim();
    if (name.isEmpty) return;
    final parent = widget.data.parentFor(widget.kind);
    await _run(() async {
      await ApiService().saveAccount(code: widget.data.nextCode(widget.kind), name: name, type: widget.kind, parentId: parent?.id, active: true);
      _name.clear();
    });
  }

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    final all = widget.data.categories(widget.kind, includeHidden: true);
    final shown = all.where((a) => a.active).toList();
    final hidden = all.where((a) => !a.active).toList();
    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(widget.title, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15)),
          const SizedBox(height: 6),
          for (final a in shown)
            Row(
              children: [
                Expanded(child: Text(a.name, style: const TextStyle(fontWeight: FontWeight.w600))),
                TextButton(onPressed: _busy ? null : () => _rename(a), child: const Text("تغییر نام")),
                TextButton(onPressed: _busy ? null : () => _run(() => _save(a, active: false)), child: const Text("پنهان")),
              ],
            ),
          if (hidden.isNotEmpty)
            ExpansionTile(
              tilePadding: EdgeInsets.zero,
              title: Text("پنهان‌شده‌ها (${fa(hidden.length)})", style: TextStyle(color: p.mid, fontSize: 13)),
              children: [
                for (final a in hidden)
                  Row(
                    children: [
                      Expanded(child: Text(a.name, style: TextStyle(color: p.mid))),
                      TextButton(onPressed: _busy ? null : () => _run(() => _save(a, active: true)), child: const Text("نمایش")),
                    ],
                  ),
              ],
            ),
          const SizedBox(height: 8),
          LabeledField(label: "دسته‌ی تازه", controller: _name, hint: widget.kind == "expense" ? "مثلاً «نوشیدنی بوفه»" : "مثلاً «اسپانسر»", maxLength: 120, onSubmitted: (_) => _add()),
          FilledButton(onPressed: _busy ? null : _add, child: const Text("افزودن")),
        ],
      ),
    );
  }
}
