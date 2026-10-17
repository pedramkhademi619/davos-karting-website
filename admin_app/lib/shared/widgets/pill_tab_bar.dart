import "package:flutter/material.dart";

import "package:davos_admin/core/theme/pit.dart";

/// Tabs drawn as a sunken track with an amber pill on the chosen one. Use as `AppBar.bottom`.
class PillTabBar extends StatelessWidget implements PreferredSizeWidget {
  const PillTabBar({super.key, required this.tabs, this.scrollable = false});

  final List<String> tabs;
  final bool scrollable;

  @override
  Size get preferredSize => const Size.fromHeight(60);

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 4, 16, 10),
      child: Container(
        height: 46,
        padding: const EdgeInsets.all(4),
        decoration: BoxDecoration(color: p.sunken, borderRadius: BorderRadius.circular(18), border: Border.all(color: p.line)),
        child: TabBar(
          isScrollable: scrollable,
          tabAlignment: scrollable ? TabAlignment.start : TabAlignment.fill,
          indicatorPadding: EdgeInsets.zero,
          splashBorderRadius: BorderRadius.circular(14),
          tabs: [for (final t in tabs) Tab(height: 36, text: t)],
        ),
      ),
    );
  }
}
