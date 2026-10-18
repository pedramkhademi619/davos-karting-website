import "package:flutter/material.dart";
import "package:get/get.dart";

import "package:davos_admin/core/constants/named_routs.dart";
import "package:davos_admin/core/theme/app_colors.dart";
import "package:davos_admin/core/theme/pit.dart";
import "package:davos_admin/core/utils/fa.dart";
import "package:davos_admin/core/utils/jalali.dart";
import "package:davos_admin/features/auth/controller/session_controller.dart";
import "package:davos_admin/features/dashboard/controller/dashboard_controller.dart";
import "package:davos_admin/features/reservations/controller/reservations_controller.dart";
import "package:davos_admin/features/reservations/model/reservation.dart";
import "package:davos_admin/features/shell/shell_controller.dart";
import "package:davos_admin/shared/widgets/animated_count.dart";
import "package:davos_admin/shared/widgets/app_card.dart";
import "package:davos_admin/shared/widgets/capacity_ring.dart";
import "package:davos_admin/shared/widgets/pressable.dart";
import "package:davos_admin/shared/widgets/skeleton.dart";
import "package:davos_admin/shared/widgets/state_view.dart";

/// The first tab: how today is going, what to do next, and what needs attention.
class TodayView extends GetView<TodayController> {
  const TodayView({super.key});

  static String _greeting() {
    final h = DateTime.now().toUtc().add(const Duration(hours: 3, minutes: 30)).hour;
    if (h < 5) return "شب بخیر";
    if (h < 12) return "صبح بخیر";
    if (h < 16) return "ظهر بخیر";
    if (h < 19) return "عصر بخیر";
    return "شب بخیر";
  }

  void _openSection(String target) {
    final shell = Get.find<ShellController>();
    switch (target) {
      case "reservations":
        shell.open(1);
      case "system":
        Get.toNamed(NamedRouts.system);
      case "settings":
        Get.toNamed(NamedRouts.settings);
      case "sms":
        Get.toNamed(NamedRouts.sms);
    }
  }

