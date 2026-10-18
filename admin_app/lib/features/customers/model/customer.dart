import "package:davos_admin/shared/models/json_read.dart";

class Customer {
  const Customer({
    required this.userId,
    required this.mobile,
    required this.fullName,
    required this.status,
    required this.marketingOptIn,
    required this.createdAt,
  });

  factory Customer.fromJson(Json j) => Customer(
    userId: j.str("user_id"),
    mobile: j.str("mobile"),
    fullName: j.str("full_name"),
    status: j.str("status"),
    marketingOptIn: j.flag("marketing_opt_in"),
    createdAt: j.str("created_at"),
  );

  final String userId;
  final String mobile;
  final String fullName;

  /// "active" or "blocked".
  final String status;
  final bool marketingOptIn;
  final String createdAt;

  bool get blocked => status == "blocked";
}
