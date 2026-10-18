import "package:flutter/material.dart";
import "package:get/get.dart";

import "package:davos_admin/core/services/api_service/api_service.dart";
import "package:davos_admin/core/theme/app_colors.dart";
import "package:davos_admin/core/theme/pit.dart";
import "package:davos_admin/core/utils/fa.dart";
import "package:davos_admin/core/utils/jalali.dart";
import "package:davos_admin/features/accounting/controller/accounting_data_controller.dart";
import "package:davos_admin/features/accounting/model/accounting_models.dart";
import "package:davos_admin/shared/dialog/dialogs.dart";
import "package:davos_admin/shared/widgets/app_button.dart";
import "package:davos_admin/shared/widgets/form_fields.dart";
import "package:davos_admin/shared/widgets/info_widgets.dart";
import "package:davos_admin/shared/widgets/pressable.dart";
import "package:davos_admin/shared/widgets/state_view.dart";

const _kinds = {"expense": "هزینه", "income": "درآمد", "owner": "شخصی"};

/// Records money in plain words: an expense, an income that is not a ticket, cash taken to the bank (or back), the owner's
/// own money, or a refund handed back to a customer. Amount, category, till or bank, done; the date defaults to today.
///
/// Arguments: the kind ("expense", "income", "owner", "refund"), or `{"kind": .., "amountToman": .., "owedIrr": ..}`.
class EntryPage extends StatefulWidget {
  const EntryPage({super.key});

  @override
  State<EntryPage> createState() => _EntryPageState();
}

