import "package:flutter/material.dart";

import "package:davos_admin/core/theme/app_colors.dart";
import "package:davos_admin/core/theme/pit.dart";
import "package:davos_admin/core/utils/fa.dart";
import "package:davos_admin/features/reservations/model/reservation.dart";
import "package:davos_admin/shared/widgets/capacity_ring.dart";
import "package:davos_admin/shared/widgets/pressable.dart";
import "package:davos_admin/shared/widgets/ticket_card.dart";

/// The day as a vertical timeline: a node per session, its free karts, and the tickets sold for it.
class SessionTimeline extends StatelessWidget {
  const SessionTimeline({
    super.key,
    required this.sessions,
    required this.tickets,
    required this.onSell,
    required this.onCheckIn,
    required this.onCancel,
    this.nowTime,
  });

  final List<SessionSlot> sessions;
  final List<Reservation> tickets;

  /// Sell a ticket for this session.
  final void Function(SessionSlot) onSell;
  final void Function(Reservation) onCheckIn;
  final void Function(Reservation) onCancel;

  /// "HH:MM" now (only when the shown day is today), to mark the current session.
  final String? nowTime;

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    final times = {...sessions.map((s) => s.time), ...tickets.map((t) => t.time)}.toList()..sort();
    if (times.isEmpty) return const SizedBox.shrink();
    String? currentTime;
    if (nowTime != null) {
      for (final t in times) {
        if (t.compareTo(nowTime!) <= 0) currentTime = t;
      }
    }
    return Column(
      children: [
        for (var i = 0; i < times.length; i++)
          _Node(
            time: times[i],
            slot: sessions.where((s) => s.time == times[i]).firstOrNull,
            tickets: tickets.where((t) => t.time == times[i]).toList(),
            first: i == 0,
            last: i == times.length - 1,
            current: times[i] == currentTime,
            line: p.line,
            onSell: onSell,
            onCheckIn: onCheckIn,
            onCancel: onCancel,
          ),
      ],
    );
  }
}

class _Node extends StatelessWidget {
  const _Node({
    required this.time,
    required this.slot,
    required this.tickets,
    required this.first,
    required this.last,
    required this.current,
    required this.line,
    required this.onSell,
    required this.onCheckIn,
    required this.onCancel,
  });

  final String time;
  final SessionSlot? slot;
  final List<Reservation> tickets;
  final bool first;
  final bool last;
  final bool current;
  final Color line;
  final void Function(SessionSlot) onSell;
  final void Function(Reservation) onCheckIn;
  final void Function(Reservation) onCancel;

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    final s = slot;
    final totalCap = s == null ? 0 : s.singleCapacity + s.doubleCapacity;
    final left = s == null ? 0 : s.singlesLeft + s.doublesLeft;
    final blocked = s?.blocked ?? false;
    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          SizedBox(
            width: 54,
            child: Column(
              children: [
                Text(fa(time), style: TextStyle(fontWeight: FontWeight.w700, fontSize: 14, color: current ? AppColors.accent : p.hi)),
                const SizedBox(height: 6),
                Expanded(
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Column(
                        children: [
                          Container(
                            width: current ? 14 : 10,
                            height: current ? 14 : 10,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              color: current ? AppColors.accent : (tickets.isEmpty ? p.bg : p.mid),
                              border: Border.all(color: current ? AppColors.accent : p.lineStrong, width: 2),
                              boxShadow: current ? const [BoxShadow(color: Color(0x66FFC400), blurRadius: 12)] : null,
                            ),
                          ),
                          Expanded(child: Container(width: 2, color: last ? Colors.transparent : line)),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.only(bottom: 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (s != null)
                    Pressable(
                      onTap: blocked ? null : () => onSell(s),
                      child: Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: p.surface,
                          borderRadius: BorderRadius.circular(18),
                          border: Border.all(color: current ? AppColors.accent.withValues(alpha: 0.6) : p.line),
                        ),
                        child: Row(
                          children: [
                            CapacityRing(used: totalCap - left, capacity: totalCap, size: 46, stroke: 4.5),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    blocked ? "بسته" : (left == 0 ? "پر است" : "${fa(s.singlesLeft)} تک • ${fa(s.doublesLeft)} دونفره خالی"),
                                    style: TextStyle(fontWeight: FontWeight.w700, fontSize: 13.5, color: blocked ? p.low : (left == 0 ? AppColors.danger : p.hi)),
                                  ),
                                  const SizedBox(height: 2),
                                  Text(
                                    tickets.isEmpty ? "بلیتی فروخته نشده" : "${fa(tickets.where((t) => t.status != "cancelled" && t.status != "expired").length)} بلیت",
                                    style: TextStyle(fontSize: 12, color: p.mid),
                                  ),
                                ],
                              ),
                            ),
                            if (!blocked)
                              Container(
                                width: 36,
                                height: 36,
                                decoration: BoxDecoration(color: AppColors.accent.withValues(alpha: 0.16), shape: BoxShape.circle),
                                child: const Icon(Icons.add_rounded, color: AppColors.accent),
                              ),
                          ],
                        ),
                      ),
                    ),
                  for (final t in tickets)
                    Padding(
                      padding: const EdgeInsets.only(top: 10),
                      child: TicketCard(reservation: t, onCheckIn: () => onCheckIn(t), onCancel: () => onCancel(t)),
                    ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
