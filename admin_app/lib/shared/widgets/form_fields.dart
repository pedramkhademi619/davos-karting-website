import "package:flutter/material.dart";
import "package:flutter/services.dart";

import "package:davos_admin/core/theme/app_colors.dart";
import "package:davos_admin/core/theme/pit.dart";
import "package:davos_admin/core/utils/fa.dart";
import "package:davos_admin/core/utils/jalali.dart";
import "package:davos_admin/shared/dialog/jalali_date_picker.dart";
import "package:davos_admin/shared/widgets/option_sheet.dart";
import "package:davos_admin/shared/widgets/pressable.dart";

/// Turns typed digits (Persian, Arabic or Latin) into Persian digits with thousands separators as the user types.
class MoneyInputFormatter extends TextInputFormatter {
  @override
  TextEditingValue formatEditUpdate(TextEditingValue old, TextEditingValue next) {
    final digits = latin(next.text).replaceAll(RegExp(r"[^0-9]"), "");
    if (digits.isEmpty) return const TextEditingValue();
    final text = grouped(int.parse(digits));
    return TextEditingValue(text: text, selection: TextSelection.collapsed(offset: text.length));
  }
}

/// Label above a field.
class FieldShell extends StatelessWidget {
  const FieldShell({super.key, required this.label, required this.child});

  final String label;
  final Widget child;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 14),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(bottom: 7, right: 2, left: 2),
          child: Text(label, style: TextStyle(fontWeight: FontWeight.w500, fontSize: 12.5, color: context.pit.mid)),
        ),
        child,
      ],
    ),
  );
}

/// A labelled text box. Use [number] / [money] / [phone] for numeric input.
class LabeledField extends StatelessWidget {
  const LabeledField({
    super.key,
    required this.label,
    required this.controller,
    this.hint,
    this.number = false,
    this.money = false,
    this.phone = false,
    this.password = false,
    this.lines = 1,
    this.suffix,
    this.maxLength,
    this.onSubmitted,
    this.onChanged,
    this.enabled = true,
    this.ltr = false,
    this.autofocus = false,
    this.big = false,
  });

  final String label;
  final TextEditingController controller;
  final String? hint;
  final bool number;
  final bool money;
  final bool phone;
  final bool password;
  final int lines;
  final String? suffix;
  final int? maxLength;
  final ValueChanged<String>? onSubmitted;
  final ValueChanged<String>? onChanged;
  final bool enabled;

  /// Left-to-right text (usernames, English).
  final bool ltr;
  final bool autofocus;

  /// Larger type, for the one field a screen is about (a search box).
  final bool big;

  @override
  Widget build(BuildContext context) {
    final numeric = number || money || phone;
    return FieldShell(
      label: label,
      child: TextField(
        controller: controller,
        enabled: enabled,
        autofocus: autofocus,
        obscureText: password,
        maxLines: password ? 1 : lines,
        minLines: lines > 1 ? 2 : 1,
        maxLength: maxLength,
        style: TextStyle(fontSize: big ? 18 : 14.5, fontWeight: big ? FontWeight.w700 : FontWeight.w400),
        keyboardType: numeric ? TextInputType.number : (lines > 1 ? TextInputType.multiline : TextInputType.text),
        textDirection: (ltr || password) ? TextDirection.ltr : null,
        textAlign: (ltr || password) ? TextAlign.left : TextAlign.start,
        inputFormatters: money ? [MoneyInputFormatter()] : null,
        onSubmitted: onSubmitted,
        onChanged: onChanged,
        decoration: InputDecoration(hintText: hint, suffixText: suffix == null ? null : "  $suffix", counterText: ""),
      ),
    );
  }
}

/// Whole number in a money field -> int.
int moneyValue(TextEditingController controller) => parseInt(controller.text);

/// Tap to pick a Jalali date; the value is an ISO date ("2026-09-26").
class DateField extends StatelessWidget {
  const DateField({super.key, required this.label, required this.value, required this.onChanged, this.clearable = false});

  final String label;
  final String? value;
  final ValueChanged<String?> onChanged;
  final bool clearable;

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    return FieldShell(
      label: label,
      child: Pressable(
        scale: 0.99,
        onTap: () async {
          final picked = await showJalaliDatePicker(context, initialIso: value ?? todayIso());
          if (picked != null) onChanged(picked);
        },
        child: InputDecorator(
          decoration: InputDecoration(
            suffixIcon: clearable && value != null
                ? IconButton(icon: const Icon(Icons.close_rounded, size: 18), onPressed: () => onChanged(null))
                : const Icon(Icons.calendar_month_rounded, size: 20),
          ),
          child: Text(
            value == null ? "انتخاب تاریخ" : "${jalaliWithWeekday(value!)} ${fa(jalaliOfIso(value!).year)}",
            style: TextStyle(color: value == null ? p.low : p.hi, fontSize: 14.5),
          ),
        ),
      ),
    );
  }
}

