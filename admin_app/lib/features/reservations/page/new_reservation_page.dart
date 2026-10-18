import "package:flutter/material.dart";
import "package:flutter/services.dart";
import "package:get/get.dart";

import "package:davos_admin/core/services/api_service/api_service.dart";
import "package:davos_admin/core/theme/app_colors.dart";
import "package:davos_admin/core/theme/pit.dart";
import "package:davos_admin/core/utils/fa.dart";
import "package:davos_admin/core/utils/jalali.dart";
import "package:davos_admin/features/reservations/model/reservation.dart";
import "package:davos_admin/shared/dialog/jalali_date_picker.dart";
import "package:davos_admin/shared/widgets/app_button.dart";
import "package:davos_admin/shared/widgets/app_card.dart";
import "package:davos_admin/shared/widgets/capacity_ring.dart";
import "package:davos_admin/shared/widgets/form_fields.dart";
import "package:davos_admin/shared/widgets/info_widgets.dart";
import "package:davos_admin/shared/widgets/pressable.dart";
import "package:davos_admin/shared/widgets/skeleton.dart";
import "package:davos_admin/shared/widgets/state_view.dart";
import "package:davos_admin/shared/widgets/ticket_card.dart";

/// Sell a ticket at the counter in one screen: day, session, karts, who paid how. The price follows the karts; the
/// button at the bottom shows the total and issues the ticket.
class NewReservationPage extends StatefulWidget {
  const NewReservationPage({super.key});

  @override
  State<NewReservationPage> createState() => _NewReservationPageState();
}

class _NewReservationPageState extends State<NewReservationPage> {
  late String _date = businessDayIso();
  String? _time;
  DayBoard? _board;
  String? _loadError;
  bool _loading = true;
  int _singles = 0;
  int _doubles = 1;
  String _method = "cash";
  bool _overbook = false;
  bool _editPrice = false;
  final _name = TextEditingController();
  final _phone = TextEditingController();
  final _note = TextEditingController();
  final _amount = TextEditingController();
  bool _busy = false;
  String? _error;
  Reservation? _created;

  @override
  void initState() {
    super.initState();
    final args = Get.arguments;
    if (args is Map) {
      _date = (args["date"] as String?) ?? _date;
      _time = args["time"] as String?;
    }
    _loadBoard();
  }

  @override
  void dispose() {
    _name.dispose();
    _phone.dispose();
    _note.dispose();
    _amount.dispose();
    super.dispose();
  }