  void _toReservations(String? day, String? time) {
    if (day != null && Get.isRegistered<ReservationsController>()) Get.find<ReservationsController>().setDay(day);
    Get.find<ShellController>().open(1);
  }

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    final session = Get.find<SessionController>();
    final me = session.me.value;
    return SafeArea(
      bottom: false,
      child: RefreshIndicator(
        onRefresh: controller.reload,
        child: Obx(() {
          final loadingFirst = controller.loading.value && controller.summary.value == null && controller.board.value == null;
          if (loadingFirst) {
            return ListView(
              padding: const EdgeInsets.all(20),
              children: const [Skeleton(height: 44, width: 200), SizedBox(height: 20), Skeleton(height: 210, radius: 28), SizedBox(height: 16), Skeleton(height: 90, radius: 22), SizedBox(height: 16), Skeleton(height: 120, radius: 22)],
            );
          }
          final failed = controller.error.value != null && controller.summary.value == null && controller.board.value == null;
          if (failed) return ListView(children: [SizedBox(height: 480, child: StateView.error(controller.error.value!, onRetry: controller.reload))]);
          final board = controller.board.value;
          final next = controller.nextSession();
          final summary = controller.summary.value;
          final alerts = controller.alerts;
          return ListView(
            padding: const EdgeInsets.only(bottom: 130),
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 14, 20, 0),
                child: Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text("${_greeting()}${me == null ? "" : "، ${me.shownName}"}", style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w700)),
                          const SizedBox(height: 2),
                          Text("${jalaliWithWeekday(controller.day)} ${fa(jalaliOfIso(controller.day).year)}", style: TextStyle(color: p.mid, fontSize: 13.5)),
                        ],
                      ),
                    ),
                    Pressable(
                      onTap: () => Get.find<ShellController>().open(Get.find<ShellController>().lastIndex),
                      child: Container(
                        width: 46,
                        height: 46,
                        decoration: BoxDecoration(gradient: AppColors.amber, shape: BoxShape.circle),
                        child: Center(
                          child: Text(
                            (me?.shownName ?? "؟").characters.first,
                            style: const TextStyle(color: AppColors.ink, fontSize: 19, fontWeight: FontWeight.w700),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 18),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: _Hero(controller: controller, next: next, hasTickets: session.can("reservations")),
              ),
              const SizedBox(height: 16),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: Row(
                  children: [
                    if (session.can("reservations")) ...[
                      _Quick(icon: Icons.confirmation_number_rounded, label: "فروش بلیت", primary: true, onTap: () async {
                        await Get.toNamed(NamedRouts.newReservation, arguments: {"date": controller.day, "time": next?.time});
                        controller.reload();
                      }),
                      _Quick(icon: Icons.how_to_reg_rounded, label: "ورود مشتری", onTap: () => Get.toNamed(NamedRouts.search)),
                      _Quick(icon: Icons.calendar_view_day_rounded, label: "سانس‌ها", onTap: () => _toReservations(controller.day, null)),
                    ],
                    if (session.can("sms")) _Quick(icon: Icons.sms_rounded, label: "پیامک", onTap: () => Get.toNamed(NamedRouts.sms)),
                  ],
                ),
              ),
              if (alerts.isNotEmpty) ...[
                const _Heading("نیاز به توجه"),
                for (final a in alerts)
                  Padding(
                    padding: const EdgeInsets.fromLTRB(20, 0, 20, 10),
                    child: _AlertTile(alert: a, onTap: () => _openSection(a.target)),
                  ),
              ],
              if (board != null && board.sessions.isNotEmpty) ...[
                _Heading("سانس‌های امروز", trailing: "همه", onTrailing: () => _toReservations(controller.day, null)),
                SizedBox(
                  height: 146,
                  child: ListView.builder(
                    scrollDirection: Axis.horizontal,
                    padding: const EdgeInsets.symmetric(horizontal: 20),
                    itemCount: board.sessions.length,
                    itemBuilder: (context, i) => _SessionChip(
                      slot: board.sessions[i],
                      isNext: board.sessions[i].time == next?.time,
                      tickets: controller.live.where((t) => t.time == board.sessions[i].time).length,
                      onTap: () => _toReservations(controller.day, board.sessions[i].time),
                    ),
                  ),
                ),
              ],
              if (summary != null) ...[
                const _Heading("این ماه"),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20),
                  child: Row(
                    children: [
                      Expanded(child: _MonthTile(label: "درآمد آنلاین", value: grouped(summary.monthOnlineRevenueToman), unit: "تومان", icon: Icons.trending_up_rounded)),
                      const SizedBox(width: 12),
                      Expanded(child: _MonthTile(label: "رزرو ثبت‌شده", value: fa(summary.monthReservations), unit: "بلیت", icon: Icons.confirmation_number_outlined)),
                    ],
                  ),
                ),
                if (summary.smsCreditToman != null)
                  Padding(
                    padding: const EdgeInsets.fromLTRB(20, 12, 20, 0),
                    child: AppCard(
                      onTap: () => Get.toNamed(NamedRouts.sms),
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                      child: Row(
                        children: [
                          Icon(Icons.sms_outlined, color: p.mid, size: 20),
                          const SizedBox(width: 12),
                          Expanded(child: Text("اعتبار پیامک", style: TextStyle(color: p.mid))),
                          Text(tomanText(summary.smsCreditToman!), style: const TextStyle(fontWeight: FontWeight.w700)),
                        ],
                      ),
                    ),
                  ),
              ],
            ],
          );
        }),
      ),
    );
  }
}

class _Heading extends StatelessWidget {
  const _Heading(this.text, {this.trailing, this.onTrailing});

  final String text;
  final String? trailing;
  final VoidCallback? onTrailing;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.fromLTRB(20, 26, 20, 12),
    child: Row(
      children: [
        Expanded(child: Text(text, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700))),
        if (trailing != null) Pressable(onTap: onTrailing, child: Text(trailing!, style: TextStyle(color: context.pit.accentText, fontWeight: FontWeight.w700, fontSize: 13))),
      ],
    ),
  );
}

/// The big card: today's tickets, who has arrived, and the next session.
class _Hero extends StatelessWidget {
  const _Hero({required this.controller, required this.next, required this.hasTickets});

