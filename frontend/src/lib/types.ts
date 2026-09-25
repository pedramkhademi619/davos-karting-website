/** Shapes of the API's JSON responses (backend/src/davos/api/schemas). */

export type BookingInfo = {
  online_booking_enabled: boolean;
  payments_enabled: boolean;
  single_capacity: number;
  double_capacity: number;
  normal_single_toman: number;
  normal_double_toman: number;
  holiday_single_toman: number;
  holiday_double_toman: number;
  holiday_weekdays: string[];
  closed_weekdays: string[];
  first_session: string;
  last_session_before: string;
  interval_minutes: number;
  hold_minutes: number;
  min_days_ahead: number;
  max_days_ahead: number;
  max_karts_per_reservation: number;
};

export type BookableDay = {
  date: string;
  date_jalali: string;
  weekday: string;
  is_holiday: boolean;
  single_price_toman: number;
  double_price_toman: number;
};

export type BookingCalendar = {
  online_booking_enabled: boolean;
  payments_enabled: boolean;
  hold_minutes: number;
  max_karts_per_reservation: number;
  days: BookableDay[];
};

export type SessionAvailability = {
  time: string;
  starts_at: string;
  singles_left: number;
  doubles_left: number;
  single_capacity: number;
  double_capacity: number;
  bookable: boolean;
};

export type DayAvailability = {
  date: string;
  date_jalali: string;
  weekday: string;
  is_holiday: boolean;
  is_closed: boolean;
  single_price_toman: number;
  double_price_toman: number;
  sessions: SessionAvailability[];
};

export type ReservationStatus = "held" | "confirmed" | "attended" | "cancelled" | "expired";

export type Reservation = {
  id: string;
  code: string;
  date: string;
  date_jalali: string;
  weekday: string;
  time: string;
  starts_at: string;
  single_count: number;
  double_count: number;
  people: number;
  amount_toman: number;
  status: ReservationStatus;
  source: "online" | "staff";
  contact_name: string;
  contact_mobile: string;
  hold_expires_at: string | null;
  confirmed_at: string | null;
  created_at: string;
  confirmed_late: boolean;
  note: string;
  cancel_reason: string;
};

export type StartPayment = {
  payment_id: string;
  redirect_url: string;
  method: "GET" | "POST";
  form_fields: Record<string, string>;
};

export type PaymentStatusValue =
  | "created"
  | "redirected"
  | "verifying"
  | "unknown"
  | "paid"
  | "failed"
  | "expired"
  | "refund_pending"
  | "reversed";

export type PaymentStatus = {
  payment_id: string;
  status: PaymentStatusValue;
  amount_irr: number | null;
  amount_toman: number | null;
  reference_id: string | null;
  reservation_id: string | null;
};

export type SignedIn = { user_id: string; is_new_user: boolean; expires_at: string; csrf_token: string };
export type Me = { user_id: string; csrf_token: string };
export type OtpRequested = { expires_in_seconds: number; resend_after_seconds: number };

export type Profile = {
  user_id: string;
  mobile: string;
  full_name: string;
  marketing_opt_in: boolean;
  created_at: string;
};

// ---- admin ----

export type AdminRole = "owner" | "staff";

export type AdminMe = { admin_id: string; username: string; display_name: string; role: AdminRole; csrf_token: string };

export type Dashboard = {
  today_confirmed: number;
  today_attended: number;
  today_karts: number;
  today_people: number;
  tomorrow_confirmed: number;
  tomorrow_karts: number;
  month_online_revenue_toman: number;
  month_reservations: number;
  held_now: number;
  sms_credit_toman: number | null;
  payments_enabled: boolean;
  online_booking_enabled: boolean;
};

export type Page<T> = { items: T[]; total: number };

export type ScheduleSettings = {
  online_booking_enabled: boolean;
  shift_start: string;
  shift_end: string;
  interval_minutes: number;
  single_capacity: number;
  double_capacity: number;
  normal_single_toman: number;
  normal_double_toman: number;
  holiday_single_toman: number;
  holiday_double_toman: number;
  holiday_weekdays: number[];
  closed_weekdays: number[];
  holiday_dates: string[];
  closed_dates: string[];
  min_days_ahead: number;
  max_days_ahead: number;
  same_day_lead_minutes: number;
  hold_minutes: number;
  max_karts_per_reservation: number;
  max_active_holds_per_customer: number;
};

export type Customer = {
  user_id: string;
  mobile: string;
  full_name: string;
  status: "active" | "blocked";
  marketing_opt_in: boolean;
  created_at: string;
};

export type AdminPayment = {
  payment_id: string;
  order_ref: string;
  customer_id: string;
  amount_toman: number;
  status: PaymentStatusValue;
  gateway: string;
  gateway_order_id: number | null;
  reference_id: string | null;
  failure_reason: string | null;
  created_at: string;
  updated_at: string;
  settled_at: string | null;
};

export type SmsAccount = {
  provider: string;
  connected: boolean;
  remaining_credit_toman: number | null;
  expires_at: string | null;
};

export type SmsLog = {
  id: string;
  kind: string;
  recipient: string;
  body: string;
  status: string;
  created_at: string;
  updated_at: string;
  sent_by: string;
  error: string;
};

export type SmsSent = { batch_id: string; accepted: number; failed: number; invalid_numbers: string[] };

export type AdminUser = {
  admin_id: string;
  username: string;
  display_name: string;
  role: AdminRole;
  is_active: boolean;
  last_login_at: string | null;
  created_at: string;
};