  Future<void> _loadBoard({bool keepTime = true}) async {
    setState(() {
      _loading = true;
      _loadError = null;
      if (!keepTime) _time = null;
    });
    try {
      final board = await ApiService().getBoard(_date);
      if (!mounted) return;
      setState(() {
        _board = board;
        if (_time != null && !board.sessions.any((s) => s.time == _time)) _time = null;
      });
    } catch (e) {
      if (mounted) setState(() => _loadError = errorMessage(e));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  int get _suggested => _board == null ? 0 : _singles * _board!.singlePriceToman + _doubles * _board!.doublePriceToman;
  int get _total => _editPrice && _amount.text.trim().isNotEmpty ? parseInt(_amount.text) : _suggested;
  SessionSlot? get _slot => _board?.sessions.where((s) => s.time == _time).firstOrNull;
  bool get _exceeds => _slot != null && (_singles > _slot!.singlesLeft || _doubles > _slot!.doublesLeft);
  bool get _ready => _time != null && _singles + _doubles > 0 && (!_exceeds || _overbook);

  Future<void> _submit() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final created = await ApiService().createCounterReservation(
        date: _date,
        time: _time!,
        singles: _singles,
        doubles: _doubles,
        name: _name.text.trim(),
        mobile: latin(_phone.text.trim()),
        note: _note.text.trim(),
        amountToman: _total,
        allowOverbooking: _overbook,
        paymentMethod: _method,
      );
      HapticFeedback.mediumImpact();
      if (mounted) setState(() => _created = created);
    } catch (e) {
      if (mounted) setState(() => _error = errorMessage(e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  void _again() {
    setState(() {
      _created = null;
      _singles = 0;
      _doubles = 1;
      _name.clear();
      _phone.clear();
      _note.clear();
      _amount.clear();
      _editPrice = false;
      _overbook = false;
    });
    _loadBoard();
  }

  @override
  Widget build(BuildContext context) {
    if (_created != null) return _Success(ticket: _created!, onAgain: _again);
    final p = context.pit;
    return Scaffold(
      appBar: AppBar(title: const Text("فروش بلیت"), leading: const BackButton()),
      body: Column(
        children: [
          Expanded(
            child: ListView(
              padding: const EdgeInsets.fromLTRB(20, 4, 20, 24),
              children: [
                _DayChips(date: _date, onChanged: (v) {
                  _date = v;
                  _loadBoard(keepTime: false);
                }),
                if (_loading && _board == null) const Padding(padding: EdgeInsets.only(top: 20), child: Skeleton(height: 150, radius: 22)),
                if (_loadError != null) SizedBox(height: 260, child: StateView.error(_loadError!, onRetry: _loadBoard)),
                if (_board != null) ...[
                  if (_board!.isHoliday)
                    Padding(padding: const EdgeInsets.only(top: 12), child: MessageBar("این روز تعطیل است؛ قیمت‌ها قیمت روز تعطیل است.", warning: true)),
                  const SectionTitle("سانس"),
                  if (_board!.sessions.isEmpty)
                    const AppCard(child: Text("برای این روز سانسی تعریف نشده است."))
                  else
                    Wrap(
                      spacing: 10,
                      runSpacing: 10,
                      children: [for (final s in _board!.sessions) _SlotTile(slot: s, selected: s.time == _time, onTap: () => setState(() => _time = s.time))],
                    ),
                  const SectionTitle("خودرو"),
                  Row(
                    children: [
                      Expanded(
                        child: _KartCard(
                          title: "تک‌نفره",
                          price: _board!.singlePriceToman,
                          count: _singles,
                          left: _slot?.singlesLeft,
                          onChanged: (v) => setState(() => _singles = v),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: _KartCard(
                          title: "دونفره",
                          price: _board!.doublePriceToman,
                          count: _doubles,
                          left: _slot?.doublesLeft,
                          onChanged: (v) => setState(() => _doubles = v),
                        ),
                      ),
                    ],
                  ),
                  if (_exceeds) ...[
                    const SizedBox(height: 12),
                    AppCard(
                      borderColor: AppColors.warning.withValues(alpha: 0.5),
                      child: SwitchRow(
                        title: "ثبت بیش از ظرفیت",
                        subtitle: "تعداد انتخابی از خودروهای خالی این سانس بیشتر است. فقط وقتی روشن کنید که خودروی اضافه در دسترس است.",
                        value: _overbook,
                        onChanged: (v) => setState(() => _overbook = v),
                      ),
                    ),
                  ],
                  const SectionTitle("پرداخت"),
                  _MethodPicker(value: _method, onChanged: (v) => setState(() => _method = v)),
                  const SectionTitle("مشتری (اختیاری)"),
                  LabeledField(label: "شماره موبایل", controller: _phone, phone: true, hint: "۰۹۱۲۱۲۳۴۵۶۷"),
                  LabeledField(label: "نام", controller: _name),
                  LabeledField(label: "یادداشت", controller: _note, lines: 2),
                  if (_editPrice) LabeledField(label: "مبلغ دلخواه (تومان)", controller: _amount, money: true, onChanged: (_) => setState(() {})),
                  if (_error != null) MessageBar(_error!, error: true),
                ],
              ],
            ),
          ),
          if (_board != null)
            Container(
              padding: EdgeInsets.fromLTRB(20, 14, 20, 14 + MediaQuery.of(context).padding.bottom),
              decoration: BoxDecoration(color: p.raised, border: Border(top: BorderSide(color: p.line))),
              child: Row(
                children: [
                  Expanded(
                    child: Pressable(
                      onTap: () => setState(() => _editPrice = !_editPrice),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Text("مبلغ کل", style: TextStyle(color: p.mid, fontSize: 12)),
                              const SizedBox(width: 4),
                              Icon(Icons.edit_rounded, size: 12, color: p.low),
                            ],
                          ),
                          Text(tomanText(_total), style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w700, height: 1.3)),
                        ],
                      ),
                    ),
                  ),
                  SizedBox(width: 190, child: AppButton(label: "صدور بلیت", icon: Icons.confirmation_number_rounded, onPressed: _ready ? _submit : null, busy: _busy)),
                ],
              ),
            ),
        ],
      ),
    );
  }
}

