import "package:davos_admin/shared/models/json_read.dart";

/// The signed-in staff member (GET /admin/auth/me and the sign-in response).
class AdminMe {
  const AdminMe({
    required this.adminId,
    required this.username,
    required this.displayName,
    required this.role,
    required this.permissions,
    required this.csrfToken,
  });

  factory AdminMe.fromJson(Json json) => AdminMe(
    adminId: json.str("admin_id"),
    username: json.str("username"),
    displayName: json.str("display_name"),
    role: json.str("role"),
    permissions: json.strings("permissions"),
    csrfToken: json.str("csrf_token"),
  );

  final String adminId;
  final String username;
  final String displayName;

  /// "owner" or "staff".
  final String role;

  /// What this person may open; the server enforces the same list on every request.
  final List<String> permissions;
  final String csrfToken;

  bool get isOwner => role == "owner";

  String get roleLabel => isOwner ? "مدیر" : "کارمند";

  String get shownName => displayName.isEmpty ? username : displayName;
}
