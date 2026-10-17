import "package:flutter/material.dart";
import "package:get/get.dart";

import "package:davos_admin/core/utils/fa.dart";
import "package:davos_admin/core/utils/jalali.dart";
import "package:davos_admin/features/auth/controller/session_controller.dart";
import "package:davos_admin/features/settings/controller/settings_controller.dart";
import "package:davos_admin/features/settings/model/schedule_settings.dart";
import "package:davos_admin/shared/dialog/jalali_date_picker.dart";
import "package:davos_admin/shared/widgets/app_button.dart";
import "package:davos_admin/shared/widgets/app_card.dart";
import "package:davos_admin/shared/widgets/form_fields.dart";
import "package:davos_admin/shared/widgets/info_widgets.dart";
import "package:davos_admin/shared/widgets/state_view.dart";

/// Python weekday numbers (Monday = 0), in the order of the Iranian week.
const _week = <int, String>{5: "شنبه", 6: "یکشنبه", 0: "دوشنبه", 1: "سه‌شنبه", 2: "چهارشنبه", 3: "پنجشنبه", 4: "جمعه"};

class SettingsPage extends GetView<SettingsController> {
  const SettingsPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("تنظیمات و قیمت‌ها")),
      body: Obx(() {
        final settings = controller.settings.value;
        final state = StateView.from(
          loading: controller.loading.value,
          isEmpty: settings == null,
          error: controller.error.value,
          emptyMessage: "تنظیماتی نیست.",
          onRetry: controller.reload,
        );
        if (state != null) return state;
        return _SettingsForm(controller: controller, initial: settings!, canEdit: Get.find<SessionController>().isOwner);
      }),
    );
  }
}

class _SettingsForm extends StatefulWidget {
  const _SettingsForm({required this.controller, required this.initial, required this.canEdit});

  final SettingsController controller;
  final ScheduleSettings initial;
  final bool canEdit;

  @override
  State<_SettingsForm> createState() => _SettingsFormState();
}

class _SettingsFormState extends State<_SettingsForm> {
  late ScheduleSettings s;
  late final Map<String, TextEditingController> _numbers;
  bool _busy = false;
  String? _message;
  bool _isError = false;

  @override
  void initState() {
    super.initState();
    s = ScheduleSettings.fromJson(widget.initial.toJson());
    // toJson drops the unused daily limit; keep what the server sent so switching the mode back does not lose it.
    s.dailyPeopleLimit = widget.initial.dailyPeopleLimit;
    s.dailyTicketLimit = widget.initial.dailyTicketLimit;
    String f(int? v) => v == null ? "" : fa(v);
    _numbers = {
      "interval": TextEditingController(text: f(s.intervalMinutes)),
      "single_capacity": TextEditingController(text: f(s.singleCapacity)),
      "double_capacity": TextEditingController(text: f(s.doubleCapacity)),
      "normal_single": TextEditingController(text: grouped(s.normalSingleToman)),
      "normal_double": TextEditingController(text: grouped(s.normalDoubleToman)),
      "holiday_single": TextEditingController(text: grouped(s.holidaySingleToman)),
      "holiday_double": TextEditingController(text: grouped(s.holidayDoubleToman)),
      "min_days": TextEditingController(text: f(s.minDaysAhead)),
      "max_days": TextEditingController(text: f(s.maxDaysAhead)),
      "lead": TextEditingController(text: f(s.sameDayLeadMinutes)),
      "hold": TextEditingController(text: f(s.holdMinutes)),
      "max_karts": TextEditingController(text: f(s.maxKartsPerReservation)),
      "max_holds": TextEditingController(text: f(s.maxActiveHoldsPerCustomer)),
      "people_limit": TextEditingController(text: f(s.dailyPeopleLimit)),
      "ticket_limit": TextEditingController(text: f(s.dailyTicketLimit)),
    };
  }

  @override
  void dispose() {
    for (final c in _numbers.values) {
      c.dispose();
    }
    super.dispose();
  }

  int _n(String key) => parseInt(_numbers[key]!.text);

