import "package:flutter/material.dart";

import "package:davos_admin/core/utils/fa.dart";

/// A number that counts up to its value (Persian digits, thousands separators).
class AnimatedCount extends StatelessWidget {
  const AnimatedCount({super.key, required this.value, this.style, this.suffix = "", this.duration = const Duration(milliseconds: 900)});

  final num value;
  final TextStyle? style;
  final String suffix;
  final Duration duration;

  @override
  Widget build(BuildContext context) => TweenAnimationBuilder<double>(
    tween: Tween(begin: 0, end: value.toDouble()),
    duration: duration,
    curve: Curves.easeOutCubic,
    builder: (context, v, _) => Text("${grouped(v.round())}$suffix", style: style),
  );
}
