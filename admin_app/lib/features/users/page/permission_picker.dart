import "package:flutter/material.dart";

import "package:davos_admin/features/users/model/panel_user.dart";

/// Checkboxes for every permission, with the ready-made presets on top. A permission that includes another (managing
/// includes viewing) ticks the included one too, and unticking the included one unticks what depends on it.
class PermissionPicker extends StatelessWidget {
  const PermissionPicker({super.key, required this.catalog, required this.value, required this.onChanged});

  final PermissionCatalog catalog;
  final List<String> value;
  final ValueChanged<List<String>> onChanged;

  List<String> _toggle(PermissionEntry entry, bool on) {
    final next = {...value};
    if (on) {
      next.add(entry.key);
      var implied = entry.implies;
      while (implied != null) {
        next.add(implied);
        implied = catalog.entries.where((e) => e.key == implied).map((e) => e.implies).firstOrNull;
      }
    } else {
      next.remove(entry.key);
      // Anything that includes this permission cannot stay on without it.
      var changed = true;
      while (changed) {
        changed = false;
        for (final other in catalog.entries) {
          if (other.implies != null && !next.contains(other.implies) && next.remove(other.key)) changed = true;
        }
      }
    }
    return catalog.entries.map((e) => e.key).where(next.contains).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (catalog.presets.isNotEmpty) ...[
          const Text("الگوهای آماده", style: TextStyle(fontWeight: FontWeight.w700)),
          const SizedBox(height: 6),
          Wrap(
            spacing: 8,
            children: [for (final preset in catalog.presets) ActionChip(label: Text(preset.label), onPressed: () => onChanged(preset.permissions))],
          ),
          const SizedBox(height: 12),
        ],
        for (final entry in catalog.entries)
          CheckboxListTile(
            contentPadding: EdgeInsets.zero,
            controlAffinity: ListTileControlAffinity.leading,
            value: value.contains(entry.key),
            title: Text(entry.label, style: const TextStyle(fontWeight: FontWeight.w600)),
            subtitle: entry.description.isEmpty ? null : Text(entry.description, style: const TextStyle(fontSize: 12, height: 1.6)),
            onChanged: (on) => onChanged(_toggle(entry, on ?? false)),
          ),
      ],
    );
  }
}
