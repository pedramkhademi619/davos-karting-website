import "package:flutter/material.dart";

import "package:davos_admin/core/theme/app_colors.dart";

/// The design tokens that change between light and dark ("the pit wall": carbon surfaces, amber highlight).
///
/// Read them with `context.pit`. Colours that mean the same thing in both themes (amber, status colours) are in
/// [AppColors].
@immutable
class Pit extends ThemeExtension<Pit> {
  const Pit({
    required this.bg,
    required this.surface,
    required this.raised,
    required this.sunken,
    required this.line,
    required this.lineStrong,
    required this.hi,
    required this.mid,
    required this.low,
    required this.accentText,
    required this.shadow,
    required this.isDark,
  });

  /// Page background.
  final Color bg;

  /// Cards.
  final Color surface;

  /// Things above cards (sheets, floating bars, dialogs).
  final Color raised;

  /// Inset areas: text fields, tracks of progress bars.
  final Color sunken;
  final Color line;
  final Color lineStrong;

  /// Text, strongest to faintest.
  final Color hi;
  final Color mid;
  final Color low;

  /// Amber that is readable as text on this background.
  final Color accentText;
  final List<BoxShadow> shadow;
  final bool isDark;

  static const dark = Pit(
    bg: Color(0xFF0A0B0E),
    surface: Color(0xFF121419),
    raised: Color(0xFF1A1D24),
    sunken: Color(0xFF0D0E12),
    line: Color(0x1FFFFFFF),
    lineStrong: Color(0x38FFFFFF),
    hi: Color(0xFFF4F4F1),
    mid: Color(0xFFA3A7B3),
    low: Color(0xFF6C7181),
    accentText: AppColors.accent,
    shadow: [],
    isDark: true,
  );

  static const light = Pit(
    bg: Color(0xFFF3F2EE),
    surface: Color(0xFFFFFFFF),
    raised: Color(0xFFFFFFFF),
    sunken: Color(0xFFEFEEE9),
    line: Color(0xFFE5E3DA),
    lineStrong: Color(0xFFC9C6B9),
    hi: Color(0xFF0C0D10),
    mid: Color(0xFF575963),
    low: Color(0xFF8A8C96),
    accentText: AppColors.accentDark,
    shadow: [BoxShadow(color: Color(0x0D101828), blurRadius: 22, spreadRadius: -6, offset: Offset(0, 8))],
    isDark: false,
  );

  @override
  Pit copyWith() => this;

  @override
  Pit lerp(ThemeExtension<Pit>? other, double t) => t < 0.5 ? this : (other as Pit? ?? this);
}

extension PitContext on BuildContext {
  Pit get pit => Theme.of(this).extension<Pit>() ?? Pit.dark;
}
