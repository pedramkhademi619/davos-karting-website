import "package:flutter/material.dart";
import "package:get/get.dart";

import "package:davos_admin/core/services/api_service/api_service.dart";
import "package:davos_admin/core/utils/fa.dart";
import "package:davos_admin/core/utils/jalali.dart";
import "package:davos_admin/features/accounting/controller/accounting_data_controller.dart";
import "package:davos_admin/features/accounting/widgets/accounting_fields.dart";
import "package:davos_admin/shared/widgets/app_button.dart";
import "package:davos_admin/shared/widgets/form_fields.dart";
import "package:davos_admin/shared/widgets/info_widgets.dart";
import "package:davos_admin/shared/widgets/state_view.dart";

/// The everyday entries without knowing debit and credit: an expense, extra income, a transfer between money accounts and
/// a payment to a supplier or back to a customer.
class QuickEntryPage extends StatefulWidget {
  const QuickEntryPage({super.key});

  @override
  State<QuickEntryPage> createState() => _QuickEntryPageState();
}

class _QuickEntryPageState extends State<QuickEntryPage> {
  final data = Get.find<AccountingDataController>();
  late String _kind = (Get.arguments is String && _kinds.containsKey(Get.arguments)) ? Get.arguments as String : "expense";
  String _day = businessDayIso();
  final _amount = TextEditingController();
  final _vat = TextEditingController();
  final _description = TextEditingController();
  String? _main;
  String? _from;
  String? _to;
  String? _vendor;
  bool _busy = false;
  String? _message;
  bool _isError = false;

  static const _kinds = {
    "expense": "هزینه",
    "income": "درآمد دیگر",
    "transfer": "انتقال",
    "vendor": "پرداخت به تامین‌کننده",
    "refund": "استرداد به مشتری",
  };

  @override
  void dispose() {
    _amount.dispose();
    _vat.dispose();
    _description.dispose();
    super.dispose();
  }

  void _setKind(String kind) => setState(() {
    _kind = kind;
    _main = _from = _to = _vendor = null;
    _message = null;
  });

  Future<void> _submit() async {
    final api = ApiService();
    final amount = moneyValue(_amount);
    setState(() {
      _busy = true;
      _message = null;
    });
    try {
      final entry = switch (_kind) {
        "expense" => await api.recordExpense(
          date: _day,
          amountToman: amount,
          description: _description.text.trim(),
          expenseAccountId: _main ?? "",
          vatToman: moneyValue(_vat),
          paidFromAccountId: _from,
          vendorId: _vendor,
        ),
        "income" => await api.recordIncome(
          date: _day,
          amountToman: amount,
          description: _description.text.trim(),
          revenueAccountId: _main ?? "",
          vatToman: moneyValue(_vat),
          depositAccountId: _to ?? "",
        ),
        "transfer" => await api.recordTransfer(
          date: _day,
          amountToman: amount,
          description: _description.text.trim(),
          fromAccountId: _from ?? "",
          toAccountId: _to ?? "",
        ),
        _ => await api.recordPayment(
          date: _day,
          amountToman: amount,
          description: _description.text.trim(),
          fromAccountId: _from ?? "",
          vendorId: _kind == "vendor" ? _vendor : null,
        ),
      };
      setState(() {
        _message = "ثبت شد؛ سند شمارهٔ ${fa(entry.number)} (سال ${fa(entry.fiscalYear)}).";
        _isError = false;
        _amount.clear();
        _vat.clear();
        _description.clear();
      });
    } catch (e) {
      setState(() {
        _message = errorMessage(e);
        _isError = true;
      });
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("ثبت سریع")),
      body: Obx(() {
        if (data.loading.value && data.accounts.isEmpty) return StateView.loading();
        if (data.error.value != null && data.accounts.isEmpty) return StateView.error(data.error.value!, onRetry: data.reload);
        return ListView(
          padding: const EdgeInsets.all(16),
          children: [
            PillSelector<String>(options: _kinds, value: _kind, onChanged: _setKind),
            const SizedBox(height: 14),
            DateField(label: "تاریخ", value: _day, onChanged: (v) => setState(() => _day = v ?? _day)),
            LabeledField(label: "مبلغ (تومان)", controller: _amount, money: true),
            ..._fields(),
            LabeledField(label: "شرح", controller: _description, lines: 2),
            if (_message != null) MessageBar(_message!, error: _isError),
            AppButton(label: "ثبت", onPressed: _submit, busy: _busy),
          ],
        );
      }),
    );
  }

  List<Widget> _fields() {
    switch (_kind) {
      case "expense":
        return [
          AccountField(label: "نوع هزینه", value: _main, type: "expense", onChanged: (v) => setState(() => _main = v)),
          LabeledField(label: "مالیات بر ارزش افزوده‌ی همین فاکتور (تومان)", controller: _vat, money: true),
          AccountField(label: "پرداخت از", value: _from, where: (a) => a.holdsMoney, optional: true, onChanged: (v) => setState(() => _from = v)),
          VendorField(value: _vendor, onChanged: (v) => setState(() => _vendor = v)),
          const Padding(
            padding: EdgeInsets.only(bottom: 12),
            child: Text("اگر «پرداخت از» را خالی بگذارید و تامین‌کننده انتخاب کنید، هزینه نسیه ثبت می‌شود.", style: TextStyle(fontSize: 12, height: 1.7)),
          ),
        ];
      case "income":
        return [
          AccountField(label: "نوع درآمد", value: _main, type: "revenue", onChanged: (v) => setState(() => _main = v)),
          LabeledField(label: "مالیات بر ارزش افزوده (تومان)", controller: _vat, money: true),
          AccountField(label: "واریز به", value: _to, where: (a) => a.holdsMoney, onChanged: (v) => setState(() => _to = v)),
        ];
      case "transfer":
        return [
          AccountField(label: "از", value: _from, where: (a) => a.holdsMoney, onChanged: (v) => setState(() => _from = v)),
          AccountField(label: "به", value: _to, where: (a) => a.holdsMoney, onChanged: (v) => setState(() => _to = v)),
        ];
      case "vendor":
        return [
          VendorField(value: _vendor, optional: false, onChanged: (v) => setState(() => _vendor = v)),
          AccountField(label: "پرداخت از", value: _from, where: (a) => a.holdsMoney, onChanged: (v) => setState(() => _from = v)),
        ];
      default:
        return [AccountField(label: "پرداخت از", value: _from, where: (a) => a.holdsMoney, onChanged: (v) => setState(() => _from = v))];
    }
  }
}
