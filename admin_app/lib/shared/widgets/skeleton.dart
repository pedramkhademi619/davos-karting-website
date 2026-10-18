import "package:flutter/material.dart";

import "package:davos_admin/core/theme/pit.dart";

/// A shimmering placeholder block. Used instead of spinners: the screen keeps its shape while data loads.
class Skeleton extends StatefulWidget {
  const Skeleton({super.key, this.height = 16, this.width, this.radius = 12});

  final double height;
  final double? width;
  final double radius;

  @override
  State<Skeleton> createState() => _SkeletonState();
}

class _SkeletonState extends State<Skeleton> with SingleTickerProviderStateMixin {
  late final AnimationController _c = AnimationController(vsync: this, duration: const Duration(milliseconds: 1400))..repeat();

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    final base = p.isDark ? const Color(0xFF1B1E26) : const Color(0xFFE9E7DF);
    final glow = p.isDark ? const Color(0xFF272B35) : const Color(0xFFF6F5F0);
    return AnimatedBuilder(
      animation: _c,
      builder: (context, _) => Container(
        height: widget.height,
        width: widget.width,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(widget.radius),
          gradient: LinearGradient(
            begin: Alignment(-1.5 + _c.value * 3, 0),
            end: Alignment(-0.5 + _c.value * 3, 0),
            colors: [base, glow, base],
          ),
        ),
      ),
    );
  }
}

/// A screenful of placeholder cards.
class SkeletonList extends StatelessWidget {
  const SkeletonList({super.key, this.count = 4, this.itemHeight = 96});

  final int count;
  final double itemHeight;

  @override
  Widget build(BuildContext context) => ListView(
    physics: const NeverScrollableScrollPhysics(),
    padding: const EdgeInsets.all(16),
    children: [
      for (var i = 0; i < count; i++)
        Padding(padding: const EdgeInsets.only(bottom: 12), child: Skeleton(height: itemHeight, radius: 22)),
    ],
  );
}
