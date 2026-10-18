import "dart:math" as math;

import "package:flutter/material.dart";
import "package:flutter/services.dart";

import "package:davos_admin/core/theme/app_colors.dart";
import "package:davos_admin/core/theme/pit.dart";
import "package:davos_admin/core/utils/fa.dart";
import "package:davos_admin/core/utils/jalali.dart";
import "package:davos_admin/features/reservations/model/reservation.dart";
import "package:davos_admin/shared/dialog/dialogs.dart";
import "package:davos_admin/shared/widgets/app_button.dart";
import "package:davos_admin/shared/widgets/pressable.dart";
import "package:davos_admin/shared/widgets/status_chip.dart";

/// A reservation drawn as a real ticket: the session time and status on top, a perforated tear line, the customer
/// below. The two main actions (check in, cancel) sit on the ticket itself.
class TicketCard extends StatelessWidget {
  const TicketCard({super.key, required this.reservation, this.onCheckIn, this.onCancel, this.showDate = false, this.highlight = false});

  final Reservation reservation;
  final VoidCallback? onCheckIn;
  final VoidCallback? onCancel;
  final bool showDate;
  final bool highlight;

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    final r = reservation;
    final dim = r.status == "cancelled" || r.status == "expired";
    final karts = [
      if (r.singleCount > 0) "${fa(r.singleCount)} تک‌نفره",
      if (r.doubleCount > 0) "${fa(r.doubleCount)} دونفره",
    ].join(" + ");
    return Opacity(
      opacity: dim ? 0.62 : 1,
      child: Container(
        decoration: BoxDecoration(
          color: p.surface,
          borderRadius: BorderRadius.circular(22),
          border: Border.all(color: highlight ? AppColors.accent : p.line, width: highlight ? 1.5 : 1),
          boxShadow: p.shadow,
        ),
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(18, 16, 18, 14),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(fa(r.time), style: TextStyle(fontSize: 30, fontWeight: FontWeight.w700, color: p.hi, height: 1.1)),
                      const SizedBox(height: 4),
                      Text(
                        showDate ? "${jalaliWithWeekday(r.date)} • $karts" : karts,
                        style: TextStyle(color: p.mid, fontSize: 12.5),
                      ),
                    ],
                  ),
                  const Spacer(),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      StatusChip(r.statusLabel, tone: reservationTone(r.status)),
                      const SizedBox(height: 8),
                      Text("#${fa(r.ticketNumber)}", style: TextStyle(color: p.accentText, fontWeight: FontWeight.w700, fontSize: 18, height: 1)),
                    ],
                  ),
                ],
              ),
            ),
            _TearLine(bg: p.bg, line: p.line, dash: p.lineStrong),
            Padding(
              padding: const EdgeInsets.fromLTRB(18, 14, 18, 14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(r.contactName.isEmpty ? "مشتری حضوری" : r.contactName, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15)),
                            if (r.contactMobile.isNotEmpty)
                              Pressable(
                                onTap: () {
                                  Clipboard.setData(ClipboardData(text: r.contactMobile));
                                  toast("شماره کپی شد.");
                                },
                                child: Padding(
                                  padding: const EdgeInsets.only(top: 3),
                                  child: Row(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      Text(fa(r.contactMobile), textDirection: TextDirection.ltr, style: TextStyle(color: p.mid, fontSize: 13)),
                                      const SizedBox(width: 6),
                                      Icon(Icons.copy_rounded, size: 13, color: p.low),
                                    ],
                                  ),
                                ),
                              ),
                          ],
                        ),
                      ),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: [
                          Text(tomanText(r.amountToman), style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15)),
                          const SizedBox(height: 3),
                          Text(
                            "${r.isOnline ? "آنلاین" : "حضوری"}${r.paymentMethod != "none" ? " • ${paymentMethodLabels[r.paymentMethod]}" : ""}",
                            style: TextStyle(color: p.low, fontSize: 12),
                          ),
                        ],
                      ),
                    ],
                  ),
                  if (r.confirmedLate)
                    _Note(icon: Icons.schedule_rounded, text: "پرداخت بعد از پایان مهلت تایید شده است.", color: AppColors.warning),
                  if (r.note.isNotEmpty) _Note(icon: Icons.notes_rounded, text: r.note, color: p.mid),
                  if (r.cancelReason.isNotEmpty) _Note(icon: Icons.block_rounded, text: r.cancelReason, color: AppColors.danger),
                  if (onCheckIn != null && r.canCheckIn || onCancel != null && r.canCancel) ...[
                    const SizedBox(height: 14),
                    Row(
                      children: [
                        if (onCheckIn != null && r.canCheckIn)
                          Expanded(flex: 3, child: AppButton(label: "ورود مشتری", icon: Icons.how_to_reg_rounded, onPressed: onCheckIn, small: true)),
                        if (onCheckIn != null && r.canCheckIn && onCancel != null && r.canCancel) const SizedBox(width: 10),
                        if (onCancel != null && r.canCancel)
                          Expanded(flex: 2, child: AppButton(label: "لغو", onPressed: onCancel, outlined: true, danger: true, small: true)),
                      ],
                    ),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Note extends StatelessWidget {
  const _Note({required this.icon, required this.text, required this.color});

  final IconData icon;
  final String text;
  final Color color;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(top: 10),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, size: 15, color: color),
        const SizedBox(width: 8),
        Expanded(child: Text(text, style: TextStyle(color: color, fontSize: 12.5, height: 1.6))),
      ],
    ),
  );
}

/// The perforation between the two halves of a ticket: a dashed line with a half-circle bitten out of each end.
class _TearLine extends StatelessWidget {
  const _TearLine({required this.bg, required this.line, required this.dash});

  final Color bg;
  final Color line;
  final Color dash;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 22,
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          Positioned.fill(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 18),
              child: CustomPaint(painter: _DashPainter(dash)),
            ),
          ),
          Positioned.fill(child: CustomPaint(painter: _NotchPainter(bg, line))),
        ],
      ),
    );
  }
}

/// The two bites: a circle in the page colour centred on each edge, with only its inside half outlined.
class _NotchPainter extends CustomPainter {
  _NotchPainter(this.bg, this.line);

  final Color bg;
  final Color line;

  @override
  void paint(Canvas canvas, Size size) {
    const r = 11.0;
    final fill = Paint()..color = bg;
    final stroke = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1
      ..color = line;
    final left = Offset(0, size.height / 2);
    final right = Offset(size.width, size.height / 2);
    canvas.drawCircle(left, r, fill);
    canvas.drawCircle(right, r, fill);
    canvas.drawArc(Rect.fromCircle(center: left, radius: r), -math.pi / 2, math.pi, false, stroke);
    canvas.drawArc(Rect.fromCircle(center: right, radius: r), math.pi / 2, math.pi, false, stroke);
  }

  @override
  bool shouldRepaint(_NotchPainter old) => old.bg != bg || old.line != line;
}

class _DashPainter extends CustomPainter {
  _DashPainter(this.color);

  final Color color;

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..strokeWidth = 1.4;
    var x = 0.0;
    while (x < size.width) {
      canvas.drawLine(Offset(x, size.height / 2), Offset(x + 6, size.height / 2), paint);
      x += 11;
    }
  }

  @override
  bool shouldRepaint(_DashPainter old) => old.color != color;
}
