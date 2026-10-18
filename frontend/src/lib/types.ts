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
  daily_booking_limit_mode: "none" | "people" | "tickets" | "both";
  daily_people_limit: number | null;
  daily_ticket_limit: number | null;
  online_booking_cutoff: string | null;
  online_booking_cutoff_passed: boolean;
  morning_shift_enabled: boolean;
  morning_first_session: string;
  morning_last_session_before: string;
  /** When under-15s may ride (weekday names as in the calendar); `junior_scope` "everyone" binds back-seat passengers too. */
  junior_weekdays: string[];
  junior_from: string;
  junior_until: string;
  junior_scope: "drivers" | "everyone";
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
  blocked: boolean;
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
  ticket_number: number;
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
  payment_method: "none" | "cash" | "card" | "transfer";
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
export type OtpRequested = {
  expires_in_seconds: number;
  resend_after_seconds: number;
  /** Only from a local development API (DEV_SMS_ECHO_ENABLED): no SMS goes out there, so the code comes back here. */
  dev_code?: string;
};

export type Profile = {
  user_id: string;
  mobile: string;
  full_name: string;
  marketing_opt_in: boolean;
  created_at: string;
};

/** One of the customer's payment attempts (GET /account/payments). */
export type AccountPayment = {
  payment_id: string;
  status: PaymentStatusValue;
  amount_toman: number;
  reference_id: string | null;
  reservation_id: string | null;
  gateway: string;
  created_at: string;
  updated_at: string;
};

/** A device signed in to the customer's account (GET /auth/sessions). */
export type DeviceSession = {
  session_id: string;
  user_agent: string;
  ip_hint: string;
  created_at: string;
  last_seen_at: string;
  is_current: boolean;
};

export type StatusLevel = "ok" | "degraded" | "down" | "disabled" | "test";

export type ServicePart = { label: string; level: StatusLevel; detail: string };

export type ServiceStatus = {
  key: string;
  group: string;
  label: string;
  level: StatusLevel;
  summary: string;
  latency_ms: number | null;
  parts: ServicePart[];
  checked_at: string;
};

export type SystemStatus = { overall: StatusLevel; checked_at: string; services: ServiceStatus[] };

// ---- admin ----

export type AdminRole = "owner" | "staff";

export type AdminMe = {
  admin_id: string;
  username: string;
  display_name: string;
  role: AdminRole;
  /** What this person may open; the server enforces the same list on every request. */
  permissions: string[];
  csrf_token: string;
};

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
  morning_shift_enabled: boolean;
  morning_start: string;
  morning_end: string;
  junior_weekdays: number[];
  junior_from: string;
  junior_until: string;
  junior_scope: "drivers" | "everyone";
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
  open_dates: string[];
  min_days_ahead: number;
  max_days_ahead: number;
  same_day_lead_minutes: number;
  hold_minutes: number;
  max_karts_per_reservation: number;
  max_active_holds_per_customer: number;
  daily_booking_limit_mode: "none" | "people" | "tickets" | "both";
  daily_people_limit: number | null;
  daily_ticket_limit: number | null;
  online_booking_cutoff: string | null;
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
  permissions: string[];
  custom_permissions: boolean;
};

export type PermissionCatalog = {
  entries: { key: string; label: string; description: string; implies: string | null; default_for_staff: boolean }[];
  presets: { key: string; label: string; permissions: string[] }[];
};

export type AssistantOverview = {
  days: number;
  questions: number;
  by_outcome: Record<string, number>;
  served_from_cache: number;
  helpful_votes: number;
  not_helpful_votes: number;
  prompt_tokens: number;
  completion_tokens: number;
  cached_answers_active: number;
  cached_answers_total: number;
  knowledge_entries: number;
};

export type AssistantInteraction = {
  interaction_id: string;
  occurred_at: string;
  outcome: string;
  question_text: string | null;
  answer_text: string | null;
  helpful: boolean | null;
  served_from_cache: boolean;
  tokens: number;
};

export type CachedAnswer = {
  entry_id: string;
  question: string;
  answer: string;
  hit_count: number;
  is_active: boolean;
  is_curated: boolean;
  created_at: string;
  last_used_at: string;
};

export type KnowledgeEntry = {
  entry_id: string;
  source_type: string;
  title: string;
  body: string;
  url: string;
  updated_at: string;
};

export type KnowledgeCatalog = {
  entries: KnowledgeEntry[];
  max_entries: number;
  max_chars: number;
  total_chars: number;
  sent_whole: boolean;
};
