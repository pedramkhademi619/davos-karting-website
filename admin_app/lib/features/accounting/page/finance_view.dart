import "package:fl_chart/fl_chart.dart";
import "package:flutter/material.dart";
import "package:get/get.dart";

import "package:davos_admin/core/constants/named_routs.dart";
import "package:davos_admin/core/theme/app_colors.dart";
import "package:davos_admin/core/theme/pit.dart";
import "package:davos_admin/core/utils/fa.dart";
import "package:davos_admin/features/accounting/controller/accounting_hub_controller.dart";
import "package:davos_admin/features/accounting/model/accounting_models.dart";
import "package:davos_admin/shared/widgets/animated_count.dart";
import "package:davos_admin/shared/widgets/app_card.dart";
import "package:davos_admin/shared/widgets/pressable.dart";
import "package:davos_admin/shared/widgets/skeleton.dart";
import "package:davos_admin/shared/widgets/state_view.dart";

const _quick = [
  ("expense", "هزینه", Icons.south_west_rounded, AppColors.danger),
  ("income", "درآمد", Icons.north_east_rounded, AppColors.success),
  ("owner", "شخصی", Icons.person_rounded, AppColors.warning),
];

const _sections = [
  (NamedRouts.accountingDayBook, "دفتر روزانه", Icons.receipt_long_rounded),
  (NamedRouts.accountingReport, "گزارش ماهانه", Icons.assessment_rounded),
  (NamedRouts.accountingCash, "صندوق", Icons.point_of_sale_rounded),
  (NamedRouts.accountingCategories, "دسته‌ها", Icons.category_rounded),
];

/// The Finance tab: money in hand, this month, the everyday entries one tap away, then every accounting section.
class FinanceView extends GetView<AccountingHubController> {
  const FinanceView({super.key});

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    return SafeArea(
      bottom: false,
      child: RefreshIndicator(
        onRefresh: controller.reload,
        child: Obx(() {
          final d = controller.dashboard.value;
          return ListView(
            padding: const EdgeInsets.only(bottom: 130),
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 14, 12, 4),
                child: Row(
                  children: [
                    const Expanded(child: Text("مالی", style: TextStyle(fontSize: 26, fontWeight: FontWeight.w700))),
                    IconButton.filledTonal(
                      onPressed: () => controller.hidden.toggle(),
                      icon: Icon(controller.hidden.value ? Icons.visibility_off_rounded : Icons.visibility_rounded),
                      tooltip: "پنهان‌سازی مبالغ",
                    ),
                  ],
                ),
              ),
              if (d == null && controller.loading.value)
                const Padding(padding: EdgeInsets.all(20), child: Column(children: [Skeleton(height: 190, radius: 28), SizedBox(height: 16), Skeleton(height: 130, radius: 22)]))
              else if (d == null)
                SizedBox(height: 380, child: StateView.error(controller.error.value ?? "اطلاعاتی نیست.", onRetry: controller.reload))
              else ...[
                Padding(padding: const EdgeInsets.fromLTRB(20, 10, 20, 0), child: _Hero(d: d, c: controller)),
                Padding(
                  padding: const EdgeInsets.fromLTRB(20, 18, 20, 0),
                  child: Row(
                    children: [
                      for (final q in _quick)
                        Expanded(
                          child: Pressable(
                            onTap: () async {
                              if (await Get.toNamed(NamedRouts.accountingEntry, arguments: q.$1) == true) controller.reload();
                            },
                            child: Column(
                              children: [
                                Container(
                                  width: 58,
                                  height: 58,
                                  decoration: BoxDecoration(color: q.$4.withValues(alpha: 0.14), borderRadius: BorderRadius.circular(20), border: Border.all(color: q.$4.withValues(alpha: 0.3))),
                                  child: Icon(q.$3, color: q.$4),
                                ),
                                const SizedBox(height: 7),
                                Text(q.$2, style: TextStyle(fontSize: 12, color: p.mid)),
                              ],
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
                Padding(padding: const EdgeInsets.fromLTRB(20, 22, 20, 0), child: _Month(d: d, c: controller)),
                if (d.trend.isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
                    child: AppCard(
                      padding: const EdgeInsets.fromLTRB(14, 16, 14, 12),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Padding(padding: EdgeInsets.symmetric(horizontal: 4), child: Text("روند درآمد و هزینه", style: TextStyle(fontWeight: FontWeight.w700))),
                          const SizedBox(height: 14),
                          SizedBox(height: 190, child: TrendChart(points: d.trend)),
                        ],
                      ),
                    ),
                  ),
                if (d.refundsPayableIrr > 0)
                  Padding(
                    padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
                    child: AppCard(
                      borderColor: AppColors.warning.withValues(alpha: 0.4),
                      child: Row(
                        children: [
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text("${controller.money(d.refundsPayableIrr)} تومان استرداد به مشتری‌ها مانده", style: const TextStyle(fontWeight: FontWeight.w700)),
                                const SizedBox(height: 4),
                                Text("وقتی پول را به حساب مشتری برگرداندید، ثبتش کنید.", style: TextStyle(color: p.mid, fontSize: 12)),
                              ],
                            ),
                          ),
                          TextButton(
                            onPressed: () async {
                              final args = {"kind": "refund", "amountToman": irrToToman(d.refundsPayableIrr), "owedIrr": d.refundsPayableIrr};
                              if (await Get.toNamed(NamedRouts.accountingEntry, arguments: args) == true) controller.reload();
                            },
                            child: const Text("ثبت پرداخت"),
                          ),
                        ],
                      ),
                    ),
                  ),
                if (d.topExpenses.isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
                    child: AppCard(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text("خرج این ماه کجا رفت", style: TextStyle(fontWeight: FontWeight.w700)),
                          const SizedBox(height: 10),
                          for (final e in d.topExpenses) _Line(e.name, controller.money(e.amountIrr), null),
                        ],
                      ),
                    ),
                  ),
              ],
              const Padding(padding: EdgeInsets.fromLTRB(20, 26, 20, 12), child: Text("بخش‌ها", style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700))),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: GridView.count(
                  crossAxisCount: 2,
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  crossAxisSpacing: 12,
                  mainAxisSpacing: 12,
                  mainAxisExtent: 72,
                  children: [
                    for (final s in _sections)
                      AppCard(
                        onTap: () => Get.toNamed(s.$1),
                        padding: const EdgeInsets.symmetric(horizontal: 14),
                        child: Row(
                          children: [
                            Icon(s.$3, color: p.accentText),
                            const SizedBox(width: 10),
                            Expanded(child: Text(s.$2, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13.5))),
                          ],
                        ),
                      ),
                  ],
                ),
              ),
            ],
          );
        }),
      ),
    );
  }
}

