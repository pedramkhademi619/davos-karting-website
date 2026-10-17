/// Persian digits and money formatting. Numbers typed by the user may arrive in Persian or Arabic digits, so every
/// parse goes through [latin] first.
const _persian = "۰۱۲۳۴۵۶۷۸۹";
const _arabic = "٠١٢٣٤٥٦٧٨٩";

/// Any value with Persian digits.
String fa(Object? value) {
  final text = value?.toString() ?? "";
  final out = StringBuffer();
  for (final unit in text.runes) {
    final char = String.fromCharCode(unit);
    final index = "0123456789".indexOf(char);
    out.write(index >= 0 ? _persian[index] : char);
  }
  return out.toString();
}

/// Persian and Arabic digits (and separators) turned into plain ASCII digits.
String latin(String text) {
  final out = StringBuffer();
  for (final unit in text.runes) {
    final char = String.fromCharCode(unit);
    final persian = _persian.indexOf(char);
    final arabic = _arabic.indexOf(char);
    if (persian >= 0) {
      out.write(persian);
    } else if (arabic >= 0) {
      out.write(arabic);
    } else if (char == "٬" || char == "،" || char == ",") {
      continue;
    } else if (char == "٫") {
      out.write(".");
    } else {
      out.write(char);
    }
  }
  return out.toString();
}

/// Whole number typed by the user -> int (0 when empty or not a number).
int parseInt(String text) => int.tryParse(latin(text).trim()) ?? 0;

/// Thousands-grouped number with Persian digits: 1250000 -> ۱٬۲۵۰٬۰۰۰.
String grouped(num value) {
  final negative = value < 0;
  final digits = value.abs().round().toString();
  final out = StringBuffer();
  for (var i = 0; i < digits.length; i++) {
    if (i > 0 && (digits.length - i) % 3 == 0) out.write("٬");
    out.write(digits[i]);
  }
  return "${negative ? "−" : ""}${fa(out)}";
}

/// An amount already in Toman.
String tomanText(num toman) => "${grouped(toman)} تومان";

/// Rial -> Toman. A Rial amount that is not a whole Toman keeps one decimal so no digit is hidden.
String tomanFromIrr(num irr) {
  final value = irr / 10;
  if (value == value.roundToDouble()) return grouped(value);
  final negative = value < 0;
  final fixed = value.abs().toStringAsFixed(1);
  final parts = fixed.split(".");
  return "${negative ? "−" : ""}${grouped(int.parse(parts[0]))}٫${fa(parts[1])}";
}

/// Like [tomanFromIrr] but a zero is a dash (for tables).
String tomanOrDash(num irr) => irr == 0 ? "—" : tomanFromIrr(irr);

/// Rial -> whole Toman for form fields.
int irrToToman(num irr) => (irr / 10).round();

/// 0.5 -> ۰٫۵ ; 10 -> ۱۰
String decimal(num value) {
  final text = value == value.roundToDouble()
      ? value.toInt().toString()
      : value.toString();
  return fa(text.replaceAll(".", "٫"));
}
