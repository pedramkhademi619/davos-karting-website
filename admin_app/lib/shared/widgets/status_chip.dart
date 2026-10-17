import "package:flutter/material.dart";

import "package:davos_admin/core/theme/app_colors.dart";

enum Tone { success, danger, warning, info, neutral }

/// A small status pill: a coloured dot and a label.
class StatusChip extends StatelessWidget {
  const StatusChip(this.label, {super.key, this.tone = Tone.neutral, this.dot = true});

  final String label;
  final Tone tone;
  final bool dot;

  /// (background, foreground) for a tone.
  static (Color, Color) colors(Tone tone, Brightness brightness) {
    final dark = brightness == Brightness.dark;
    Color soft(Color c, Color lightSoft) => dark ? c.withValues(alpha: 0.16) : lightSoft;
    switch (tone) {
      case Tone.success:
        return (soft(AppColors.success, AppColors.successSoft), dark ? AppColors.success : const Color(0xFF0B6B38));
      case Tone.danger:
        return (soft(AppColors.danger, AppColors.dangerSoft), dark ? const Color(0xFFFF8A7E) : const Color(0xFF9A1B10));
      case Tone.warning:
        return (soft(AppColors.warning, AppColors.warningSoft), dark ? AppColors.warning : const Color(0xFF6B4A00));
      case Tone.info:
        return (soft(AppColors.info, AppColors.infoSoft), dark ? const Color(0xFF8DB6FF) : const Color(0xFF123F8C));
      case Tone.neutral:
        return (dark ? Colors.white.withValues(alpha: 0.08) : const Color(0xFFECEBE5), dark ? const Color(0xFFB4B8C3) : const Color(0xFF575963));
    }
  }

  @override
  Widget build(BuildContext context) {
    final (background, foreground) = colors(tone, Theme.of(context).brightness);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(color: background, borderRadius: BorderRadius.circular(20)),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (dot) ...[
            Container(width: 6, height: 6, decoration: BoxDecoration(color: foreground, shape: BoxShape.circle)),
            const SizedBox(width: 6),
          ],
          Text(label, style: TextStyle(color: foreground, fontSize: 12, fontWeight: FontWeight.w700, height: 1.3)),
        ],
      ),
    );
  }
}
