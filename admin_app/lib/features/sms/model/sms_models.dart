import "package:davos_admin/shared/models/json_read.dart";

class SmsAccount {
  const SmsAccount({required this.provider, required this.connected, required this.remainingCreditToman, required this.expiresAt});

  factory SmsAccount.fromJson(Json j) => SmsAccount(
    provider: j.str("provider"),
    connected: j.flag("connected"),
    remainingCreditToman: j.integerOrNull("remaining_credit_toman"),
    expiresAt: j.strOrNull("expires_at"),
  );

  final String provider;
  final bool connected;
  final int? remainingCreditToman;
  final String? expiresAt;

  String get providerLabel => switch (provider) {
    "kavenegar" => "کاوه‌نگار",
    "recording" => "آزمایشی (ارسال نمی‌شود)",
    "console" => "کنسول (فقط لاگ)",
    _ => provider,
  };
}

class SmsLog {
  const SmsLog({
    required this.id,
    required this.kind,
    required this.recipient,
    required this.body,
    required this.status,
    required this.createdAt,
    required this.sentBy,
    required this.error,
  });

  factory SmsLog.fromJson(Json j) => SmsLog(
    id: j.str("id"),
    kind: j.str("kind"),
    recipient: j.str("recipient"),
    body: j.str("body"),
    status: j.str("status"),
    createdAt: j.str("created_at"),
    sentBy: j.str("sent_by"),
    error: j.str("error"),
  );

  final String id;
  final String kind;
  final String recipient;
  final String body;
  final String status;
  final String createdAt;
  final String sentBy;
  final String error;
}

class SmsSent {
  const SmsSent({required this.batchId, required this.accepted, required this.failed, required this.invalidNumbers});

  factory SmsSent.fromJson(Json j) => SmsSent(
    batchId: j.str("batch_id"),
    accepted: j.integer("accepted"),
    failed: j.integer("failed"),
    invalidNumbers: j.strings("invalid_numbers"),
  );

  final String batchId;
  final int accepted;
  final int failed;
  final List<String> invalidNumbers;
}

const Map<String, String> smsStatusLabels = {
  "queued": "در صف",
  "sent": "ارسال شد",
  "delivered": "رسید",
  "failed": "ناموفق",
  "blocked": "مسدود",
  "unknown": "نامشخص",
};

const Map<String, String> smsKindLabels = {
  "otp": "کد ورود",
  "reservation_confirmed": "تایید رزرو",
  "custom": "دستی",
  "bulk": "گروهی",
};