  Future<void> _save() async {
    s
      ..intervalMinutes = _n("interval")
      ..singleCapacity = _n("single_capacity")
      ..doubleCapacity = _n("double_capacity")
      ..normalSingleToman = _n("normal_single")
      ..normalDoubleToman = _n("normal_double")
      ..holidaySingleToman = _n("holiday_single")
      ..holidayDoubleToman = _n("holiday_double")
      ..minDaysAhead = _n("min_days")
      ..maxDaysAhead = _n("max_days")
      ..sameDayLeadMinutes = _n("lead")
      ..holdMinutes = _n("hold")
      ..maxKartsPerReservation = _n("max_karts")
      ..maxActiveHoldsPerCustomer = _n("max_holds")
      ..dailyPeopleLimit = _numbers["people_limit"]!.text.trim().isEmpty ? null : _n("people_limit")
      ..dailyTicketLimit = _numbers["ticket_limit"]!.text.trim().isEmpty ? null : _n("ticket_limit");
    setState(() {
      _busy = true;
      _message = null;
    });
    final error = await widget.controller.save(s);
    if (!mounted) return;
    setState(() {
      _busy = false;
      _isError = error != null;
      _message = error ?? "ذخیره شد. سایت، صفحه رزرو و دستیار هوشمند از همین حالا (حداکثر ۳۰ ثانیه) با این تنظیمات کار می‌کنند.";
    });
  }

  Widget _num(String label, String key, {bool money = false, String? suffix}) =>
      LabeledField(label: label, controller: _numbers[key]!, number: !money, money: money, suffix: suffix);

