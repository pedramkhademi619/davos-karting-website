import "package:davos_admin/shared/models/json_read.dart";

class PanelUser {
  const PanelUser({
    required this.adminId,
    required this.username,
    required this.displayName,
    required this.role,
    required this.isActive,
    required this.lastLoginAt,
    required this.permissions,
    required this.customPermissions,
  });

  factory PanelUser.fromJson(Json j) => PanelUser(
    adminId: j.str("admin_id"),
    username: j.str("username"),
    displayName: j.str("display_name"),
    role: j.str("role"),
    isActive: j.flag("is_active"),
    lastLoginAt: j.strOrNull("last_login_at"),
    permissions: j.strings("permissions"),
    customPermissions: j.flag("custom_permissions"),
  );

  final String adminId;
  final String username;
  final String displayName;
  final String role;
  final bool isActive;
  final String? lastLoginAt;
  final List<String> permissions;

  /// False while the person simply has the staff defaults.
  final bool customPermissions;

  bool get isOwner => role == "owner";
  String get shownName => displayName.isEmpty ? username : displayName;
}

class PermissionEntry {
  const PermissionEntry({
    required this.key,
    required this.label,
    required this.description,
    required this.implies,
    required this.defaultForStaff,
  });

  factory PermissionEntry.fromJson(Json j) => PermissionEntry(
    key: j.str("key"),
    label: j.str("label"),
    description: j.str("description"),
    implies: j.strOrNull("implies"),
    defaultForStaff: j.flag("default_for_staff"),
  );

  final String key;
  final String label;
  final String description;

  /// The permission this one includes (manage includes view).
  final String? implies;
  final bool defaultForStaff;
}

class PermissionPreset {
  const PermissionPreset({required this.key, required this.label, required this.permissions});

  factory PermissionPreset.fromJson(Json j) =>
      PermissionPreset(key: j.str("key"), label: j.str("label"), permissions: j.strings("permissions"));

  final String key;
  final String label;
  final List<String> permissions;
}

class PermissionCatalog {
  const PermissionCatalog({required this.entries, required this.presets});

  factory PermissionCatalog.fromJson(Json j) => PermissionCatalog(
    entries: j.list("entries").map(PermissionEntry.fromJson).toList(),
    presets: j.list("presets").map(PermissionPreset.fromJson).toList(),
  );

  final List<PermissionEntry> entries;
  final List<PermissionPreset> presets;
}
