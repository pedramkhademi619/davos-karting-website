import "package:flutter/material.dart";

import "package:davos_admin/core/theme/app_colors.dart";
import "package:davos_admin/core/theme/pit.dart";
import "package:davos_admin/shared/widgets/app_card.dart";

/// Heading of a block on a screen: small, calm, with room above it.
class SectionTitle extends StatelessWidget {
  const SectionTitle(this.text, {super.key, this.trailing});

  final String text;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(top: 26, bottom: 12),
    child: Row(
      children: [
        Expanded(
          child: Text(text, style: TextStyle(fontWeight: FontWeight.w700, fontSize: 15, color: context.pit.hi)),
        ),
        ?trailing,
      ],
    ),
  );
}

/// One number with its caption (dashboard tiles).
class StatTile extends StatelessWidget {
  const StatTile({super.key, required this.label, required this.value, this.hint, this.color, this.icon});

  final String label;
  final String value;
  final String? hint;
  final Color? color;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    return AppCard(
      padding: const EdgeInsets.all(14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(label, maxLines: 2, overflow: TextOverflow.ellipsis, style: TextStyle(color: p.mid, fontSize: 12, height: 1.4)),
              ),
              if (icon != null) Icon(icon, size: 17, color: color ?? p.low),
            ],
          ),
          const SizedBox(height: 8),
          FittedBox(
            fit: BoxFit.scaleDown,
            alignment: AlignmentDirectional.centerStart,
            child: Text(value, style: TextStyle(fontSize: 23, fontWeight: FontWeight.w700, color: color ?? p.hi, height: 1.2)),
          ),
          if (hint != null) ...[const SizedBox(height: 2), Text(hint!, style: TextStyle(color: p.low, fontSize: 11))],
        ],
      ),
    );
  }
}

/// A two-column grid of [StatTile]s.
class StatGrid extends StatelessWidget {
  const StatGrid({super.key, required this.tiles, this.height = 98});

  final List<Widget> tiles;
  final double height;

  @override
  Widget build(BuildContext context) => GridView.count(
    crossAxisCount: 2,
    crossAxisSpacing: 12,
    mainAxisSpacing: 12,
    shrinkWrap: true,
    physics: const NeverScrollableScrollPhysics(),
    mainAxisExtent: height,
    children: tiles,
  );
}

/// "label ........ value" line.
class InfoRow extends StatelessWidget {
  const InfoRow(this.label, this.value, {super.key, this.valueColor, this.bold = false});

  final String label;
  final String value;
  final Color? valueColor;
  final bool bold;

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Flexible(flex: 3, child: Text(label, style: TextStyle(color: p.mid, fontSize: 13, height: 1.5))),
          const SizedBox(width: 12),
          Expanded(
            flex: 4,
            child: Text(
              value,
              textAlign: TextAlign.end,
              style: TextStyle(color: valueColor ?? p.hi, fontWeight: bold ? FontWeight.w700 : FontWeight.w500, fontSize: 14, height: 1.5),
            ),
          ),
        ],
      ),
    );
  }
}

/// Inline message for form success, warning and failure.
class MessageBar extends StatelessWidget {
  const MessageBar(this.text, {super.key, this.error = false, this.warning = false});

  final String text;
  final bool error;

  /// Amber instead of green: it works, but something needs attention.
  final bool warning;

  @override
  Widget build(BuildContext context) {
    final color = error ? AppColors.danger : (warning ? AppColors.warning : AppColors.success);
    final icon = error ? Icons.error_rounded : (warning ? Icons.warning_amber_rounded : Icons.check_circle_rounded);
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withValues(alpha: 0.32)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: color, size: 20),
          const SizedBox(width: 10),
          Expanded(
            child: Text(text, style: TextStyle(color: context.pit.hi, fontWeight: FontWeight.w500, height: 1.7, fontSize: 13.5)),
          ),
        ],
      ),
    );
  }
}
