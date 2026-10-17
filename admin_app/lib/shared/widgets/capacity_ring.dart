import "dart:math" as math;

import "package:flutter/material.dart";

import "package:davos_admin/core/theme/app_colors.dart";
import "package:davos_admin/core/theme/pit.dart";
import "package:davos_admin/core/utils/fa.dart";

/// How full a session is: a ring that goes amber then red as the karts run out, with the free count in the middle.
class CapacityRing extends StatelessWidget {
  const CapacityRing({super.key, required this.used, required this.capacity, this.size = 56, this.stroke = 5, this.showFree = true});

  final int used;
  final int capacity;
  final double size;
  final double stroke;

  /// Show the free count (otherwise the used count) in the middle.
  final bool showFree;

  /// Share of the capacity still free (0..1).
  double get freeShare => capacity <= 0 ? 0 : ((capacity - used) / capacity).clamp(0, 1).toDouble();

  static Color colorFor(double freeShare) => freeShare <= 0 ? AppColors.danger : (freeShare < 0.34 ? AppColors.warning : AppColors.success);

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    final color = colorFor(freeShare);
    return SizedBox(
      width: size,
      height: size,
      child: TweenAnimationBuilder<double>(
        tween: Tween(begin: 0, end: capacity <= 0 ? 0 : (used / capacity).clamp(0, 1).toDouble()),
        duration: const Duration(milliseconds: 700),
        curve: Curves.easeOutCubic,
        builder: (context, value, _) => CustomPaint(
          painter: _RingPainter(progress: value, color: color, track: p.sunken, stroke: stroke),
          child: Center(
            child: Text(
              fa(showFree ? math.max(capacity - used, 0) : used),
              style: TextStyle(fontWeight: FontWeight.w700, fontSize: size * 0.3, color: p.hi, height: 1),
            ),
          ),
        ),
      ),
    );
  }
}

class _RingPainter extends CustomPainter {
  _RingPainter({required this.progress, required this.color, required this.track, required this.stroke});

  final double progress;
  final Color color;
  final Color track;
  final double stroke;

  @override
  void paint(Canvas canvas, Size size) {
    final rect = Offset.zero & size;
    final inner = rect.deflate(stroke / 2);
    final base = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = stroke
      ..color = track;
    canvas.drawArc(inner, 0, math.pi * 2, false, base);
    if (progress <= 0) return;
    final arc = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = stroke
      ..strokeCap = StrokeCap.round
      ..color = color;
    // Start at the top and run clockwise.
    canvas.drawArc(inner, -math.pi / 2, math.pi * 2 * progress, false, arc);
  }

  @override
  bool shouldRepaint(_RingPainter old) => old.progress != progress || old.color != color || old.track != track;
}
