import "package:davos_admin/shared/models/json_read.dart";
import "package:davos_admin/shared/widgets/status_chip.dart";

const Map<String, String> reservationStatusLabels = {
  "held": "در انتظار پرداخت",
  "confirmed": "قطعی",
  "attended": "حضور یافته",
  "cancelled": "لغو شده",
  "expired": "منقضی",
};

Tone reservationTone(String status) => switch (status) {
  "confirmed" => Tone.info,
  "attended" => Tone.success,
  "held" => Tone.warning,
  "cancelled" || "expired" => Tone.neutral,
  _ => Tone.neutral,
};

/// How a counter sale was paid; "none" for online reservations (paid at the gateway).
const Map<String, String> paymentMethodLabels = {
  "none": "پرداخت نشده",
  "cash": "نقدی",
  "card": "کارتخوان",
  "transfer": "کارت‌به‌کارت",
};

class Reservation {
  const Reservation({
    required this.id,
    required this.code,
    required this.ticketNumber,
    required this.date,
    required this.weekday,
    required this.time,
    required this.singleCount,
    required this.doubleCount,
    required this.people,
    required this.amountToman,
    required this.status,
    required this.source,
    required this.contactName,
    required this.contactMobile,
    required this.holdExpiresAt,
    required this.confirmedAt,
    required this.createdAt,
    required this.confirmedLate,
    required this.note,
    required this.cancelReason,
    required this.paymentMethod,
  });

  factory Reservation.fromJson(Json j) => Reservation(
    id: j.str("id"),
    code: j.str("code"),
    ticketNumber: j.integer("ticket_number"),
    date: j.str("date"),
    weekday: j.str("weekday"),
    time: j.str("time"),
    singleCount: j.integer("single_count"),
    doubleCount: j.integer("double_count"),
    people: j.integer("people"),
    amountToman: j.integer("amount_toman"),
    status: j.str("status"),
    source: j.str("source"),
    contactName: j.str("contact_name"),
    contactMobile: j.str("contact_mobile"),
    holdExpiresAt: j.strOrNull("hold_expires_at"),
    confirmedAt: j.strOrNull("confirmed_at"),
    createdAt: j.str("created_at"),
    confirmedLate: j.flag("confirmed_late"),
    note: j.str("note"),
    cancelReason: j.str("cancel_reason"),
    paymentMethod: j.str("payment_method", "none"),
  );

  final String id;
  final String code;
  final int ticketNumber;
  final String date;
  final String weekday;
  final String time;
  final int singleCount;
  final int doubleCount;
  final int people;
  final int amountToman;
  final String status;

  /// "online" or "staff".
  final String source;
  final String contactName;
  final String contactMobile;
  final String? holdExpiresAt;
  final String? confirmedAt;
  final String createdAt;
  final bool confirmedLate;
  final String note;
  final String cancelReason;
  final String paymentMethod;

  bool get isOnline => source == "online";
  bool get canCancel => status == "held" || status == "confirmed";
  bool get canCheckIn => status == "confirmed";
  String get statusLabel => reservationStatusLabels[status] ?? status;
  int get karts => singleCount + doubleCount;
}

class SessionSlot {
  const SessionSlot({
    required this.time,
    required this.singlesLeft,
    required this.doublesLeft,
    required this.singleCapacity,
    required this.doubleCapacity,
    required this.bookable,
    required this.blocked,
  });

  factory SessionSlot.fromJson(Json j) => SessionSlot(
    time: j.str("time"),
    singlesLeft: j.integer("singles_left"),
    doublesLeft: j.integer("doubles_left"),
    singleCapacity: j.integer("single_capacity"),
    doubleCapacity: j.integer("double_capacity"),
    bookable: j.flag("bookable"),
    blocked: j.flag("blocked"),
  );

  final String time;
  final int singlesLeft;
  final int doublesLeft;
  final int singleCapacity;
  final int doubleCapacity;
  final bool bookable;
  final bool blocked;
}

/// All sessions of one day with free karts (GET /admin/reservations/board).
class DayBoard {
  const DayBoard({
    required this.date,
    required this.weekday,
    required this.isHoliday,
    required this.isClosed,
    required this.singlePriceToman,
    required this.doublePriceToman,
    required this.sessions,
  });

  factory DayBoard.fromJson(Json j) => DayBoard(
    date: j.str("date"),
    weekday: j.str("weekday"),
    isHoliday: j.flag("is_holiday"),
    isClosed: j.flag("is_closed"),
    singlePriceToman: j.integer("single_price_toman"),
    doublePriceToman: j.integer("double_price_toman"),
    sessions: j.list("sessions").map(SessionSlot.fromJson).toList(),
  );

  final String date;
  final String weekday;
  final bool isHoliday;
  final bool isClosed;
  final int singlePriceToman;
  final int doublePriceToman;
  final List<SessionSlot> sessions;
}
