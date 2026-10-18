import "package:flutter/material.dart" hide Flow;
import "package:get/get.dart";

import "package:davos_admin/core/constants/named_routs.dart";
import "package:davos_admin/core/theme/app_colors.dart";
import "package:davos_admin/core/theme/pit.dart";
import "package:davos_admin/core/utils/fa.dart";
import "package:davos_admin/core/utils/jalali.dart";
import "package:davos_admin/features/accounting/controller/accounting_data_controller.dart";
import "package:davos_admin/features/accounting/controller/day_book_controller.dart";
import "package:davos_admin/features/accounting/model/accounting_models.dart";
import "package:davos_admin/features/accounting/model/accounting_month.dart";
import "package:davos_admin/shared/dialog/dialogs.dart";
import "package:davos_admin/shared/widgets/app_card.dart";
import "package:davos_admin/shared/widgets/state_view.dart";

/// The month day by day: ticket sales as one line per day, then everything recorded by hand. Long-press (or the trash
/// icon) deletes a wrong entry; the books keep a reversing entry, so nothing silently disappears.
class DayBookPage extends GetView<DayBookController> {
  const DayBookPage({super.key});

  @override
  Widget build(BuildContext context) {
    final data = Get.find<AccountingDataController>();
    return Scaffold(
      appBar: AppBar(title: const Text("دفتر روزانه")),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () async {
          if (await Get.toNamed(NamedRouts.accountingEntry, arguments: "expense") == true) controller.reload();
        },
        icon: const Icon(Icons.add_rounded),
        label: const Text("ثبت"),
      ),
      body: Column(
        children: [
          Obx(() => MonthStepper(month: controller.month.value, onStep: controller.step)),
          Expanded(
            child: Obx(() {
              if (controller.loading.value && controller.days.isEmpty) return StateView.loading();
              if (controller.error.value != null) return StateView.error(controller.error.value!, onRetry: controller.reload);
              if (controller.days.isEmpty) return StateView.empty("در این ماه چیزی ثبت نشده است.");
              final byId = data.byId;
              return RefreshIndicator(
                onRefresh: controller.reload,
                child: ListView.separated(
                  padding: const EdgeInsets.fromLTRB(16, 4, 16, 110),
                  itemCount: controller.days.length,
                  separatorBuilder: (_, _) => const SizedBox(height: 12),
                  itemBuilder: (context, i) => _Day(day: controller.days[i], byId: byId, controller: controller),
                ),
              );
            }),
          ),
        ],
      ),
    );
  }
}

/// ‹ مهر ۱۴۰۵ › : steps through Jalali months, never past the current one.
class MonthStepper extends StatelessWidget {
  const MonthStepper({super.key, required this.month, required this.onStep});

  final AccountingMonth month;
  final ValueChanged<int> onStep;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.fromLTRB(12, 6, 12, 8),
    child: Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        IconButton.outlined(onPressed: () => onStep(-1), icon: const Icon(Icons.chevron_left_rounded), tooltip: "ماه قبل"),
        SizedBox(width: 150, child: Text(month.label, textAlign: TextAlign.center, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700))),
        IconButton.outlined(onPressed: month.isCurrent ? null : () => onStep(1), icon: const Icon(Icons.chevron_right_rounded), tooltip: "ماه بعد"),
      ],
    ),
  );
}

class _Day extends StatelessWidget {
  const _Day({required this.day, required this.byId, required this.controller});

  final DayBookDay day;
  final Map<String, Account> byId;
  final DayBookController controller;

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    final sales = day.sales;
    return AppCard(
      padding: EdgeInsets.zero,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            decoration: BoxDecoration(color: p.sunken, borderRadius: const BorderRadius.vertical(top: Radius.circular(22))),
            child: Text(jalaliWithWeekday(day.date), style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13.5)),
          ),
          if (sales != null)
            _Row(
              flow: Flow.moneyIn,
              title: "فروش بلیت",
              subtitle: [
                if (sales.onlineIrr != 0) "آنلاین ${tomanFromIrr(sales.onlineIrr)}",
                if (sales.cashIrr != 0) "نقد ${tomanFromIrr(sales.cashIrr)}",
                if (sales.cardIrr != 0) "کارت ${tomanFromIrr(sales.cardIrr)}",
              ].join(" · "),
              amountIrr: sales.receivedIrr,
            ),
          for (final entry in day.entries)
            Builder(
              builder: (context) {
                final view = EntryView.of(entry, byId);
                return _Row(
                  flow: view.flow,
                  title: view.title,
                  subtitle: [if (view.category != null && view.category != view.title) view.category!, ?view.wallet, if (entry.reversed) "حذف شده"].where((s) => s.isNotEmpty).join(" · "),
                  amountIrr: view.amountIrr,
                  faded: entry.reversed,
                  onDelete: entry.deletable ? () => _delete(context, entry, view) : null,
                );
              },
            ),
        ],
      ),
    );
  }

  Future<void> _delete(BuildContext context, Entry entry, EntryView view) async {
    final ok = await confirm(context, title: "حذف از دفتر", message: "«${view.title}» به مبلغ ${tomanFromIrr(view.amountIrr)} تومان حذف شود؟", confirmLabel: "حذف", danger: true);
    if (!ok) return;
    final message = await controller.remove(entry);
    toast(message ?? "حذف شد.", error: message != null);
  }
}

class _Row extends StatelessWidget {
  const _Row({required this.flow, required this.title, required this.subtitle, required this.amountIrr, this.faded = false, this.onDelete});

  final Flow flow;
  final String title;
  final String subtitle;
  final int amountIrr;
  final bool faded;
  final VoidCallback? onDelete;

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    final (icon, color, sign) = switch (flow) {
      Flow.moneyIn => (Icons.south_rounded, AppColors.success, "+"),
      Flow.moneyOut => (Icons.north_rounded, AppColors.danger, "−"),
      Flow.move => (Icons.swap_horiz_rounded, p.mid, ""),
      Flow.other => (Icons.circle_outlined, p.mid, ""),
    };
    return InkWell(
      onLongPress: onDelete,
      child: Opacity(
        opacity: faded ? 0.5 : 1,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 11),
          child: Row(
            children: [
              CircleAvatar(radius: 17, backgroundColor: color.withValues(alpha: 0.14), child: Icon(icon, size: 18, color: color)),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title, style: TextStyle(fontWeight: FontWeight.w700, decoration: faded ? TextDecoration.lineThrough : null)),
                    if (subtitle.isNotEmpty) Text(subtitle, style: TextStyle(color: p.low, fontSize: 11.5)),
                  ],
                ),
              ),
              Text("$sign${tomanFromIrr(amountIrr)}", textDirection: TextDirection.ltr, style: TextStyle(fontWeight: FontWeight.w700, color: color)),
              if (onDelete != null) IconButton(onPressed: onDelete, icon: Icon(Icons.delete_outline_rounded, size: 19, color: p.low), tooltip: "حذف"),
            ],
          ),
        ),
      ),
    );
  }
}