  final TodayController controller;
  final SessionSlot? next;
  final bool hasTickets;

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    final s = controller.summary.value;
    final tickets = hasTickets ? controller.expected : (s?.todayConfirmed ?? 0);
    final arrived = hasTickets ? controller.attended : (s?.todayAttended ?? 0);
    final people = hasTickets ? controller.people : (s?.todayPeople ?? 0);
    final karts = hasTickets ? controller.karts : (s?.todayKarts ?? 0);
    final share = tickets == 0 ? 0.0 : (arrived / tickets).clamp(0, 1).toDouble();
    final fg = p.isDark ? p.hi : AppColors.ink;
    final soft = p.isDark ? p.mid : AppColors.ink.withValues(alpha: 0.7);
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(30),
        gradient: p.isDark
            ? const LinearGradient(begin: Alignment.topRight, end: Alignment.bottomLeft, colors: [Color(0xFF2A2208), Color(0xFF14161B), Color(0xFF121419)])
            : AppColors.amber,
        border: Border.all(color: p.isDark ? AppColors.accent.withValues(alpha: 0.25) : Colors.transparent),
        boxShadow: p.isDark ? const [BoxShadow(color: Color(0x1FFFC400), blurRadius: 40, spreadRadius: -8, offset: Offset(0, 14))] : const [BoxShadow(color: Color(0x40FFB300), blurRadius: 30, spreadRadius: -8, offset: Offset(0, 12))],
      ),
      padding: const EdgeInsets.all(22),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text("بلیت‌های امروز", style: TextStyle(color: soft, fontWeight: FontWeight.w500, fontSize: 13.5)),
          const SizedBox(height: 6),
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              AnimatedCount(value: tickets, style: TextStyle(fontSize: 58, fontWeight: FontWeight.w700, color: p.isDark ? AppColors.accent : AppColors.ink, height: 1.05)),
              const SizedBox(width: 10),
              Padding(padding: const EdgeInsets.only(bottom: 10), child: Text("بلیت", style: TextStyle(color: soft, fontSize: 15))),
              const Spacer(),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  _Mini("${fa(people)} نفر", fg),
                  const SizedBox(height: 4),
                  _Mini("${fa(karts)} خودرو", fg),
                ],
              ),
            ],
          ),
          const SizedBox(height: 18),
          ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: SizedBox(
              height: 8,
              child: TweenAnimationBuilder<double>(
                tween: Tween(begin: 0, end: share),
                duration: const Duration(milliseconds: 800),
                curve: Curves.easeOutCubic,
                builder: (context, v, _) => LinearProgressIndicator(
                  value: v,
                  backgroundColor: p.isDark ? Colors.white.withValues(alpha: 0.08) : AppColors.ink.withValues(alpha: 0.14),
                  color: p.isDark ? AppColors.success : AppColors.ink,
                ),
              ),
            ),
          ),
          const SizedBox(height: 8),
          Text("${fa(arrived)} از ${fa(tickets)} بلیت وارد شده‌اند", style: TextStyle(color: soft, fontSize: 12.5)),
          if (next != null) ...[
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 11),
              decoration: BoxDecoration(color: p.isDark ? Colors.white.withValues(alpha: 0.06) : Colors.white.withValues(alpha: 0.4), borderRadius: BorderRadius.circular(16)),
              child: Row(
                children: [
                  Icon(Icons.flag_rounded, size: 18, color: p.isDark ? AppColors.accent : AppColors.ink),
                  const SizedBox(width: 10),
                  Text("سانس بعدی", style: TextStyle(color: soft, fontSize: 13)),
                  const Spacer(),
                  Text(fa(next!.time), style: TextStyle(fontWeight: FontWeight.w700, fontSize: 17, color: fg)),
                  const SizedBox(width: 12),
                  Text("${fa(next!.singlesLeft + next!.doublesLeft)} خودرو خالی", style: TextStyle(color: soft, fontSize: 12.5)),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _Mini extends StatelessWidget {
  const _Mini(this.text, this.color);

  final String text;
  final Color color;

  @override
  Widget build(BuildContext context) => Text(text, style: TextStyle(color: color, fontWeight: FontWeight.w700, fontSize: 15));
}

class _Quick extends StatelessWidget {
  const _Quick({required this.icon, required this.label, required this.onTap, this.primary = false});

  final IconData icon;
  final String label;
  final VoidCallback onTap;
  final bool primary;

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    return Expanded(
      child: Pressable(
        onTap: onTap,
        child: Column(
          children: [
            Container(
              width: 62,
              height: 62,
              decoration: BoxDecoration(
                gradient: primary ? AppColors.amber : null,
                color: primary ? null : p.surface,
                borderRadius: BorderRadius.circular(22),
                border: Border.all(color: primary ? Colors.transparent : p.line),
                boxShadow: primary && p.isDark ? const [BoxShadow(color: Color(0x33FFC400), blurRadius: 20, offset: Offset(0, 8))] : null,
              ),
              child: Icon(icon, color: primary ? AppColors.ink : p.hi, size: 26),
            ),
            const SizedBox(height: 8),
            Text(label, style: TextStyle(fontSize: 12, fontWeight: FontWeight.w500, color: p.mid)),
          ],
        ),
      ),
    );
  }
}

class _AlertTile extends StatelessWidget {
  const _AlertTile({required this.alert, required this.onTap});

  final TodayAlert alert;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    final color = switch (alert.tone) {
      "danger" => AppColors.danger,
      "warning" => AppColors.warning,
      _ => AppColors.info,
    };
    final icon = switch (alert.tone) {
      "danger" => Icons.error_rounded,
      "warning" => Icons.warning_amber_rounded,
      _ => Icons.info_rounded,
    };
    return AppCard(
      onTap: onTap,
      padding: const EdgeInsets.all(14),
      borderColor: color.withValues(alpha: 0.35),
      color: Color.alphaBlend(color.withValues(alpha: p.isDark ? 0.07 : 0.06), p.surface),
      child: Row(
        children: [
          Icon(icon, color: color),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(alert.title, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14)),
                const SizedBox(height: 2),
                Text(alert.hint, style: TextStyle(color: p.mid, fontSize: 12.5, height: 1.5)),
              ],
            ),
          ),
          Icon(Icons.chevron_left_rounded, color: p.low),
        ],
      ),
    );
  }
}

