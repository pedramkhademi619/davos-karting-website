import "package:flutter/material.dart";

/// Fixed brand and status colours. Surfaces and text change with light/dark, so they live in [Pit] (pit.dart).
abstract class AppColors {
  AppColors._();

  static const Color ink = Color(0xFF0C0D10);

  /// Brand amber, the one colour that says "do this".
  static const Color accent = Color(0xFFFFC400);
  static const Color accentDeep = Color(0xFFFFA000);
  static const Color accentDark = Color(0xFF7A5B10);

  static const Color danger = Color(0xFFFF5C4D);
  static const Color dangerSoft = Color(0xFFFFE5E2);
  static const Color success = Color(0xFF22C26E);
  static const Color successSoft = Color(0xFFDCF6E8);
  static const Color warning = Color(0xFFFFB020);
  static const Color warningSoft = Color(0xFFFFF3C4);
  static const Color info = Color(0xFF4E92FF);
  static const Color infoSoft = Color(0xFFDFEBFF);
  static const Color muted = Color(0xFF8A8C96);

  /// Amber gradient used on primary buttons and hero accents.
  static const LinearGradient amber = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [Color(0xFFFFD43B), Color(0xFFFFB300)],
  );
}
