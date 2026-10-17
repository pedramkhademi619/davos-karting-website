import "package:flutter/material.dart";
import "package:shamsi_date/shamsi_date.dart";

import "package:davos_admin/core/theme/app_colors.dart";
import "package:davos_admin/core/theme/pit.dart";
import "package:davos_admin/core/utils/fa.dart";
import "package:davos_admin/core/utils/jalali.dart";

/// A Jalali (Persian calendar) date picker. Returns the chosen day as an ISO date, or null when dismissed.
Future<String?> showJalaliDatePicker(BuildContext context, {required String initialIso}) {
  return showDialog<String>(
    context: context,
    builder: (_) => Directionality(
      textDirection: TextDirection.rtl,
      child: Dialog(child: _JalaliPicker(initialIso: initialIso)),
    ),
  );
}

class _JalaliPicker extends StatefulWidget {
  const _JalaliPicker({required this.initialIso});

  final String initialIso;

  @override
  State<_JalaliPicker> createState() => _JalaliPickerState();
}

class _JalaliPickerState extends State<_JalaliPicker> {
  late int _year;
  late int _month;
  late int _selectedDay;
  late int _selectedMonth;
  late int _selectedYear;

  @override
  void initState() {
    super.initState();
    final j = jalaliOfIso(widget.initialIso);
    _year = _selectedYear = j.year;
    _month = _selectedMonth = j.month;
    _selectedDay = j.day;
  }

  void _shift(int delta) {
    setState(() {
      _month += delta;
      if (_month > 12) {
        _month = 1;
        _year++;
      } else if (_month < 1) {
        _month = 12;
        _year--;
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final first = Jalali(_year, _month, 1);
    final length = first.monthLength;
    // weekDay: 1 = Saturday ... 7 = Friday, which is exactly the column order of an Iranian calendar.
    final offset = first.weekDay - 1;
    final today = jalaliOfIso(todayIso());
    final cells = <Widget>[
      for (final name in jalaliWeekdays)
        Center(child: Text(name.substring(0, 1), style: TextStyle(fontWeight: FontWeight.w700, fontSize: 12, color: context.pit.low))),
      for (var i = 0; i < offset; i++) const SizedBox.shrink(),
      for (var day = 1; day <= length; day++) _dayCell(day, today),
    ];
    return Padding(
      padding: const EdgeInsets.all(14),
      child: SizedBox(
        width: 320,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              children: [
                IconButton(icon: const Icon(Icons.chevron_right), onPressed: () => _shift(-1)),
                Expanded(
                  child: Text(
                    "${jalaliMonths[_month - 1]} ${fa(_year)}",
                    textAlign: TextAlign.center,
                    style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 17),
                  ),
                ),
                IconButton(icon: const Icon(Icons.chevron_left), onPressed: () => _shift(1)),
              ],
            ),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                TextButton(onPressed: () => setState(() => _year--), child: const Text("سال قبل")),
                TextButton(onPressed: () => setState(() => _year++), child: const Text("سال بعد")),
              ],
            ),
            GridView.count(
              crossAxisCount: 7,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              mainAxisSpacing: 4,
              crossAxisSpacing: 4,
              children: cells,
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                TextButton(
                  onPressed: () => Navigator.of(context).pop(todayIso()),
                  child: const Text("امروز"),
                ),
                const Spacer(),
                TextButton(onPressed: () => Navigator.of(context).pop(), child: const Text("انصراف")),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _dayCell(int day, Jalali today) {
    final selected = day == _selectedDay && _month == _selectedMonth && _year == _selectedYear;
    final isToday = day == today.day && _month == today.month && _year == today.year;
    return InkWell(
      borderRadius: BorderRadius.circular(10),
      onTap: () => Navigator.of(context).pop(isoOfJalali(Jalali(_year, _month, day))),
      child: Container(
        alignment: Alignment.center,
        decoration: BoxDecoration(
          gradient: selected ? AppColors.amber : null,
          borderRadius: BorderRadius.circular(10),
          border: isToday && !selected ? Border.all(color: AppColors.accent, width: 1.5) : null,
        ),
        child: Text(
          fa(day),
          style: TextStyle(
            color: selected ? AppColors.ink : null,
            fontWeight: selected || isToday ? FontWeight.w700 : FontWeight.w400,
          ),
        ),
      ),
    );
  }
}