class _SessionChip extends StatelessWidget {
  const _SessionChip({required this.slot, required this.isNext, required this.tickets, required this.onTap});

  final SessionSlot slot;
  final bool isNext;
  final int tickets;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    final cap = slot.singleCapacity + slot.doubleCapacity;
    final left = slot.singlesLeft + slot.doublesLeft;
    return Padding(
      padding: const EdgeInsetsDirectional.only(end: 10),
      child: Pressable(
        onTap: onTap,
        child: Container(
          width: 98,
          padding: const EdgeInsets.symmetric(vertical: 12),
          decoration: BoxDecoration(
            color: p.surface,
            borderRadius: BorderRadius.circular(22),
            border: Border.all(color: isNext ? AppColors.accent : p.line, width: isNext ? 1.6 : 1),
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(fa(slot.time), style: TextStyle(fontWeight: FontWeight.w700, fontSize: 16, color: isNext ? p.accentText : p.hi)),
              const SizedBox(height: 8),
              CapacityRing(used: cap - left, capacity: cap, size: 50, stroke: 5),
              const SizedBox(height: 8),
              Text(slot.blocked ? "بسته" : "${fa(tickets)} بلیت", style: TextStyle(color: p.mid, fontSize: 11.5)),
            ],
          ),
        ),
      ),
    );
  }
}

class _MonthTile extends StatelessWidget {
  const _MonthTile({required this.label, required this.value, required this.unit, required this.icon});

  final String label;
  final String value;
  final String unit;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    return AppCard(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(children: [Icon(icon, size: 17, color: p.accentText), const SizedBox(width: 6), Text(label, style: TextStyle(color: p.mid, fontSize: 12.5))]),
          const SizedBox(height: 10),
          FittedBox(fit: BoxFit.scaleDown, alignment: AlignmentDirectional.centerStart, child: Text(value, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w700, height: 1.1))),
          Text(unit, style: TextStyle(color: p.low, fontSize: 12)),
        ],
      ),
    );
  }
}