/// Tap to pick a time of day in 24-hour form; the value is "HH:MM".
class TimeField extends StatelessWidget {
  const TimeField({super.key, required this.label, required this.value, required this.onChanged, this.clearable = false});

  final String label;
  final String? value;
  final ValueChanged<String?> onChanged;
  final bool clearable;

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    return FieldShell(
      label: label,
      child: Pressable(
        scale: 0.99,
        onTap: () async {
          final parts = (value ?? "12:00").split(":");
          final picked = await showTimePicker(
            context: context,
            initialTime: TimeOfDay(hour: int.tryParse(parts[0]) ?? 12, minute: int.tryParse(parts.length > 1 ? parts[1] : "0") ?? 0),
            builder: (context, child) => MediaQuery(
              data: MediaQuery.of(context).copyWith(alwaysUse24HourFormat: true),
              child: Directionality(textDirection: TextDirection.ltr, child: child!),
            ),
          );
          if (picked != null) onChanged("${picked.hour.toString().padLeft(2, "0")}:${picked.minute.toString().padLeft(2, "0")}");
        },
        child: InputDecorator(
          decoration: InputDecoration(
            suffixIcon: clearable && value != null
                ? IconButton(icon: const Icon(Icons.close_rounded, size: 18), onPressed: () => onChanged(null))
                : const Icon(Icons.schedule_rounded, size: 20),
          ),
          child: Text(value == null ? "انتخاب ساعت" : fa(value), style: TextStyle(color: value == null ? p.low : p.hi, fontSize: 14.5)),
        ),
      ),
    );
  }
}

/// A labelled picker: tap to choose from a bottom sheet (searchable when the list is long).
class ChoiceField<T> extends StatelessWidget {
  const ChoiceField({
    super.key,
    required this.label,
    required this.value,
    required this.options,
    required this.onChanged,
    this.hint = "انتخاب کنید",
  });

  final String label;
  final T? value;

  /// value -> text shown
  final Map<T, String> options;
  final ValueChanged<T?> onChanged;
  final String hint;

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    final shown = options.containsKey(value) ? options[value] : null;
    return FieldShell(
      label: label,
      child: Pressable(
        scale: 0.99,
        onTap: () async {
          final picked = await showOptionSheet<T>(context, title: label, options: options, selected: value);
          if (picked != null) onChanged(picked);
        },
        child: InputDecorator(
          decoration: const InputDecoration(suffixIcon: Icon(Icons.unfold_more_rounded, size: 20)),
          child: Text(shown ?? hint, maxLines: 1, overflow: TextOverflow.ellipsis, style: TextStyle(color: shown == null ? p.low : p.hi, fontSize: 14.5)),
        ),
      ),
    );
  }
}

/// A switch with a title and an explanation.
class SwitchRow extends StatelessWidget {
  const SwitchRow({super.key, required this.title, required this.value, required this.onChanged, this.subtitle});

  final String title;
  final String? subtitle;
  final bool value;
  final ValueChanged<bool> onChanged;

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14.5)),
                if (subtitle != null) Padding(padding: const EdgeInsets.only(top: 2), child: Text(subtitle!, style: TextStyle(fontSize: 12, height: 1.7, color: p.mid))),
              ],
            ),
          ),
          const SizedBox(width: 12),
          Switch(value: value, onChanged: (v) {
            HapticFeedback.selectionClick();
            onChanged(v);
          }),
        ],
      ),
    );
  }
}

/// A row of selectable pills (status filter, audience...): the chosen one is amber.
class PillSelector<T> extends StatelessWidget {
  const PillSelector({super.key, required this.options, required this.value, required this.onChanged});

  final Map<T, String> options;
  final T value;
  final ValueChanged<T> onChanged;

  @override
  Widget build(BuildContext context) {
    final p = context.pit;
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: [
          for (final entry in options.entries)
            Padding(
              padding: const EdgeInsetsDirectional.only(end: 8),
              child: Pressable(
                onTap: () => onChanged(entry.key),
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 180),
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 9),
                  decoration: BoxDecoration(
                    color: entry.key == value ? AppColors.accent : p.surface,
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: entry.key == value ? AppColors.accent : p.line),
                  ),
                  child: Text(
                    entry.value,
                    style: TextStyle(
                      color: entry.key == value ? AppColors.ink : p.mid,
                      fontWeight: entry.key == value ? FontWeight.w700 : FontWeight.w500,
                      fontSize: 13,
                    ),
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
