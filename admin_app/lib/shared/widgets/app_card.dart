import "package:flutter/material.dart";

import "package:davos_admin/core/theme/pit.dart";
import "package:davos_admin/shared/widgets/pressable.dart";

/// The basic surface: a rounded card with a hairline border (and a soft shadow in the light theme).
class AppCard extends StatelessWidget {
  const AppCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(16),
    this.onTap,
    this.color,
    this.gradient,
    this.radius = 22,
    this.borderColor,
  });

  final Widget child;
  final EdgeInsetsGeometry padding;
  final VoidCallback? onTap;
  final Color? color;
  final Gradient? gradient;
  final double radius;
  final Color? borderColor;

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    final card = Container(
      width: double.infinity,
      padding: padding,
      decoration: BoxDecoration(
        color: gradient == null ? (color ?? p.surface) : null,
        gradient: gradient,
        borderRadius: BorderRadius.circular(radius),
        border: Border.all(color: borderColor ?? p.line),
        boxShadow: p.shadow,
      ),
      child: child,
    );
    return onTap == null ? card : Pressable(onTap: onTap, scale: 0.985, child: card);
  }
}