class _Line extends StatelessWidget {
  const _Line(this.label, this.value, this.color);

  final String label;
  final String value;
  final Color? color;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 6),
    child: Row(
      children: [
        Expanded(child: Text(label, style: TextStyle(color: context.pit.mid, fontSize: 13.5))),
        Text(value, style: TextStyle(fontWeight: FontWeight.w700, color: color)),
      ],
    ),
  );
}

class _Hero extends StatelessWidget {
  const _Hero({required this.d, required this.c});

  final AccountingDashboard d;
  final AccountingHubController c;

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    final fg = p.isDark ? p.hi : AppColors.ink;
    final soft = p.isDark ? p.mid : AppColors.ink.withValues(alpha: 0.7);
    return Container(
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(30),
        gradient: p.isDark
            ? const LinearGradient(begin: Alignment.topRight, end: Alignment.bottomLeft, colors: [Color(0xFF16223A), Color(0xFF14161B), Color(0xFF121419)])
            : const LinearGradient(begin: Alignment.topRight, end: Alignment.bottomLeft, colors: [Color(0xFF1B2744), Color(0xFF0C0D10)]),
        border: Border.all(color: p.isDark ? AppColors.info.withValues(alpha: 0.25) : Colors.transparent),
        boxShadow: const [BoxShadow(color: Color(0x26000000), blurRadius: 30, offset: Offset(0, 12))],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text("پول در دسترس", style: TextStyle(color: p.isDark ? soft : Colors.white70, fontSize: 13.5)),
          const SizedBox(height: 6),
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Obx(
                () => c.hidden.value
                    ? const Text("••••••••", style: TextStyle(fontSize: 40, fontWeight: FontWeight.w700, color: Colors.white, height: 1.2))
                    : AnimatedCount(value: irrToToman(d.liquidIrr), style: const TextStyle(fontSize: 40, fontWeight: FontWeight.w700, color: Colors.white, height: 1.2)),
              ),
              const SizedBox(width: 8),
              const Padding(padding: EdgeInsets.only(bottom: 8), child: Text("تومان", style: TextStyle(color: Colors.white70))),
            ],
          ),
          const SizedBox(height: 18),
          Obx(
            () => Row(
              children: [
                _Chip("صندوق", c.money(d.cashIrr)),
                _Chip("بانک", c.money(d.bankIrr)),
                              ],
            ),
          ),
          // keep a use of fg so the palette helper above stays meaningful in light mode too
          SizedBox(height: fg == soft ? 0 : 0),
        ],
      ),
    );
  }
}

class _Chip extends StatelessWidget {
  const _Chip(this.label, this.value);

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) => Expanded(
    child: Container(
      margin: const EdgeInsetsDirectional.only(end: 8),
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
      decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.07), borderRadius: BorderRadius.circular(14)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(color: Colors.white60, fontSize: 11), maxLines: 1, overflow: TextOverflow.ellipsis),
          const SizedBox(height: 3),
          FittedBox(fit: BoxFit.scaleDown, alignment: AlignmentDirectional.centerStart, child: Text(value, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 13.5))),
        ],
      ),
    ),
  );
}

