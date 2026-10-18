import "package:davos_admin/shared/models/json_read.dart";
import "package:davos_admin/shared/widgets/status_chip.dart";

/// Payment status values and how they read in Persian.
const Map<String, String> paymentStatusLabels = {
  "created": "ایجاد شده",
  "redirected": "در درگاه",
  "verifying": "در حال تایید",
  "unknown": "نامشخص",
  "paid": "پرداخت شده",
  "failed": "ناموفق",
  "expired": "منقضی",
  "refund_pending": "در انتظار استرداد",
  "reversed": "برگشت خورده",
};

Tone paymentTone(String status) => switch (status) {
  "paid" => Tone.success,
  "failed" || "reversed" => Tone.danger,
  "refund_pending" || "unknown" || "verifying" => Tone.warning,
  _ => Tone.neutral,
};

class AdminPayment {
  const AdminPayment({
    required this.paymentId,
    required this.orderRef,
    required this.amountToman,
    required this.status,
    required this.gateway,
    required this.gatewayOrderId,
    required this.referenceId,
    required this.failureReason,
    required this.createdAt,
    required this.settledAt,
  });

  factory AdminPayment.fromJson(Json j) => AdminPayment(
    paymentId: j.str("payment_id"),
    orderRef: j.str("order_ref"),
    amountToman: j.integer("amount_toman"),
    status: j.str("status"),
    gateway: j.str("gateway"),
    gatewayOrderId: j.integerOrNull("gateway_order_id"),
    referenceId: j.strOrNull("reference_id"),
    failureReason: j.strOrNull("failure_reason"),
    createdAt: j.str("created_at"),
    settledAt: j.strOrNull("settled_at"),
  );

  final String paymentId;
  final String orderRef;
  final int amountToman;
  final String status;
  final String gateway;
  final int? gatewayOrderId;
  final String? referenceId;
  final String? failureReason;
  final String createdAt;
  final String? settledAt;

  String get statusLabel => paymentStatusLabels[status] ?? status;
}

