import "package:flutter/material.dart";
import "package:shamsi_date/shamsi_date.dart";
import "package:get/get.dart";

import "package:davos_admin/core/utils/fa.dart";
import "package:davos_admin/core/utils/jalali.dart";
import "package:davos_admin/features/accounting/controller/accounting_settings_controller.dart";
import "package:davos_admin/features/accounting/model/accounting_models.dart";
import "package:davos_admin/shared/dialog/dialogs.dart";
import "package:davos_admin/shared/widgets/app_button.dart";
import "package:davos_admin/shared/widgets/app_card.dart";
import "package:davos_admin/shared/widgets/form_fields.dart";
import "package:davos_admin/shared/widgets/info_widgets.dart";
import "package:davos_admin/shared/widgets/state_view.dart";

class AccountingSettingsPage extends GetView<AccountingSettingsController> {
  const AccountingSettingsPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("تنظیمات حسابداری")),
      body: Obx(() {
        final s = controller.settings.value;
        final state = StateView.from(
          loading: controller.loading.value,
          isEmpty: s == null,
          error: controller.error.value,
          emptyMessage: "تنظیماتی نیست.",
          onRetry: controller.reload,
        );
        if (state != null) return state;
        return _Form(controller: controller, initial: s!);
      }),
    );
  }
}

class _Form extends StatefulWidget {
  const _Form({required this.controller, required this.initial});

  final AccountingSettingsController controller;
  final AccountingSettings initial;

  @override
  State<_Form> createState() => _FormState();
}

class _FormState extends State<_Form> {
  late AccountingSettings s = AccountingSettings.fromJson(widget.initial.toJson());
  late final _vat = TextEditingController(text: decimal(s.vatPercent));
  late final _fee = TextEditingController(text: decimal(s.gatewayFeePercent));
  final _year = TextEditingController(text: fa(currentJalaliYear() - 1));
  String _syncFrom = isoOfJalali(Jalali(currentJalaliYear(), 1, 1));
  String _syncTo = todayIso();
  bool _busy = false;
  bool _syncing = false;
  String? _message;
  bool _isError = false;
  String? _syncMessage;
  bool _syncError = false;

  @override
  void dispose() {
    _vat.dispose();
    _fee.dispose();
    _year.dispose();
    super.dispose();
  }

  double _percent(String text) => double.tryParse(latin(text).replaceAll("٫", ".")) ?? 0;

  Future<void> _save() async {
    s
      ..vatPercent = _percent(_vat.text)
      ..gatewayFeePercent = _percent(_fee.text);
    setState(() {
      _busy = true;
      _message = null;
    });
    final m = await widget.controller.save(s);
    if (!mounted) return;
    setState(() {
      _busy = false;
      _isError = m != null;
      _message = m ?? "ذخیره شد.";
    });
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        AppCard(
          child: Column(
            children: [
              SwitchRow(
                title: "ثبت خودکار فروش در دفتر",
                subtitle: "هر رزرو قطعی یا لغوشده خودش سند می‌خورد.",
                value: s.autoPostingEnabled,
                onChanged: (v) => setState(() => s.autoPostingEnabled = v),
              ),
              LabeledField(label: "نرخ مالیات بر ارزش افزوده", controller: _vat, suffix: "درصد", number: true),
              LabeledField(label: "کارمزد درگاه پرداخت", controller: _fee, suffix: "درصد", number: true),
              ChoiceField<String>(
                label: "زمان شناسایی درآمد",
                value: s.revenueRecognition,
                options: const {"on_payment": "هنگام پرداخت", "on_session": "هنگام برگزاری سانس"},
                onChanged: (v) => setState(() => s.revenueRecognition = v ?? s.revenueRecognition),
              ),
              DateField(
                label: "قفل دفتر تا تاریخ",
                value: s.lockedThrough,
                clearable: true,
                onChanged: (v) => setState(() => s.lockedThrough = v),
              ),
              const Text("روی تاریخ‌های قفل‌شده سند جدید ثبت نمی‌شود.", style: TextStyle(fontSize: 12)),
              const SizedBox(height: 12),
              if (_message != null) MessageBar(_message!, error: _isError),
              AppButton(label: "ذخیره", onPressed: _save, busy: _busy),
            ],
          ),
        ),
        const SectionTitle("ثبت رزروهای قدیمی"),
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text("رزروهایی را که هنوز سند فروش ندارند در دفتر ثبت می‌کند و درآمد سررسیدشده را می‌شناسد.", style: TextStyle(height: 1.7)),
              const SizedBox(height: 10),
              DateField(label: "از", value: _syncFrom, onChanged: (v) => setState(() => _syncFrom = v ?? _syncFrom)),
              DateField(label: "تا", value: _syncTo, onChanged: (v) => setState(() => _syncTo = v ?? _syncTo)),
              if (_syncMessage != null) MessageBar(_syncMessage!, error: _syncError),
              AppButton(
                label: "ثبت رزروهای ثبت‌نشده",
                outlined: true,
                busy: _syncing,
                onPressed: () async {
                  setState(() {
                    _syncing = true;
                    _syncMessage = null;
                  });
                  final r = await widget.controller.sync(_syncFrom, _syncTo);
                  if (!mounted) return;
                  setState(() {
                    _syncing = false;
                    _syncMessage = r.$1;
                    _syncError = r.$2;
                  });
                },
              ),
            ],
          ),
        ),
        const SectionTitle("بستن سال مالی"),
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                "با بستن سال، سند بستن ثبت می‌شود، سود یا زیان به حقوق صاحبان سرمایه منتقل می‌شود و دفتر آن سال قفل می‌شود. این کار برگشت‌پذیر نیست.",
                style: TextStyle(height: 1.7),
              ),
              const SizedBox(height: 10),
              LabeledField(label: "سال شمسی", controller: _year, number: true),
              AppButton(
                label: "بستن سال مالی",
                danger: true,
                outlined: true,
                onPressed: () async {
                  final year = parseInt(_year.text);
                  if (!await confirm(context, title: "بستن سال ${fa(year)}", message: "مطمئن هستید؟ بعد از بستن، در این سال سند جدید ثبت نمی‌شود.", danger: true, confirmLabel: "بستن سال")) return;
                  final m = await widget.controller.closeYear(year);
                  toast(m ?? "سال ${fa(year)} بسته شد.", error: m != null);
                },
              ),
            ],
          ),
        ),
      ],
    );
  }
}
