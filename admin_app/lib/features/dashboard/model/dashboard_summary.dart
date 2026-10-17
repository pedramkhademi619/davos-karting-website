import "package:davos_admin/shared/models/json_read.dart";

/// Today at a glance (GET /admin/dashboard).
class DashboardSummary {
  const DashboardSummary({
    required this.todayConfirmed,
    required this.todayAttended,
    required this.todayKarts,
    required this.todayPeople,
    required this.tomorrowConfirmed,
    required this.tomorrowKarts,
    required this.monthOnlineRevenueToman,
    required this.monthReservations,
    required this.heldNow,
    required this.smsCreditToman,
    required this.paymentsEnabled,
    required this.onlineBookingEnabled,
  });

  factory DashboardSummary.fromJson(Json j) => DashboardSummary(
    todayConfirmed: j.integer("today_confirmed"),
    todayAttended: j.integer("today_attended"),
    todayKarts: j.integer("today_karts"),
    todayPeople: j.integer("today_people"),
    tomorrowConfirmed: j.integer("tomorrow_confirmed"),
    tomorrowKarts: j.integer("tomorrow_karts"),
    monthOnlineRevenueToman: j.integer("month_online_revenue_toman"),
    monthReservations: j.integer("month_reservations"),
    heldNow: j.integer("held_now"),
    smsCreditToman: j.integerOrNull("sms_credit_toman"),
    paymentsEnabled: j.flag("payments_enabled"),
    onlineBookingEnabled: j.flag("online_booking_enabled"),
  );

  final int todayConfirmed;
  final int todayAttended;
  final int todayKarts;
  final int todayPeople;
  final int tomorrowConfirmed;
  final int tomorrowKarts;
  final int monthOnlineRevenueToman;
  final int monthReservations;
  final int heldNow;
  final int? smsCreditToman;
  final bool paymentsEnabled;
  final bool onlineBookingEnabled;
}
