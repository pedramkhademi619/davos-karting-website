import "package:flutter/material.dart";

import "package:davos_admin/core/theme/app_colors.dart";
import "package:davos_admin/core/theme/pit.dart";
import "package:davos_admin/shared/widgets/pressable.dart";

/// The app's button. Primary is the amber gradient (the one main action of a screen); [outlined] is the quiet version;
/// [danger] turns either red. Shows a spinner and ignores taps while [busy].
class AppButton extends StatelessWidget {
  const AppButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.busy = false,
    this.icon,
    this.outlined = false,
    this.danger = false,
    this.expand = true,
    this.small = false,
  });

  final String label;
  final VoidCallback? onPressed;
  final bool busy;
  final IconData? icon;
  final bool outlined;
  final bool danger;
  final bool expand;
  final bool small;

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    final enabled = onPressed != null && !busy;
    final Color foreground;
    BoxDecoration decoration;
    if (outlined) {
      foreground = danger ? AppColors.danger : p.hi;
      decoration = BoxDecoration(
        borderRadius: BorderRadius.circular(small ? 13 : 17),
        border: Border.all(color: danger ? AppColors.danger.withValues(alpha: 0.6) : p.lineStrong),
      );
    } else if (danger) {
      foreground = Colors.white;
      decoration = BoxDecoration(color: AppColors.danger, borderRadius: BorderRadius.circular(small ? 13 : 17));
    } else {
      foreground = AppColors.ink;
      decoration = BoxDecoration(
        gradient: AppColors.amber,
        borderRadius: BorderRadius.circular(small ? 13 : 17),
        boxShadow: p.isDark ? const [BoxShadow(color: Color(0x33FFC400), blurRadius: 22, offset: Offset(0, 8))] : const [],
      );
    }
    final child = busy
        ? SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2.4, color: foreground))
        : Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (icon != null) ...[Icon(icon, size: small ? 17 : 20, color: foreground), const SizedBox(width: 8)],
              Flexible(
                child: Text(
                  label,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(color: foreground, fontWeight: FontWeight.w700, fontSize: small ? 13 : 15),
                ),
              ),
            ],
          );
    final button = Opacity(
      opacity: enabled || busy ? 1 : 0.4,
      child: Container(
        height: small ? 40 : 54,
        padding: EdgeInsets.symmetric(horizontal: small ? 16 : 22),
        alignment: Alignment.center,
        decoration: decoration,
        child: child,
      ),
    );
    final tappable = Pressable(onTap: enabled ? onPressed : null, child: button);
    return expand ? SizedBox(width: double.infinity, child: tappable) : tappable;
  }
}
