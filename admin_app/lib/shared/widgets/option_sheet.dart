import "package:flutter/material.dart";

import "package:davos_admin/core/theme/app_colors.dart";
import "package:davos_admin/core/theme/pit.dart";

/// A bottom sheet to pick one option from a list, with a search box when the list is long (account pickers).
Future<T?> showOptionSheet<T>(BuildContext context, {required String title, required Map<T, String> options, T? selected}) {
  return showModalBottomSheet<T>(
    context: context,
    isScrollControlled: true,
    useSafeArea: true,
    showDragHandle: true,
    builder: (_) => Directionality(
      textDirection: TextDirection.rtl,
      child: _OptionSheet<T>(title: title, options: options, selected: selected),
    ),
  );
}

class _OptionSheet<T> extends StatefulWidget {
  const _OptionSheet({required this.title, required this.options, required this.selected});

  final String title;
  final Map<T, String> options;
  final T? selected;

  @override
  State<_OptionSheet<T>> createState() => _OptionSheetState<T>();
}

class _OptionSheetState<T> extends State<_OptionSheet<T>> {
  String _query = "";

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    final entries = widget.options.entries.where((e) => _query.isEmpty || e.value.contains(_query)).toList();
    return DraggableScrollableSheet(
      expand: false,
      initialChildSize: widget.options.length > 7 ? 0.8 : 0.5,
      minChildSize: 0.4,
      maxChildSize: 0.92,
      builder: (context, scroll) => Padding(
        padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 0, 20, 12),
              child: Align(alignment: AlignmentDirectional.centerStart, child: Text(widget.title, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700))),
            ),
            if (widget.options.length > 7)
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
                child: TextField(
                  onChanged: (v) => setState(() => _query = v.trim()),
                  decoration: const InputDecoration(hintText: "جستجو", prefixIcon: Icon(Icons.search_rounded)),
                ),
              ),
            Expanded(
              child: ListView.builder(
                controller: scroll,
                padding: const EdgeInsets.fromLTRB(12, 0, 12, 24),
                itemCount: entries.length,
                itemBuilder: (context, i) {
                  final e = entries[i];
                  final on = e.key == widget.selected;
                  return InkWell(
                    borderRadius: BorderRadius.circular(14),
                    onTap: () => Navigator.of(context).pop(e.key),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
                      margin: const EdgeInsets.only(bottom: 4),
                      decoration: BoxDecoration(
                        color: on ? AppColors.accent.withValues(alpha: 0.14) : null,
                        borderRadius: BorderRadius.circular(14),
                      ),
                      child: Row(
                        children: [
                          Expanded(child: Text(e.value, style: TextStyle(fontWeight: on ? FontWeight.w700 : FontWeight.w500, color: p.hi))),
                          if (on) const Icon(Icons.check_rounded, color: AppColors.accent),
                        ],
                      ),
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}
