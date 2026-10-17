import "package:flutter/material.dart";

import "package:davos_admin/core/theme/app_colors.dart";
import "package:davos_admin/core/theme/pit.dart";
import "package:davos_admin/core/utils/fa.dart";
import "package:davos_admin/core/utils/jalali.dart";
import "package:davos_admin/shared/widgets/pressable.dart";

/// A horizontal strip of days (Jalali) around today; the chosen one is amber. Pick any other date with the calendar.
class DayStrip extends StatefulWidget {
  const DayStrip({super.key, required this.selected, required this.onSelect, this.before = 4, this.after = 24});

  final String selected;
  final ValueChanged<String> onSelect;
  final int before;
  final int after;

  @override
  State<DayStrip> createState() => _DayStripState();
}

class _DayStripState extends State<DayStrip> {
  static const _itemWidth = 62.0;
  final ScrollController _scroll = ScrollController();

  late final String _today = businessDayIso();

  List<String> get _days => [for (var i = -widget.before; i <= widget.after; i++) addDaysIso(_today, i)];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _centre());
  }

  @override
  void didUpdateWidget(DayStrip old) {
    super.didUpdateWidget(old);
    if (old.selected != widget.selected) _centre();
  }

  void _centre() {
    final index = _days.indexOf(widget.selected);
    if (index < 0 || !_scroll.hasClients) return;
    final width = MediaQuery.of(context).size.width;
    // RTL: the list starts at the right edge, so the offset grows towards the left.
    final target = (index * _itemWidth - width / 2 + _itemWidth / 2).clamp(0.0, _scroll.position.maxScrollExtent);
    _scroll.animateTo(target, duration: const Duration(milliseconds: 350), curve: Curves.easeOutCubic);
  }

  @override
  void dispose() {
    _scroll.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    final days = _days;
    return SizedBox(
      height: 84,
      child: ListView.builder(
        controller: _scroll,
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        itemCount: days.length,
        itemBuilder: (context, i) {
          final iso = days[i];
          final j = jalaliOfIso(iso);
          final on = iso == widget.selected;
          final isToday = iso == _today;
          return Padding(
            padding: const EdgeInsetsDirectional.only(end: 8),
            child: Pressable(
              onTap: () => widget.onSelect(iso),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                width: _itemWidth - 8,
                decoration: BoxDecoration(
                  gradient: on ? AppColors.amber : null,
                  color: on ? null : p.surface,
                  borderRadius: BorderRadius.circular(18),
                  border: Border.all(color: on ? Colors.transparent : (isToday ? AppColors.accent.withValues(alpha: 0.6) : p.line)),
                ),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(jalaliWeekdays[j.weekDay - 1], style: TextStyle(fontSize: 11.5, color: on ? AppColors.ink.withValues(alpha: 0.75) : p.mid, fontWeight: FontWeight.w500)),
                    const SizedBox(height: 4),
                    Text(fa(j.day), style: TextStyle(fontSize: 21, fontWeight: FontWeight.w700, color: on ? AppColors.ink : p.hi, height: 1.1)),
                    const SizedBox(height: 2),
                    Text(
                      isToday ? "امروز" : jalaliMonths[j.month - 1],
                      style: TextStyle(fontSize: 10.5, color: on ? AppColors.ink.withValues(alpha: 0.75) : (isToday ? p.accentText : p.low), fontWeight: isToday ? FontWeight.w700 : FontWeight.w400),
                    ),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}
