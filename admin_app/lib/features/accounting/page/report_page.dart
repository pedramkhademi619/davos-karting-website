import "package:flutter/material.dart";
import "package:get/get.dart";

import "package:davos_admin/core/theme/app_colors.dart";
import "package:davos_admin/core/theme/pit.dart";
import "package:davos_admin/core/utils/fa.dart";
import "package:davos_admin/features/accounting/controller/report_controller.dart";
import "package:davos_admin/features/accounting/model/accounting_models.dart";
import "package:davos_admin/features/accounting/page/day_book_page.dart";
import "package:davos_admin/shared/widgets/app_card.dart";
import "package:davos_admin/shared/widgets/state_view.dart";

/// One month's profit and loss in categories, compared with the month before, and where ticket money came from.
class ReportPage extends GetView<ReportController> {
  const ReportPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("گزارش ماهانه")),
      body: Column(
        children: [
          Obx(() => MonthStepper(month: controller.month.value, onStep: controller.step)),
          Expanded(
            child: Obx(() {
              final s = controller.statement.value;
              final sales = controller.sales.value;
              if (controller.error.value != null) return StateView.error(controller.error.value!, onRetry: controller.reload);
              if (s == null || sales == null) return StateView.loading();
              final now = s.current;
              return RefreshIndicator(
                onRefresh: controller.reload,
                child: ListView(
                  padding: const EdgeInsets.fromLTRB(16, 4, 16, 40),
                  children: [
                    _Profit(now: now, before: s.previous),
                    if (sales.receivedIrr > 0) ...[const SizedBox(height: 14), _Channels(sales: sales)],
                    const SizedBox(height: 14),
                    _Lines(title: "درآمدها", lines: now.revenue, totalIrr: now.totalRevenueIrr, color: AppColors.success),
                    const SizedBox(height: 14),
                    _Lines(title: "هزینه‌ها", lines: now.expenses, totalIrr: now.totalExpensesIrr, color: AppColors.danger),
                  ],
                ),
              );
            }),
          ),
        ],
      ),
    );
  }
}

/// "+۱۲٪ نسبت به ماه قبل"; nothing when there is no previous month to compare with.
String? _change(int now, int before) {
  if (before == 0) return null;
  final percent = ((now - before) / before.abs() * 100).round();
  return "${percent > 0 ? "+" : percent < 0 ? "−" : ""}${fa(percent.abs())}٪ نسبت به ماه قبل";
}

class _Profit extends StatelessWidget {
  const _Profit({required this.now, required this.before});

  final IncomeStatementPeriod now;
  final IncomeStatementPeriod before;

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    Widget figure(String label, int irr, int beforeIrr, {Color? color}) => Expanded(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: TextStyle(color: p.mid, fontSize: 12.5)),
          const SizedBox(height: 4),
          FittedBox(
            fit: BoxFit.scaleDown,
            alignment: AlignmentDirectional.centerStart,
            child: Text(tomanFromIrr(irr), style: TextStyle(fontWeight: FontWeight.w700, fontSize: 17, color: color)),
          ),
          if (_change(irr, beforeIrr) case final text?) Text(text, style: TextStyle(color: p.low, fontSize: 11)),
        ],
      ),
    );
    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text("سود (زیان)", style: TextStyle(color: p.mid)),
          const SizedBox(height: 4),
          Text(
            "${tomanFromIrr(now.netProfitIrr)} تومان",
            style: TextStyle(fontSize: 26, fontWeight: FontWeight.w700, color: now.netProfitIrr < 0 ? AppColors.danger : null),
          ),
          if (_change(now.netProfitIrr, before.netProfitIrr) case final text?) Text(text, style: TextStyle(color: p.low, fontSize: 12)),
          const Divider(height: 26),
          Row(
            children: [
              figure("درآمد", now.totalRevenueIrr, before.totalRevenueIrr),
              const SizedBox(width: 12),
              figure("هزینه", now.totalExpensesIrr, before.totalExpensesIrr),
            ],
          ),
        ],
      ),
    );
  }
}

class _Channels extends StatelessWidget {
  const _Channels({required this.sales});

  final SalesReport sales;

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    Widget channel(String label, int irr) => Expanded(
      child: Container(
        padding: const EdgeInsets.all(10),
        decoration: BoxDecoration(color: p.sunken, borderRadius: BorderRadius.circular(14)),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(label, style: TextStyle(color: p.mid, fontSize: 11.5)),
            FittedBox(fit: BoxFit.scaleDown, child: Text(tomanFromIrr(irr), style: const TextStyle(fontWeight: FontWeight.w700))),
            Text("${fa((irr / sales.receivedIrr * 100).round())}٪", style: TextStyle(color: p.low, fontSize: 11)),
          ],
        ),
      ),
    );
    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text("فروش بلیت از کجا آمد", style: TextStyle(fontWeight: FontWeight.w700)),
          const SizedBox(height: 10),
          Row(
            children: [
              channel("آنلاین", sales.onlineIrr),
              const SizedBox(width: 8),
              channel("حضوری، نقد", sales.cashIrr),
              const SizedBox(width: 8),
              channel("حضوری، کارت", sales.cardIrr),
            ],
          ),
        ],
      ),
    );
  }
}

class _Lines extends StatelessWidget {
  const _Lines({required this.title, required this.lines, required this.totalIrr, required this.color});

  final String title;
  final List<StatementLine> lines;
  final int totalIrr;
  final Color color;

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    final shown = lines.where((l) => l.amountIrr != 0).toList()..sort((a, b) => b.amountIrr.compareTo(a.amountIrr));
    final peak = shown.fold<int>(1, (m, l) => l.amountIrr.abs() > m ? l.amountIrr.abs() : m);
    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: const TextStyle(fontWeight: FontWeight.w700)),
          const SizedBox(height: 10),
          if (shown.isEmpty) Text("چیزی ثبت نشده است.", style: TextStyle(color: p.mid)),
          for (final line in shown)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 6),
              child: Column(
                children: [
                  Row(
                    children: [
                      Expanded(child: Text(line.name, style: const TextStyle(fontSize: 13.5))),
                      Text(tomanFromIrr(line.amountIrr), style: TextStyle(color: line.amountIrr < 0 ? AppColors.danger : p.mid, fontSize: 13)),
                    ],
                  ),
                  const SizedBox(height: 5),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(5),
                    child: LinearProgressIndicator(value: line.amountIrr.abs() / peak, minHeight: 7, backgroundColor: p.sunken, color: color),
                  ),
                ],
              ),
            ),
          if (shown.isNotEmpty) ...[
            const Divider(height: 22),
            Row(children: [const Expanded(child: Text("جمع", style: TextStyle(fontWeight: FontWeight.w700))), Text(tomanFromIrr(totalIrr), style: const TextStyle(fontWeight: FontWeight.w700))]),
          ],
        ],
      ),
    );
  }
}