class _DayChips extends StatelessWidget {
  const _DayChips({required this.date, required this.onChanged});

  final String date;
  final ValueChanged<String> onChanged;

  @override
  Widget build(BuildContext context) {
    final today = businessDayIso();
    final options = {today: "امروز", addDaysIso(today, 1): "فردا", addDaysIso(today, 2): "پس‌فردا"};
    final custom = !options.containsKey(date);
    return PillSelector<String>(
      options: {...options, if (custom) date: jalaliText(date), "pick": "تاریخ دیگر…"},
      value: date,
      onChanged: (v) async {
        if (v == "pick") {
          final picked = await showJalaliDatePicker(context, initialIso: date);
          if (picked != null) onChanged(picked);
        } else {
          onChanged(v);
        }
      },
    );
  }
}

class _SlotTile extends StatelessWidget {
  const _SlotTile({required this.slot, required this.selected, required this.onTap});

  final SessionSlot slot;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    final cap = slot.singleCapacity + slot.doubleCapacity;
    final left = slot.singlesLeft + slot.doublesLeft;
    final share = cap == 0 ? 0.0 : left / cap;
    final color = slot.blocked ? p.low : CapacityRing.colorFor(share);
    return Pressable(
      onTap: slot.blocked ? null : onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        width: 86,
        padding: const EdgeInsets.symmetric(vertical: 11),
        decoration: BoxDecoration(
          gradient: selected ? AppColors.amber : null,
          color: selected ? null : p.surface,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: selected ? Colors.transparent : p.line),
        ),
        child: Column(
          children: [
            Text(fa(slot.time), style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: selected ? AppColors.ink : (slot.blocked ? p.low : p.hi))),
            const SizedBox(height: 6),
            ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: SizedBox(
                width: 52,
                height: 4,
                child: LinearProgressIndicator(value: share.clamp(0, 1), backgroundColor: selected ? AppColors.ink.withValues(alpha: 0.2) : p.sunken, color: selected ? AppColors.ink : color),
              ),
            ),
            const SizedBox(height: 5),
            Text(
              slot.blocked ? "بسته" : (left == 0 ? "پر" : "${fa(left)} خالی"),
              style: TextStyle(fontSize: 11, color: selected ? AppColors.ink.withValues(alpha: 0.75) : p.mid),
            ),
          ],
        ),
      ),
    );
  }
}

class _KartCard extends StatelessWidget {
  const _KartCard({required this.title, required this.price, required this.count, required this.left, required this.onChanged});

  final String title;
  final int price;
  final int count;
  final int? left;
  final ValueChanged<int> onChanged;

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    return AppCard(
      padding: const EdgeInsets.all(14),
      borderColor: count > 0 ? AppColors.accent.withValues(alpha: 0.55) : null,
      child: Column(
        children: [
          Text(title, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15)),
          Text(tomanText(price), style: TextStyle(color: p.mid, fontSize: 12)),
          if (left != null) Text("${fa(left)} خالی", style: TextStyle(color: left == 0 ? AppColors.danger : p.low, fontSize: 11.5)),
          const SizedBox(height: 10),
          Row(
            children: [
              _Step(icon: Icons.remove_rounded, onTap: count > 0 ? () => onChanged(count - 1) : null),
              Expanded(child: Center(child: Text(fa(count), style: const TextStyle(fontSize: 28, fontWeight: FontWeight.w700, height: 1.1)))),
              _Step(icon: Icons.add_rounded, onTap: count < 50 ? () => onChanged(count + 1) : null, filled: true),
            ],
          ),
        ],
      ),
    );
  }
}

