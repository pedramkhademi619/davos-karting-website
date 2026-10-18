import "package:flutter/material.dart";

import "package:davos_admin/core/theme/app_colors.dart";
import "package:davos_admin/core/theme/pit.dart";

/// Light and dark themes. The type is Noto Sans Arabic, with a Latin fallback for punctuation.
abstract class AppTheme {
  AppTheme._();

  static const String fontFamily = "noto";
  static const List<String> fontFallback = ["noto_latin"];

  static ThemeData get light => _build(Pit.light, Brightness.light);
  static ThemeData get dark => _build(Pit.dark, Brightness.dark);

  static TextTheme _text(Pit p) {
    TextStyle s(double size, FontWeight w, {Color? color, double height = 1.55}) =>
        TextStyle(fontSize: size, fontWeight: w, color: color ?? p.hi, height: height);
    return TextTheme(
      displayLarge: s(40, FontWeight.w700, height: 1.2),
      displayMedium: s(32, FontWeight.w700, height: 1.2),
      headlineMedium: s(24, FontWeight.w700, height: 1.35),
      titleLarge: s(20, FontWeight.w700, height: 1.4),
      titleMedium: s(16, FontWeight.w700),
      titleSmall: s(14, FontWeight.w700),
      bodyLarge: s(16, FontWeight.w400, height: 1.7),
      bodyMedium: s(14, FontWeight.w400, height: 1.7),
      bodySmall: s(12, FontWeight.w400, color: p.mid),
      labelLarge: s(14, FontWeight.w700),
      labelMedium: s(12, FontWeight.w500, color: p.mid),
      labelSmall: s(11, FontWeight.w500, color: p.mid),
    );
  }