class _Month extends StatelessWidget {
  const _Month({required this.d, required this.c});

  final AccountingDashboard d;
  final AccountingHubController c;

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    final top = d.monthRevenueIrr > d.monthExpensesIrr ? d.monthRevenueIrr : d.monthExpensesIrr;
    double share(int v) => top <= 0 ? 0 : (v / top).clamp(0, 1).toDouble();
    return AppCard(
      child: Obx(
        () => Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Expanded(child: Text("این ماه", style: TextStyle(fontWeight: FontWeight.w700, fontSize: 15))),
                Text("سود ", style: TextStyle(color: p.mid, fontSize: 13)),
                Text(c.money(d.monthProfitIrr), style: TextStyle(fontWeight: FontWeight.w700, fontSize: 17, color: d.monthProfitIrr >= 0 ? AppColors.success : AppColors.danger)),
              ],
            ),
            const SizedBox(height: 16),
            _Bar("درآمد", c.money(d.monthRevenueIrr), share(d.monthRevenueIrr), AppColors.success),
            const SizedBox(height: 12),
            _Bar("هزینه", c.money(d.monthExpensesIrr), share(d.monthExpensesIrr), AppColors.danger),
            const SizedBox(height: 12),
            Text("درآمد امروز: ${c.money(d.todayRevenueIrr)} تومان", style: TextStyle(color: p.mid, fontSize: 12.5)),
          ],
        ),
      ),
    );
  }
}

class _Bar extends StatelessWidget {
  const _Bar(this.label, this.value, this.share, this.color);

  final String label;
  final String value;
  final double share;
  final Color color;

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    return Column(
      children: [
        Row(children: [Text(label, style: TextStyle(color: p.mid, fontSize: 13)), const Spacer(), Text(value, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14))]),
        const SizedBox(height: 6),
        ClipRRect(
          borderRadius: BorderRadius.circular(6),
          child: SizedBox(
            height: 8,
            child: TweenAnimationBuilder<double>(
              tween: Tween(begin: 0, end: share),
              duration: const Duration(milliseconds: 800),
              curve: Curves.easeOutCubic,
              builder: (context, v, _) => LinearProgressIndicator(value: v, backgroundColor: p.sunken, color: color),
            ),
          ),
        ),
      ],
    );
  }
}

/// Revenue and expenses per month as grouped bars (millions of Toman).
class TrendChart extends StatelessWidget {
  const TrendChart({super.key, required this.points});

  final List<TrendPoint> points;

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    double m(int irr) => irr / 10 / 1000000;
    final maxY = points.fold<double>(1, (acc, e) => [acc, m(e.revenueIrr), m(e.expensesIrr)].reduce((a, b) => a > b ? a : b));
    return Column(
      children: [
        Expanded(
          child: BarChart(
            BarChartData(
              maxY: maxY * 1.15,
              gridData: FlGridData(drawVerticalLine: false, getDrawingHorizontalLine: (_) => FlLine(color: p.line, strokeWidth: 1, dashArray: [4, 4])),
              borderData: FlBorderData(show: false),
              barTouchData: BarTouchData(enabled: false),
              titlesData: FlTitlesData(
                topTitles: const AxisTitles(),
                rightTitles: const AxisTitles(),
                leftTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    reservedSize: 34,
                    getTitlesWidget: (value, meta) => Text(fa(value.round()), style: TextStyle(fontSize: 10, color: p.low)),
                  ),
                ),
                bottomTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    getTitlesWidget: (value, meta) {
                      final i = value.toInt();
                      if (i < 0 || i >= points.length) return const SizedBox.shrink();
                      final key = points[i].key;
                      return Padding(padding: const EdgeInsets.only(top: 6), child: Text(fa(key.length >= 7 ? key.substring(5) : key), style: TextStyle(fontSize: 10, color: p.low)));
                    },
                  ),
                ),
              ),
              barGroups: [
                for (var i = 0; i < points.length; i++)
                  BarChartGroupData(
                    x: i,
                    barsSpace: 3,
                    barRods: [
                      BarChartRodData(toY: m(points[i].revenueIrr), color: AppColors.success, width: 8, borderRadius: BorderRadius.circular(4)),
                      BarChartRodData(toY: m(points[i].expensesIrr), color: AppColors.danger, width: 8, borderRadius: BorderRadius.circular(4)),
                    ],
                  ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 10),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.circle, size: 9, color: AppColors.success),
            const SizedBox(width: 5),
            Text("درآمد", style: TextStyle(fontSize: 11.5, color: p.mid)),
            const SizedBox(width: 16),
            const Icon(Icons.circle, size: 9, color: AppColors.danger),
            const SizedBox(width: 5),
            Text("هزینه", style: TextStyle(fontSize: 11.5, color: p.mid)),
            const SizedBox(width: 16),
            Text("میلیون تومان", style: TextStyle(fontSize: 11, color: p.low)),
          ],
        ),
      ],
    );
  }
}
