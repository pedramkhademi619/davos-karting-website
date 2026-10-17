import "package:flutter/material.dart";
import "package:get/get.dart";

import "package:davos_admin/core/theme/app_colors.dart";
import "package:davos_admin/core/utils/fa.dart";
import "package:davos_admin/core/utils/jalali.dart";
import "package:davos_admin/features/accounting/controller/reports_controller.dart";
import "package:davos_admin/features/accounting/model/accounting_models.dart";
import "package:davos_admin/features/accounting/widgets/accounting_fields.dart";
import "package:davos_admin/shared/widgets/app_card.dart";
import "package:davos_admin/shared/widgets/form_fields.dart";
import "package:davos_admin/shared/widgets/info_widgets.dart";
import "package:davos_admin/shared/widgets/state_view.dart";

/// Every accounting report. Amounts are shown in Toman.
class ReportsPage extends GetView<ReportsController> {
  const ReportsPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("گزارش‌های مالی")),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 12, 12, 0),
            child: Obx(
              () => PillSelector<ReportKind>(
                options: {for (final k in ReportKind.values) k: k.label},
                value: controller.kind.value,
                onChanged: controller.choose,
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 12, 12, 0),
            child: Obx(() {
              final single = controller.kind.value == ReportKind.balanceSheet || controller.kind.value == ReportKind.cashPosition;
              return Row(
                children: [
                  if (!single) ...[
                    Expanded(child: DateField(label: "از", value: controller.from.value, onChanged: (v) => controller.setRange(start: v))),
                    const SizedBox(width: 10),
                  ],
                  Expanded(child: DateField(label: single ? "تا تاریخ" : "تا", value: controller.to.value, onChanged: (v) => controller.setRange(end: v))),
                ],
              );
            }),
          ),
          Obx(
            () => controller.kind.value == ReportKind.ledger
                ? Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 12),
                    child: AccountField(label: "حساب", value: controller.ledgerAccount.value, where: (a) => true, onChanged: controller.setLedgerAccount),
                  )
                : const SizedBox.shrink(),
          ),
          Expanded(
            child: Obx(() {
              if (controller.loading.value) return StateView.loading();
              if (controller.error.value != null) return StateView.error(controller.error.value!, onRetry: controller.reload);
              final r = controller.result.value;
              if (r == null) {
                return StateView.empty(controller.kind.value == ReportKind.ledger ? "حساب را انتخاب کنید." : "اطلاعاتی نیست.");
              }
              return ListView(padding: const EdgeInsets.fromLTRB(12, 0, 12, 24), children: _body(context, r));
            }),
          ),
        ],
      ),
    );
  }

  List<Widget> _body(BuildContext context, Object r) {
    if (r is IncomeStatement) return _income(r);
    if (r is BalanceSheet) return _balance(r);
    if (r is TrialBalance) return _trial(r);
    if (r is SalesReport) return _sales(r);
    if (r is VatReport) return _vat(r);
    if (r is Ledger) return _ledger(r);
    if (r is List<StatementLine>) return _cash(r);
    return const [];
  }

  Widget _lines(String title, List<StatementLine> lines, int total) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      SectionTitle(title),
      AppCard(
        child: Column(
          children: [
            for (final l in lines) InfoRow("${l.code.isEmpty ? "" : "${fa(l.code)}  "}${l.name}", tomanFromIrr(l.amountIrr)),
            if (lines.isEmpty) const Text("—"),
            const Divider(),
            InfoRow("جمع", tomanFromIrr(total), bold: true),
          ],
        ),
      ),
    ],
  );

  List<Widget> _income(IncomeStatement r) {
    final c = r.current;
    return [
      _lines("درآمدها", c.revenue, c.totalRevenueIrr),
      _lines("هزینه‌ها", c.expenses, c.totalExpensesIrr),
      const SectionTitle("نتیجه"),
      AppCard(
        child: Column(
          children: [
            InfoRow("سود (زیان) خالص", tomanFromIrr(c.netProfitIrr), bold: true, valueColor: c.netProfitIrr >= 0 ? AppColors.success : AppColors.danger),
            InfoRow("دورهٔ قبل (${jalaliText(r.previous.from)} تا ${jalaliText(r.previous.to)})", tomanFromIrr(r.previous.netProfitIrr)),
          ],
        ),
      ),
    ];
  }

  List<Widget> _balance(BalanceSheet r) => [
    _lines("دارایی‌ها", r.assets, r.totalAssetsIrr),
    _lines("بدهی‌ها", r.liabilities, r.totalLiabilitiesIrr),
    _lines("حقوق صاحبان سرمایه", r.equity, r.totalEquityIrr),
    const SectionTitle("خلاصه"),
    AppCard(
      child: Column(
        children: [
          InfoRow("سود جاری", tomanFromIrr(r.currentEarningsIrr)),
          InfoRow(
            "اختلاف ترازنامه",
            r.differenceIrr == 0 ? "تراز است" : tomanFromIrr(r.differenceIrr),
            bold: true,
            valueColor: r.differenceIrr == 0 ? AppColors.success : AppColors.danger,
          ),
        ],
      ),
    ),
  ];

  List<Widget> _trial(TrialBalance r) => [
    const SectionTitle("گردش و مانده حساب‌ها"),
    for (final row in r.rows)
      Padding(
        padding: const EdgeInsets.only(bottom: 6),
        child: AppCard(
          padding: const EdgeInsets.all(10),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text("${fa(row.code)}  ${row.name}", style: const TextStyle(fontWeight: FontWeight.w700)),
              InfoRow("گردش بدهکار / بستانکار", "${tomanFromIrr(row.debitIrr)} / ${tomanFromIrr(row.creditIrr)}"),
              InfoRow("مانده بدهکار / بستانکار", "${tomanFromIrr(row.closingDebitIrr)} / ${tomanFromIrr(row.closingCreditIrr)}"),
            ],
          ),
        ),
      ),
    const SectionTitle("جمع"),
    AppCard(
      child: Column(
        children: [
          InfoRow("جمع گردش بدهکار", tomanFromIrr(r.totalDebitIrr)),
          InfoRow("جمع گردش بستانکار", tomanFromIrr(r.totalCreditIrr)),
          InfoRow("جمع مانده بدهکار", tomanFromIrr(r.totalClosingDebitIrr)),
          InfoRow("جمع مانده بستانکار", tomanFromIrr(r.totalClosingCreditIrr)),
        ],
      ),
    ),
  ];

  List<Widget> _sales(SalesReport r) => [
    const SectionTitle("جمع دوره"),
    AppCard(
      child: Column(
        children: [
          InfoRow("آنلاین", tomanFromIrr(r.onlineIrr)),
          InfoRow("نقدی", tomanFromIrr(r.cashIrr)),
          InfoRow("کارتخوان", tomanFromIrr(r.cardIrr)),
          InfoRow("کارت‌به‌کارت", tomanFromIrr(r.transferIrr)),
          const Divider(),
          InfoRow("دریافتی", tomanFromIrr(r.receivedIrr), bold: true),
          InfoRow("درآمد شناسایی‌شده", tomanFromIrr(r.revenueIrr), bold: true),
        ],
      ),
    ),
    const SectionTitle("روز به روز"),
    for (final d in r.days)
      Padding(
        padding: const EdgeInsets.only(bottom: 6),
        child: AppCard(
          padding: const EdgeInsets.all(10),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(jalaliWithWeekday(d.date), style: const TextStyle(fontWeight: FontWeight.w700)),
              InfoRow("دریافتی", tomanFromIrr(d.receivedIrr)),
              InfoRow("درآمد", tomanFromIrr(d.revenueIrr)),
            ],
          ),
        ),
      ),
  ];

  List<Widget> _vat(VatReport r) => [
    const SectionTitle("مالیات بر ارزش افزوده"),
    AppCard(
      child: Column(
        children: [
          InfoRow("مانده ابتدای دوره", tomanFromIrr(r.openingBalanceIrr)),
          InfoRow("دریافت‌شده از مشتریان", tomanFromIrr(r.collectedIrr)),
          InfoRow("پرداخت‌شده روی خریدها", tomanFromIrr(r.paidIrr)),
          const Divider(),
          InfoRow("قابل پرداخت", tomanFromIrr(r.netPayableIrr), bold: true, valueColor: r.netPayableIrr > 0 ? AppColors.danger : AppColors.success),
        ],
      ),
    ),
  ];

  List<Widget> _ledger(Ledger r) => [
    SectionTitle("${fa(r.account.code)}  ${r.account.name}"),
    AppCard(
      child: Column(
        children: [InfoRow("مانده ابتدای دوره", tomanFromIrr(r.openingIrr)), InfoRow("مانده پایان دوره", tomanFromIrr(r.closingIrr), bold: true)],
      ),
    ),
    const SizedBox(height: 8),
    for (final l in r.lines)
      Padding(
        padding: const EdgeInsets.only(bottom: 6),
        child: AppCard(
          padding: const EdgeInsets.all(10),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text("سند ${fa(l.number)} • ${jalaliText(l.date)}", style: const TextStyle(fontWeight: FontWeight.w700)),
              Text(l.description, style: const TextStyle(height: 1.6, fontSize: 13)),
              InfoRow(l.debitIrr > 0 ? "بدهکار" : "بستانکار", tomanFromIrr(l.debitIrr > 0 ? l.debitIrr : l.creditIrr)),
              InfoRow("مانده", tomanFromIrr(l.balanceIrr), bold: true),
            ],
          ),
        ),
      ),
  ];

  List<Widget> _cash(List<StatementLine> lines) => [
    const SectionTitle("موجودی حساب‌های نقد"),
    AppCard(
      child: Column(
        children: [
          for (final l in lines) InfoRow(l.name, tomanFromIrr(l.amountIrr), bold: l.group == "total"),
          if (lines.isEmpty) const Text("—"),
        ],
      ),
    ),
  ];
}