  static ThemeData _build(Pit p, Brightness brightness) {
    final scheme = ColorScheme.fromSeed(seedColor: AppColors.accent, brightness: brightness).copyWith(
      primary: AppColors.accent,
      onPrimary: AppColors.ink,
      secondary: AppColors.accent,
      onSecondary: AppColors.ink,
      error: AppColors.danger,
      surface: p.surface,
      onSurface: p.hi,
      surfaceContainerHighest: p.sunken,
      outline: p.line,
      outlineVariant: p.line,
    );
    final border = OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: BorderSide(color: p.line));
    return ThemeData(
      useMaterial3: true,
      brightness: brightness,
      fontFamily: fontFamily,
      fontFamilyFallback: fontFallback,
      colorScheme: scheme,
      scaffoldBackgroundColor: p.bg,
      canvasColor: p.bg,
      textTheme: _text(p),
      extensions: [p],
      hintColor: p.low,
      splashFactory: InkSparkle.splashFactory,
      highlightColor: Colors.transparent,
      appBarTheme: AppBarTheme(
        backgroundColor: p.bg,
        foregroundColor: p.hi,
        elevation: 0,
        scrolledUnderElevation: 0,
        surfaceTintColor: Colors.transparent,
        centerTitle: false,
        toolbarHeight: 64,
        titleSpacing: 20,
        titleTextStyle: TextStyle(fontFamily: fontFamily, fontWeight: FontWeight.w700, fontSize: 20, color: p.hi),
      ),
      tabBarTheme: TabBarThemeData(
        dividerColor: Colors.transparent,
        indicatorSize: TabBarIndicatorSize.tab,
        indicator: BoxDecoration(color: AppColors.accent, borderRadius: BorderRadius.circular(14)),
        labelColor: AppColors.ink,
        unselectedLabelColor: p.mid,
        labelStyle: const TextStyle(fontFamily: fontFamily, fontWeight: FontWeight.w700, fontSize: 13),
        unselectedLabelStyle: const TextStyle(fontFamily: fontFamily, fontWeight: FontWeight.w500, fontSize: 13),
        overlayColor: const WidgetStatePropertyAll(Colors.transparent),
        labelPadding: const EdgeInsets.symmetric(horizontal: 16),
      ),
      cardTheme: CardThemeData(
        color: p.surface,
        elevation: 0,
        margin: EdgeInsets.zero,
        surfaceTintColor: Colors.transparent,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(22), side: BorderSide(color: p.line)),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: p.sunken,
        border: border,
        enabledBorder: border,
        disabledBorder: border,
        focusedBorder: border.copyWith(borderSide: const BorderSide(color: AppColors.accent, width: 1.6)),
        errorBorder: border.copyWith(borderSide: const BorderSide(color: AppColors.danger)),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 15),
        hintStyle: TextStyle(color: p.low, fontSize: 14),
        suffixStyle: TextStyle(color: p.mid, fontSize: 13),
      ),
      floatingActionButtonTheme: FloatingActionButtonThemeData(
        backgroundColor: AppColors.accent,
        foregroundColor: AppColors.ink,
        elevation: 0,
        highlightElevation: 0,
        extendedTextStyle: const TextStyle(fontFamily: fontFamily, fontWeight: FontWeight.w700, fontSize: 14),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
      ),
      chipTheme: ChipThemeData(
        backgroundColor: p.surface,
        selectedColor: AppColors.accent,
        side: BorderSide(color: p.line),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        labelStyle: TextStyle(fontFamily: fontFamily, color: p.hi, fontWeight: FontWeight.w500, fontSize: 13),
        secondaryLabelStyle: const TextStyle(fontFamily: fontFamily, color: AppColors.ink, fontWeight: FontWeight.w700),
        checkmarkColor: AppColors.ink,
      ),
      dividerTheme: DividerThemeData(color: p.line, space: 1, thickness: 1),
      listTileTheme: ListTileThemeData(iconColor: p.mid, textColor: p.hi),
      dialogTheme: DialogThemeData(
        backgroundColor: p.raised,
        surfaceTintColor: Colors.transparent,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(26)),
        titleTextStyle: TextStyle(fontFamily: fontFamily, fontWeight: FontWeight.w700, fontSize: 18, color: p.hi),
      ),
      bottomSheetTheme: BottomSheetThemeData(
        backgroundColor: p.raised,
        surfaceTintColor: Colors.transparent,
        modalBackgroundColor: p.raised,
        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(30))),
      ),
      switchTheme: SwitchThemeData(
        thumbColor: WidgetStateProperty.resolveWith((s) => s.contains(WidgetState.selected) ? AppColors.ink : p.mid),
        trackColor: WidgetStateProperty.resolveWith((s) => s.contains(WidgetState.selected) ? AppColors.accent : p.sunken),
        trackOutlineColor: WidgetStateProperty.resolveWith((s) => s.contains(WidgetState.selected) ? AppColors.accent : p.lineStrong),
      ),
      checkboxTheme: CheckboxThemeData(
        fillColor: WidgetStateProperty.resolveWith((s) => s.contains(WidgetState.selected) ? AppColors.accent : Colors.transparent),
        checkColor: const WidgetStatePropertyAll(AppColors.ink),
        side: BorderSide(color: p.lineStrong, width: 1.5),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
      ),
      progressIndicatorTheme: const ProgressIndicatorThemeData(color: AppColors.accent),
      snackBarTheme: const SnackBarThemeData(behavior: SnackBarBehavior.floating),
      iconButtonTheme: IconButtonThemeData(style: IconButton.styleFrom(foregroundColor: p.hi)),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: p.accentText,
          textStyle: const TextStyle(fontFamily: fontFamily, fontWeight: FontWeight.w700),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          minimumSize: const Size(0, 52),
          backgroundColor: AppColors.accent,
          foregroundColor: AppColors.ink,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          textStyle: const TextStyle(fontFamily: fontFamily, fontWeight: FontWeight.w700, fontSize: 15),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          minimumSize: const Size(0, 52),
          foregroundColor: p.hi,
          side: BorderSide(color: p.lineStrong),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          textStyle: const TextStyle(fontFamily: fontFamily, fontWeight: FontWeight.w700, fontSize: 15),
        ),
      ),
    );
  }
}
