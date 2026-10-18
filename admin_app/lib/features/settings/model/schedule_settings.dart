import "package:davos_admin/shared/models/json_read.dart";

/// Booking settings and prices (GET/PUT /admin/settings/schedule). Everything the website, the booking page and the AI
/// assistant show comes from here. Weekdays use Python numbering (Monday = 0).
class ScheduleSettings {
  ScheduleSettings({
    required this.onlineBookingEnabled,
    required this.shiftStart,
    required this.shiftEnd,
    required this.morningShiftEnabled,
    required this.morningStart,
    required this.morningEnd,
    required this.juniorWeekdays,
    required this.juniorFrom,
    required this.juniorUntil,
    required this.juniorScope,
    required this.intervalMinutes,
    required this.singleCapacity,
    required this.doubleCapacity,
    required this.normalSingleToman,
    required this.normalDoubleToman,
    required this.holidaySingleToman,
    required this.holidayDoubleToman,
    required this.holidayWeekdays,
    required this.closedWeekdays,
    required this.holidayDates,
    required this.closedDates,
    required this.openDates,
    required this.minDaysAhead,
    required this.maxDaysAhead,
    required this.sameDayLeadMinutes,
    required this.holdMinutes,
    required this.maxKartsPerReservation,
    required this.maxActiveHoldsPerCustomer,
    required this.dailyBookingLimitMode,
    required this.dailyPeopleLimit,
    required this.dailyTicketLimit,
    required this.onlineBookingCutoff,
  });

  factory ScheduleSettings.fromJson(Json j) => ScheduleSettings(
    onlineBookingEnabled: j.flag("online_booking_enabled"),
    shiftStart: j.str("shift_start", "10:00"),
    shiftEnd: j.str("shift_end", "22:00"),
    morningShiftEnabled: j.flag("morning_shift_enabled", true),
    morningStart: j.str("morning_start", "10:00"),
    morningEnd: j.str("morning_end", "14:00"),
    juniorWeekdays: List<int>.from((j["junior_weekdays"] as List?) ?? const [5, 6, 0, 1, 2]),
    juniorFrom: j.str("junior_from", "15:00"),
    juniorUntil: j.str("junior_until", "18:00"),
    juniorScope: j.str("junior_scope", "drivers"),
    intervalMinutes: j.integer("interval_minutes", 30),
    singleCapacity: j.integer("single_capacity"),
    doubleCapacity: j.integer("double_capacity"),
    normalSingleToman: j.integer("normal_single_toman"),
    normalDoubleToman: j.integer("normal_double_toman"),
    holidaySingleToman: j.integer("holiday_single_toman"),
    holidayDoubleToman: j.integer("holiday_double_toman"),
    holidayWeekdays: List<int>.from((j["holiday_weekdays"] as List?) ?? const []),
    closedWeekdays: List<int>.from((j["closed_weekdays"] as List?) ?? const []),
    holidayDates: j.strings("holiday_dates"),
    closedDates: j.strings("closed_dates"),
    openDates: j.strings("open_dates"),
    minDaysAhead: j.integer("min_days_ahead"),
    maxDaysAhead: j.integer("max_days_ahead", 30),
    sameDayLeadMinutes: j.integer("same_day_lead_minutes"),
    holdMinutes: j.integer("hold_minutes", 10),
    maxKartsPerReservation: j.integer("max_karts_per_reservation", 10),
    maxActiveHoldsPerCustomer: j.integer("max_active_holds_per_customer", 1),
    dailyBookingLimitMode: j.str("daily_booking_limit_mode", "none"),
    dailyPeopleLimit: j.integerOrNull("daily_people_limit"),
    dailyTicketLimit: j.integerOrNull("daily_ticket_limit"),
    onlineBookingCutoff: j.strOrNull("online_booking_cutoff"),
  );

  bool onlineBookingEnabled;

  /// The evening shift.
  String shiftStart;
  String shiftEnd;

  /// The morning shift (the owner's default: from 10:00).
  bool morningShiftEnabled;
  String morningStart;
  String morningEnd;

  /// When under-15s may ride; [juniorScope] "drivers" (11-14 year olds driving) or "everyone" (passengers too).
  List<int> juniorWeekdays;
  String juniorFrom;
  String juniorUntil;
  String juniorScope;
  int intervalMinutes;
  int singleCapacity;
  int doubleCapacity;
  int normalSingleToman;
  int normalDoubleToman;
  int holidaySingleToman;
  int holidayDoubleToman;
  List<int> holidayWeekdays;
  List<int> closedWeekdays;
  List<String> holidayDates;
  List<String> closedDates;
  List<String> openDates;
  int minDaysAhead;
  int maxDaysAhead;
  int sameDayLeadMinutes;
  int holdMinutes;
  int maxKartsPerReservation;
  int maxActiveHoldsPerCustomer;

  /// "none", "people", "tickets" or "both".
  String dailyBookingLimitMode;
  int? dailyPeopleLimit;
  int? dailyTicketLimit;

  /// "HH:MM" (Tehran) after which online booking for the same day closes, or null.
  String? onlineBookingCutoff;

  Json toJson() => {
    "online_booking_enabled": onlineBookingEnabled,
    "shift_start": shiftStart,
    "shift_end": shiftEnd,
    "morning_shift_enabled": morningShiftEnabled,
    "morning_start": morningStart,
    "morning_end": morningEnd,
    "junior_weekdays": juniorWeekdays,
    "junior_from": juniorFrom,
    "junior_until": juniorUntil,
    "junior_scope": juniorScope,
    "interval_minutes": intervalMinutes,
    "single_capacity": singleCapacity,
    "double_capacity": doubleCapacity,
    "normal_single_toman": normalSingleToman,
    "normal_double_toman": normalDoubleToman,
    "holiday_single_toman": holidaySingleToman,
    "holiday_double_toman": holidayDoubleToman,
    "holiday_weekdays": holidayWeekdays,
    "closed_weekdays": closedWeekdays,
    "holiday_dates": holidayDates,
    "closed_dates": closedDates,
    "open_dates": openDates,
    "min_days_ahead": minDaysAhead,
    "max_days_ahead": maxDaysAhead,
    "same_day_lead_minutes": sameDayLeadMinutes,
    "hold_minutes": holdMinutes,
    "max_karts_per_reservation": maxKartsPerReservation,
    "max_active_holds_per_customer": maxActiveHoldsPerCustomer,
    "daily_booking_limit_mode": dailyBookingLimitMode,
    "daily_people_limit": dailyBookingLimitMode == "people" || dailyBookingLimitMode == "both" ? dailyPeopleLimit : null,
    "daily_ticket_limit": dailyBookingLimitMode == "tickets" || dailyBookingLimitMode == "both" ? dailyTicketLimit : null,
    "online_booking_cutoff": onlineBookingCutoff,
  };
}
