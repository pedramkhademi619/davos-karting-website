import "package:flutter/material.dart";
import "package:get/get.dart";

import "package:davos_admin/core/constants/named_routs.dart";
import "package:davos_admin/core/theme/pit.dart";
import "package:davos_admin/core/utils/fa.dart";
import "package:davos_admin/core/utils/jalali.dart";
import "package:davos_admin/features/reservations/controller/reservation_actions.dart";
import "package:davos_admin/features/reservations/controller/reservations_controller.dart";
import "package:davos_admin/features/reservations/model/reservation.dart";
import "package:davos_admin/features/reservations/page/day_strip.dart";
import "package:davos_admin/features/reservations/page/session_timeline.dart";
import "package:davos_admin/shared/dialog/jalali_date_picker.dart";
import "package:davos_admin/shared/widgets/app_card.dart";
import "package:davos_admin/shared/widgets/form_fields.dart";
import "package:davos_admin/shared/widgets/skeleton.dart";
import "package:davos_admin/shared/widgets/state_view.dart";

/// The reservations tab: pick a day on the strip, see its sessions as a timeline with the tickets under each.
class ReservationsView extends GetView<ReservationsController> {
  const ReservationsView({super.key});

  Future<void> _sell(SessionSlot? slot) async {
    await Get.toNamed(NamedRouts.newReservation, arguments: {"date": controller.day.value, "time": slot?.time});
    controller.reload();
  }

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    return SafeArea(
      bottom: false,
      child: RefreshIndicator(
        onRefresh: controller.reload,
        child: Obx(() {
          final board = controller.board.value;
          final first = board == null;
          final today = businessDayIso();
          return ListView(
            padding: const EdgeInsets.only(bottom: 130),
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 14, 12, 8),
                child: Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text("رزروها", style: TextStyle(fontSize: 26, fontWeight: FontWeight.w700)),
                          Text(
                            board == null ? " " : "${jalaliWithWeekday(controller.day.value)} ${fa(jalaliOfIso(controller.day.value).year)}",
                            style: TextStyle(color: p.mid, fontSize: 13),
                          ),
                        ],
                      ),
                    ),
                    IconButton.filledTonal(
                      onPressed: () async {
                        final picked = await showJalaliDatePicker(context, initialIso: controller.day.value);
                        if (picked != null) controller.setDay(picked);
                      },
                      icon: const Icon(Icons.calendar_month_rounded),
                      tooltip: "انتخاب تاریخ",
                    ),
                    IconButton.filledTonal(onPressed: () => Get.toNamed(NamedRouts.search), icon: const Icon(Icons.search_rounded), tooltip: "جستجوی بلیت"),
                  ],
                ),
              ),
              DayStrip(selected: controller.day.value, onSelect: controller.setDay),
              if (first && controller.loading.value)
                const Padding(padding: EdgeInsets.all(20), child: Column(children: [Skeleton(height: 90, radius: 22), SizedBox(height: 12), Skeleton(height: 160, radius: 22)]))
              else if (first && controller.error.value != null)
                SizedBox(height: 320, child: StateView.error(controller.error.value!, onRetry: controller.reload))
              else if (board != null) ...[
                Padding(
                  padding: const EdgeInsets.fromLTRB(20, 14, 20, 0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          if (board.isHoliday) const _Tag("روز تعطیل", Icons.celebration_rounded),
                          if (board.isClosed) const _Tag("رزرو آنلاین بسته است", Icons.lock_rounded),
                          _Tag("تک‌نفره ${tomanText(board.singlePriceToman)}", Icons.directions_car_rounded),
                          _Tag("دونفره ${tomanText(board.doublePriceToman)}", Icons.people_rounded),
                        ],
                      ),
                      const SizedBox(height: 14),
                      AppCard(
                        padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 8),
                        child: Row(
                          children: [
                            _Metric(fa(controller.ticketCount), "بلیت"),
                            _Metric(fa(controller.kartCount), "خودرو"),
                            _Metric(fa(controller.peopleCount), "نفر"),
                            _Metric(grouped(controller.revenueToman ~/ 1000), "هزار تومان"),
                          ],
                        ),
                      ),
                      const SizedBox(height: 14),
                      PillSelector<String>(
                        options: const {"all": "همه", "confirmed": "قطعی", "attended": "وارد شده", "held": "در انتظار پرداخت", "cancelled": "لغو شده"},
                        value: controller.filter.value,
                        onChanged: (v) => controller.filter.value = v,
                      ),
                      const SizedBox(height: 20),
                    ],
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: board.sessions.isEmpty && controller.visible.isEmpty
                      ? SizedBox(height: 240, child: StateView.empty("برای این روز سانسی تعریف نشده است.", icon: Icons.event_busy_rounded))
                      : SessionTimeline(
                          sessions: controller.filter.value == "all" ? board.sessions : const [],
                          tickets: controller.visible,
                          nowTime: controller.day.value == today ? _nowTime() : null,
                          onSell: _sell,
                          onCheckIn: (r) async {
                            if (await ReservationActions.checkIn(r)) controller.reload();
                          },
                          onCancel: (r) async {
                            if (await ReservationActions.cancel(context, r)) controller.reload();
                          },
                        ),
                ),
              ],
            ],
          );
        }),
      ),
    );
  }

  static String _nowTime() {
    final t = DateTime.now().toUtc().add(const Duration(hours: 3, minutes: 30));
    return "${t.hour.toString().padLeft(2, "0")}:${t.minute.toString().padLeft(2, "0")}";
  }
}

class _Tag extends StatelessWidget {
  const _Tag(this.text, this.icon);

  final String text;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 6),
      decoration: BoxDecoration(color: p.surface, borderRadius: BorderRadius.circular(12), border: Border.all(color: p.line)),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [Icon(icon, size: 14, color: p.accentText), const SizedBox(width: 6), Text(text, style: TextStyle(fontSize: 12, color: p.mid))],
      ),
    );
  }
}

class _Metric extends StatelessWidget {
  const _Metric(this.value, this.label);

  final String value;
  final String label;

  @override
  Widget build(BuildContext context) => Expanded(
    child: Column(
      children: [
        Text(value, style: const TextStyle(fontSize: 21, fontWeight: FontWeight.w700, height: 1.2)),
        const SizedBox(height: 2),
        Text(label, style: TextStyle(fontSize: 11.5, color: context.pit.mid)),
      ],
    ),
  );
}