  Widget _days(String title, List<int> selected) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(title, style: const TextStyle(fontWeight: FontWeight.w600)),
      const SizedBox(height: 6),
      Wrap(
        spacing: 8,
        runSpacing: 4,
        children: [
          for (final entry in _week.entries)
            FilterChip(
              label: Text(entry.value),
              selected: selected.contains(entry.key),
              onSelected: widget.canEdit
                  ? (on) => setState(() => on ? selected.add(entry.key) : selected.remove(entry.key))
                  : null,
            ),
        ],
      ),
    ],
  );

  Widget _dates(String title, String hint, List<String> dates) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(title, style: const TextStyle(fontWeight: FontWeight.w600)),
      Text(hint, style: TextStyle(fontSize: 12, height: 1.6, color: Theme.of(context).hintColor)),
      Wrap(
        spacing: 8,
        children: [
          for (final date in dates)
            InputChip(
              label: Text(jalaliLong(date)),
              onDeleted: widget.canEdit ? () => setState(() => dates.remove(date)) : null,
            ),
          if (widget.canEdit)
            ActionChip(
              avatar: const Icon(Icons.add, size: 16),
              label: const Text("افزودن تاریخ"),
              onPressed: () async {
                final picked = await showJalaliDatePicker(context, initialIso: todayIso());
                if (picked != null && !dates.contains(picked)) setState(() => dates..add(picked)..sort());
              },
            ),
        ],
      ),
      const SizedBox(height: 12),
    ],
  );

  @override
  Widget build(BuildContext context) {
    final people = s.dailyBookingLimitMode == "people" || s.dailyBookingLimitMode == "both";
    final tickets = s.dailyBookingLimitMode == "tickets" || s.dailyBookingLimitMode == "both";
    return AbsorbPointer(
      absorbing: !widget.canEdit,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (!widget.canEdit) const MessageBar("تغییر تنظیمات فقط برای مدیر ممکن است."),
          AppCard(
            child: SwitchRow(
              title: "رزرو آنلاین فعال باشد",
              subtitle: "با خاموش کردن، سایت دیگر رزرو جدید نمی‌پذیرد.",
              value: s.onlineBookingEnabled,
              onChanged: (v) => setState(() => s.onlineBookingEnabled = v),
            ),
          ),
          const SectionTitle("سانس‌ها و خودروها"),
          AppCard(
            child: Column(
              children: [
                TimeField(label: "شروع اولین سانس", value: s.shiftStart, onChanged: (v) => setState(() => s.shiftStart = v ?? s.shiftStart)),
                TimeField(label: "پایان سانس‌ها (بعد از نیمه‌شب هم مجاز)", value: s.shiftEnd, onChanged: (v) => setState(() => s.shiftEnd = v ?? s.shiftEnd)),
                _num("فاصلهٔ سانس‌ها", "interval", suffix: "دقیقه"),
                _num("تعداد خودروی تک‌نفره هر سانس", "single_capacity"),
                _num("تعداد خودروی دونفره هر سانس", "double_capacity"),
              ],
            ),
          ),
          const SectionTitle("قیمت‌ها"),
          AppCard(
            child: Column(
              children: [
                _num("تک‌نفره، روز عادی", "normal_single", money: true, suffix: "تومان"),
                _num("دونفره، روز عادی", "normal_double", money: true, suffix: "تومان"),
                _num("تک‌نفره، روز تعطیل", "holiday_single", money: true, suffix: "تومان"),
                _num("دونفره، روز تعطیل", "holiday_double", money: true, suffix: "تومان"),
              ],
            ),
          ),
          const SectionTitle("روزهای هفته"),
          AppCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _days("روزهای تعطیل (قیمت تعطیل)", s.holidayWeekdays),
                const SizedBox(height: 14),
                _days("روزهای بدون رزرو آنلاین", s.closedWeekdays),
                const SizedBox(height: 6),
                Text(
                  "برداشتن یک روز از این فهرست، همهٔ آن روزهای هفته را باز می‌کند. برای باز کردن فقط یک تاریخ مشخص از «روزهای باز استثنایی» پایین استفاده کنید.",
                  style: TextStyle(fontSize: 12, height: 1.7, color: Theme.of(context).hintColor),
                ),
              ],
            ),
          ),
          const SectionTitle("تاریخ‌های خاص"),
          AppCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _dates("تعطیلی‌های خاص", "این تاریخ‌ها با قیمت تعطیل حساب می‌شوند.", s.holidayDates),
                _dates("روزهای بسته", "در این تاریخ‌ها رزرو آنلاین بسته است.", s.closedDates),
                _dates("روزهای باز استثنایی", "این تاریخ‌ها حتی اگر روز هفته‌شان بسته باشد برای رزرو باز می‌شوند.", s.openDates),
              ],
            ),
          ),
          const SectionTitle("قوانین رزرو"),
          AppCard(
            child: Column(
              children: [
                _num("حداقل فاصله تا روز رزرو", "min_days", suffix: "روز"),
                _num("حداکثر فاصله تا روز رزرو", "max_days", suffix: "روز"),
                _num("رزرو همان روز، حداقل زمان قبل از سانس", "lead", suffix: "دقیقه"),
                _num("مهلت پرداخت", "hold", suffix: "دقیقه"),
                _num("حداکثر خودرو در هر رزرو", "max_karts"),
                _num("حداکثر رزرو در انتظار پرداخت برای هر مشتری", "max_holds"),
                TimeField(
                  label: "بسته شدن رزرو آنلاین همان روز",
                  value: s.onlineBookingCutoff,
                  clearable: true,
                  onChanged: (v) => setState(() => s.onlineBookingCutoff = v),
                ),
              ],
            ),
          ),
          const SectionTitle("محدودیت رزرو آنلاین در روز"),
          AppCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  "اگر همه‌چیز آنلاین رزرو شود، جایی برای مشتری حضوری نمی‌ماند. با این محدودیت، از یک تعداد مشخص به بعد در هر روز رزرو آنلاین بسته می‌شود؛ رزرو حضوری همچنان آزاد است.",
                  style: TextStyle(fontSize: 13, height: 1.8, color: Theme.of(context).hintColor),
                ),
                const SizedBox(height: 10),
                PillSelector<String>(
                  options: const {"none": "بدون محدودیت", "people": "تعداد نفرات", "tickets": "تعداد تیکت", "both": "ترکیبی"},
                  value: s.dailyBookingLimitMode,
                  onChanged: (v) => setState(() => s.dailyBookingLimitMode = v),
                ),
                const SizedBox(height: 12),
                if (people) _num("سقف نفرات آنلاین در روز", "people_limit"),
                if (tickets) _num("سقف تیکت آنلاین در روز", "ticket_limit"),
                if (s.dailyBookingLimitMode == "both")
                  const Text("در حالت ترکیبی، هرکدام از دو سقف زودتر پر شود رزرو آنلاین آن روز بسته می‌شود.", style: TextStyle(fontSize: 12, height: 1.7)),
              ],
            ),
          ),
          const SizedBox(height: 16),
          if (_message != null) MessageBar(_message!, error: _isError),
          if (widget.canEdit) AppButton(label: "ذخیرهٔ تنظیمات", onPressed: _save, busy: _busy),
          const SizedBox(height: 24),
        ],
      ),
    );
  }
}