class _Step extends StatelessWidget {
  const _Step({required this.icon, required this.onTap, this.filled = false});

  final IconData icon;
  final VoidCallback? onTap;
  final bool filled;

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    return Pressable(
      onTap: onTap,
      child: Opacity(
        opacity: onTap == null ? 0.35 : 1,
        child: Container(
          width: 38,
          height: 38,
          decoration: BoxDecoration(
            color: filled ? AppColors.accent : p.sunken,
            shape: BoxShape.circle,
            border: filled ? null : Border.all(color: p.lineStrong),
          ),
          child: Icon(icon, size: 20, color: filled ? AppColors.ink : p.hi),
        ),
      ),
    );
  }
}

class _MethodPicker extends StatelessWidget {
  const _MethodPicker({required this.value, required this.onChanged});

  final String value;
  final ValueChanged<String> onChanged;

  static const _items = [
    ("cash", "نقد", Icons.payments_rounded),
    ("card", "کارتخوان", Icons.credit_card_rounded),
    ("transfer", "کارت‌به‌کارت", Icons.swap_horiz_rounded),
    ("none", "بعداً", Icons.schedule_rounded),
  ];

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    return Row(
      children: [
        for (final item in _items)
          Expanded(
            child: Padding(
              padding: const EdgeInsetsDirectional.only(end: 8),
              child: Pressable(
                onTap: () => onChanged(item.$1),
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 180),
                  padding: const EdgeInsets.symmetric(vertical: 13),
                  decoration: BoxDecoration(
                    color: value == item.$1 ? AppColors.accent.withValues(alpha: 0.16) : p.surface,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: value == item.$1 ? AppColors.accent : p.line, width: value == item.$1 ? 1.5 : 1),
                  ),
                  child: Column(
                    children: [
                      Icon(item.$3, size: 22, color: value == item.$1 ? AppColors.accent : p.mid),
                      const SizedBox(height: 6),
                      Text(item.$2, style: TextStyle(fontSize: 11.5, fontWeight: value == item.$1 ? FontWeight.w700 : FontWeight.w500, color: value == item.$1 ? p.hi : p.mid)),
                    ],
                  ),
                ),
              ),
            ),
          ),
      ],
    );
  }
}

/// The ticket just issued, with the next step one tap away.
class _Success extends StatelessWidget {
  const _Success({required this.ticket, required this.onAgain});

  final Reservation ticket;
  final VoidCallback onAgain;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            children: [
              const Spacer(),
              TweenAnimationBuilder<double>(
                tween: Tween(begin: 0.4, end: 1),
                duration: const Duration(milliseconds: 600),
                curve: Curves.elasticOut,
                builder: (context, v, child) => Transform.scale(scale: v, child: child),
                child: Container(
                  width: 84,
                  height: 84,
                  decoration: BoxDecoration(shape: BoxShape.circle, color: AppColors.success.withValues(alpha: 0.15), border: Border.all(color: AppColors.success.withValues(alpha: 0.5), width: 2)),
                  child: const Icon(Icons.check_rounded, size: 46, color: AppColors.success),
                ),
              ),
              const SizedBox(height: 18),
              const Text("بلیت صادر شد", style: TextStyle(fontSize: 22, fontWeight: FontWeight.w700)),
              const SizedBox(height: 6),
              Text("${jalaliWithWeekday(ticket.date)} • سانس ${fa(ticket.time)}", style: TextStyle(color: context.pit.mid)),
              const SizedBox(height: 22),
              TicketCard(reservation: ticket),
              const Spacer(),
              AppButton(label: "فروش بعدی", icon: Icons.add_rounded, onPressed: onAgain),
              const SizedBox(height: 10),
              AppButton(label: "بازگشت", outlined: true, onPressed: Get.back),
            ],
          ),
        ),
      ),
    );
  }
}