class _EntryPageState extends State<EntryPage> {
  final data = Get.find<AccountingDataController>();
  final _amount = TextEditingController();
  final _description = TextEditingController();
  late String _kind;
  int _owedIrr = 0;
  String? _category;
  late Wallet _wallet;
  bool _ownerDraw = true;
  String _day = businessDayIso();
  bool _busy = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    final args = Get.arguments;
    final map = args is Map ? args : const {};
    _kind = (args is String ? args : map["kind"] as String?) ?? "expense";
    if (!_kinds.containsKey(_kind) && _kind != "refund") _kind = "expense";
    final amount = map["amountToman"];
    if (amount is int && amount > 0) _amount.text = grouped(amount);
    _owedIrr = map["owedIrr"] is int ? map["owedIrr"] as int : 0;
    _wallet = _kind == "expense" || _kind == "income" ? Wallet.cash : Wallet.bank;
  }

  @override
  void dispose() {
    _amount.dispose();
    _description.dispose();
    super.dispose();
  }

  bool get _needsCategory => _kind == "expense" || _kind == "income";

  /// A category that is not in the list: typed here, saved for good (it also shows in the categories page).
  Future<void> _addCategory() async {
    final controller = TextEditingController();
    final ok = await showFormSheet<bool>(
      context,
      title: _kind == "expense" ? "بابت تازه" : "محل درآمد تازه",
      builder: (sheet) => Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          LabeledField(label: "نام", controller: controller, autofocus: true, maxLength: 120),
          AppButton(label: "افزودن", onPressed: () => Navigator.of(sheet).pop(true)),
        ],
      ),
    );
    final name = controller.text.trim();
    controller.dispose();
    if (ok != true || name.isEmpty) return;
    final kind = _kind == "expense" ? "expense" : "revenue";
    try {
      await ApiService().saveAccount(code: data.nextCode(kind), name: name, type: kind, parentId: data.parentFor(kind)?.id, active: true);
      await data.reload();
      final created = data.categories(kind).where((a) => a.name == name).firstOrNull;
      if (created != null && mounted) setState(() => _category = created.id);
    } catch (e) {
      toast(errorMessage(e), error: true);
    }
  }

  Future<void> _submit() async {
    final amount = moneyValue(_amount);
    final till = data.wallet(Wallet.cash);
    final bank = data.wallet(Wallet.bank);
    final chosen = data.wallet(_wallet);
    if (amount <= 0) return setState(() => _error = "مبلغ را بنویسید.");
    if (_needsCategory && _category == null) return setState(() => _error = "بابت چه بوده؟ یک دسته انتخاب کنید.");
    if (till == null || bank == null || chosen == null) return setState(() => _error = "حساب صندوق یا بانک پیدا نشد.");
    setState(() {
      _busy = true;
      _error = null;
    });
    final api = ApiService();
    final note = _description.text.trim();
    try {
      switch (_kind) {
        case "expense":
          await api.recordExpense(date: _day, amountToman: amount, description: note, expenseAccountId: _category!, paidFromAccountId: chosen.id);
        case "income":
          await api.recordIncome(date: _day, amountToman: amount, description: note, revenueAccountId: _category!, depositAccountId: chosen.id);
        case "owner":
          // the owner's own money: not an expense or income of the business, so profit does not change
          final capital = data.capital;
          if (capital == null) throw StateError("حساب سرمایه پیدا نشد.");
          await api.postJournalEntry(
            date: _day,
            description: note.isNotEmpty ? note : (_ownerDraw ? "برداشت شخصی مالک" : "آورده‌ی مالک"),
            debitAccountId: _ownerDraw ? capital.id : chosen.id,
            creditAccountId: _ownerDraw ? chosen.id : capital.id,
            amountToman: amount,
          );
        default:
          await api.payRefund(date: _day, amountToman: amount, description: note, fromAccountId: chosen.id);
      }
      toast("${tomanText(amount)} ثبت شد.");
      Get.back(result: true);
    } on StateError catch (e) {
      setState(() => _error = e.message);
    } catch (e) {
      setState(() => _error = errorMessage(e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(_kind == "refund" ? "پرداخت استرداد به مشتری" : "ثبت دخل و خرج")),
      body: Obx(() {
        if (data.loading.value && data.accounts.isEmpty) return StateView.loading();
        if (data.error.value != null && data.accounts.isEmpty) return StateView.error(data.error.value!, onRetry: data.reload);
        final options = _needsCategory ? data.categories(_kind == "expense" ? "expense" : "revenue") : const <Account>[];
        return ListView(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 32),
          children: [
            if (_kind != "refund") ...[
              PillSelector<String>(
                options: _kinds,
                value: _kind,
                onChanged: (kind) => setState(() {
                  _kind = kind;
                  _category = null;
                  _error = null;
                }),
              ),
              const SizedBox(height: 16),
            ],
            LabeledField(label: "مبلغ", controller: _amount, money: true, big: true, suffix: "تومان", autofocus: _amount.text.isEmpty),
            if (_kind == "refund" && _owedIrr > 0)
              Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Text("مانده‌ی استرداد پرداخت‌نشده: ${tomanFromIrr(_owedIrr)} تومان", style: TextStyle(color: context.pit.mid, fontSize: 12.5)),
              ),
            if (_needsCategory)
              FieldShell(
                label: _kind == "expense" ? "بابت" : "از محل",
                child: options.isEmpty
                    ? const Text("هنوز دسته‌ای ندارید؛ از بخش «دسته‌ها» یکی اضافه کنید.")
                    : const SizedBox.shrink(),
              ),
            if (_needsCategory)
              Padding(
                padding: const EdgeInsets.only(bottom: 14),
                child: Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    for (final a in options) _Chip(a.name, selected: a.id == _category, onTap: () => setState(() => _category = a.id)),
                    _Chip("+ جدید", selected: false, onTap: _addCategory),
                  ],
                ),
              ),
            if (_kind == "owner") ...[
              FieldShell(
                label: "کدام",
                child: PillSelector<bool>(
                  options: const {true: "برداشت برای خودم", false: "آورده به مجموعه"},
                  value: _ownerDraw,
                  onChanged: (v) => setState(() => _ownerDraw = v),
                ),
              ),
              Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Text("پول شخصی مالک؛ هزینه یا درآمد مجموعه حساب نمی‌شود و سود را تغییر نمی‌دهد.", style: TextStyle(color: context.pit.mid, fontSize: 12, height: 1.7)),
              ),
            ],
            FieldShell(
              label: _kind == "income" || (_kind == "owner" && !_ownerDraw) ? "واریز به" : "پرداخت از",
              child: PillSelector<Wallet>(
                options: walletLabels,
                value: _wallet,
                onChanged: (w) => setState(() => _wallet = w),
              ),
            ),
            DateField(label: "تاریخ", value: _day, onChanged: (v) => setState(() => _day = v ?? _day)),
            LabeledField(label: "توضیح (اختیاری)", controller: _description, hint: _kind == "expense" ? "مثلاً تعویض لنت کارت ۴" : null),
            if (_error != null) MessageBar(_error!, error: true),
            AppButton(label: "ثبت", onPressed: _submit, busy: _busy),
          ],
        );
      }),
    );
  }
}

class _Chip extends StatelessWidget {
  const _Chip(this.label, {required this.selected, required this.onTap});

  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    return Pressable(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 160),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 9),
        decoration: BoxDecoration(
          color: selected ? AppColors.accent : p.surface,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: selected ? AppColors.accent : p.line),
        ),
        child: Text(label, style: TextStyle(color: selected ? AppColors.ink : p.hi, fontWeight: selected ? FontWeight.w700 : FontWeight.w500, fontSize: 13)),
      ),
    );
  }
}
