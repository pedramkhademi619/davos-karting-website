import "dart:ui";

import "package:flutter/material.dart";

import "package:davos_admin/core/theme/app_colors.dart";
import "package:davos_admin/core/theme/pit.dart";
import "package:davos_admin/shared/widgets/pressable.dart";

class NavItem {
  const NavItem({required this.label, required this.icon, required this.activeIcon});

  final String label;
  final IconData icon;
  final IconData activeIcon;
}

/// The floating bottom bar: frosted glass, rounded, with the main action (sell a ticket) as a raised amber button in the
/// middle. The bar shows only the tabs the signed-in person may open.
class PitNavBar extends StatelessWidget {
  const PitNavBar({super.key, required this.items, required this.index, required this.onSelect, this.onAction});

  final List<NavItem> items;
  final int index;
  final ValueChanged<int> onSelect;

  /// The centre button; null hides it.
  final VoidCallback? onAction;

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    final half = (items.length / 2).ceil();
    final children = <Widget>[];
    for (var i = 0; i < items.length; i++) {
      if (onAction != null && i == half) children.add(_Action(onTap: onAction!));
      children.add(Expanded(child: _Tab(item: items[i], selected: i == index, onTap: () => onSelect(i))));
    }
    if (onAction != null && half >= items.length) children.add(_Action(onTap: onAction!));
    return SafeArea(
      top: false,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(30),
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 22, sigmaY: 22),
            child: Container(
              height: 70,
              padding: const EdgeInsets.symmetric(horizontal: 8),
              decoration: BoxDecoration(
                color: p.raised.withValues(alpha: p.isDark ? 0.82 : 0.9),
                borderRadius: BorderRadius.circular(30),
                border: Border.all(color: p.lineStrong.withValues(alpha: p.isDark ? 0.5 : 0.7)),
                boxShadow: const [BoxShadow(color: Color(0x40000000), blurRadius: 30, offset: Offset(0, 10))],
              ),
              child: Row(children: children),
            ),
          ),
        ),
      ),
    );
  }
}

class _Tab extends StatelessWidget {
  const _Tab({required this.item, required this.selected, required this.onTap});

  final NavItem item;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    return Pressable(
      onTap: onTap,
      scale: 0.92,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 220),
        curve: Curves.easeOut,
        margin: const EdgeInsets.symmetric(vertical: 9, horizontal: 2),
        decoration: BoxDecoration(color: selected ? AppColors.accent.withValues(alpha: 0.14) : Colors.transparent, borderRadius: BorderRadius.circular(20)),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(selected ? item.activeIcon : item.icon, size: 24, color: selected ? AppColors.accent : p.mid),
            const SizedBox(height: 3),
            Text(item.label, style: TextStyle(fontSize: 10.5, fontWeight: selected ? FontWeight.w700 : FontWeight.w500, color: selected ? p.hi : p.mid)),
          ],
        ),
      ),
    );
  }
}

class _Action extends StatelessWidget {
  const _Action({required this.onTap});

  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(horizontal: 6),
    child: Pressable(
      onTap: onTap,
      scale: 0.9,
      child: Container(
        width: 56,
        height: 56,
        decoration: const BoxDecoration(
          gradient: AppColors.amber,
          shape: BoxShape.circle,
          boxShadow: [BoxShadow(color: Color(0x66FFB300), blurRadius: 22, offset: Offset(0, 8))],
        ),
        child: const Icon(Icons.confirmation_number_rounded, color: AppColors.ink, size: 28),
      ),
    ),
  );
}
