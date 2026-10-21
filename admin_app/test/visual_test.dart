// Renders the main screens to PNG files so they can be looked at (not a pass/fail comparison).
// Run: flutter test test/visual_test.dart --dart-define=SHOTS_DIR=/some/dir
import "dart:io";
import "dart:ui" as ui;

import "package:flutter/material.dart";
import "package:flutter/rendering.dart";
import "package:flutter/services.dart";
import "package:flutter_test/flutter_test.dart";
import "package:get/get.dart";
import "package:get_storage/get_storage.dart";

import "package:davos_admin/core/constants/named_routs.dart";
import "package:davos_admin/core/interceptors/session_interceptor.dart";
import "package:davos_admin/core/services/api_service/api_service.dart";
import "package:davos_admin/core/utils/admin_app.dart";
import "package:davos_admin/features/auth/controller/session_controller.dart";
import "package:davos_admin/features/auth/model/admin_me.dart";
import "package:davos_admin/features/shell/shell_controller.dart";

import "helpers/fake_server.dart";

const _dir = String.fromEnvironment("SHOTS_DIR", defaultValue: "");

Future<void> _loadFonts() async {
  final vazir = FontLoader("noto")
    ..addFont(Future.value(ByteData.sublistView(File("assets/fonts/NotoSansArabic-Regular.ttf").readAsBytesSync())))
    ..addFont(Future.value(ByteData.sublistView(File("assets/fonts/NotoSansArabic-Bold.ttf").readAsBytesSync())));
  await vazir.load();
  final latinFont = FontLoader("noto_latin")
    ..addFont(Future.value(ByteData.sublistView(File("assets/fonts/NotoSans-Regular.ttf").readAsBytesSync())))
    ..addFont(Future.value(ByteData.sublistView(File("assets/fonts/NotoSans-Bold.ttf").readAsBytesSync())));
  await latinFont.load();
  final flutterRoot = Platform.environment["FLUTTER_ROOT"] ?? "${Platform.environment["HOME"]}/tools/flutter";
  final icons = File("$flutterRoot/bin/cache/artifacts/material_fonts/MaterialIcons-Regular.otf");
  if (icons.existsSync()) {
    final loader = FontLoader("MaterialIcons")..addFont(Future.value(ByteData.sublistView(icons.readAsBytesSync())));
    await loader.load();
  }
}

Future<void> _shot(WidgetTester tester, String name) async {
  await tester.pump(const Duration(milliseconds: 600));
  await tester.runAsync(() async {
    final boundary = tester.renderObject<RenderRepaintBoundary>(find.byType(RepaintBoundary).first);
    final image = await boundary.toImage(pixelRatio: 2);
    final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
    File("$_dir/$name.png").writeAsBytesSync(bytes!.buffer.asUint8List());
  });
}

Map<String, FakeResponse> _routes() {
  const base = "/api/v1/admin";
  return {
    "GET $base/dashboard": const FakeResponse({
      "today_confirmed": 14, "today_attended": 6, "today_karts": 22, "today_people": 31, "tomorrow_confirmed": 9,
      "tomorrow_karts": 13, "month_online_revenue_toman": 48500000, "month_reservations": 212, "held_now": 2,
      "sms_credit_toman": 1005500, "payments_enabled": true, "online_booking_enabled": true,
    }),
    "GET $base/reservations/board": FakeResponse({
      "date": "2026-10-16", "weekday": "جمعه", "is_holiday": true, "is_closed": false,
      "single_price_toman": 350000, "double_price_toman": 600000,
      "sessions": [
        for (final e in const [("14:00", 0, 0), ("14:30", 1, 0), ("15:00", 4, 2), ("15:30", 6, 4), ("16:00", 2, 3), ("16:30", 6, 4)])
          {"time": e.$1, "starts_at": "x", "singles_left": e.$2, "doubles_left": e.$3, "single_capacity": 6, "double_capacity": 4, "bookable": true, "blocked": false},
      ],
    }),
    "GET $base/reservations": FakeResponse({
      "total": 4,
      "items": [
        for (final e in const [
          (104, "14:30", "confirmed", "online", "علی رضایی", "09121234567", 1, 2, 5, 1550000, "none", ""),
          (105, "15:00", "attended", "staff", "", "", 0, 1, 2, 600000, "cash", ""),
          (106, "15:00", "held", "online", "سارا محمدی", "09351112233", 2, 0, 2, 700000, "none", ""),
          (103, "14:00", "cancelled", "online", "رضا کریمی", "09127778899", 0, 1, 2, 600000, "none", "تغییر برنامه مشتری"),
        ])
          {
            "id": "r${e.$1}", "code": "AB${e.$1}", "ticket_number": e.$1, "date": "2026-10-16", "date_jalali": "", "weekday": "جمعه",
            "time": e.$2, "starts_at": "x", "single_count": e.$7, "double_count": e.$8, "people": e.$9, "amount_toman": e.$10,
            "status": e.$3, "source": e.$4, "contact_name": e.$5, "contact_mobile": e.$6,
            "hold_expires_at": null, "confirmed_at": "2026-10-15T10:00:00Z", "created_at": "2026-10-15T09:50:00Z",
            "confirmed_late": false, "note": "", "cancel_reason": e.$12, "payment_method": e.$11,
          },
      ],
    }),
    "GET $base/accounting/accounts": const FakeResponse([]),
    "GET $base/accounting/vendors": const FakeResponse([]),
    "GET $base/accounting/reports/dashboard": FakeResponse({
      "cash_irr": 125000000, "bank_irr": 480000000, "pos_irr": 32000000, "gateway_irr": 15000000, "liquid_irr": 652000000,
      "payables_irr": 90000000, "refunds_payable_irr": 0, "vat_balance_irr": 12000000, "today_revenue_irr": 41000000,
      "month_revenue_irr": 485000000, "month_expenses_irr": 210000000, "month_profit_irr": 275000000, "unrecognized_advances_irr": 8000000,
      "trend": [
        for (var i = 0; i < 6; i++) {"key": "1405-0${i + 1}", "revenue_irr": 300000000 + i * 40000000, "expenses_irr": 150000000 + i * 12000000, "profit_irr": 0},
      ],
      "top_expenses": [
        {"account_id": "x", "code": "6101", "name": "حقوق و دستمزد", "group": "", "amount_irr": 90000000},
        {"account_id": "y", "code": "6102", "name": "سوخت و روغن", "group": "", "amount_irr": 41000000},
      ],
    }),
    "GET $base/sms/account": const FakeResponse({"provider": "kavenegar", "connected": true, "remaining_credit_toman": 1005500, "expires_at": null}),
    "GET $base/sms/messages": const FakeResponse({"total": 0, "items": []}),
    "GET $base/settings/schedule": const FakeResponse({
      "online_booking_enabled": true, "shift_start": "10:00", "shift_end": "23:30", "interval_minutes": 30, "single_capacity": 6,
      "double_capacity": 4, "normal_single_toman": 350000, "normal_double_toman": 600000, "holiday_single_toman": 420000,
      "holiday_double_toman": 720000, "holiday_weekdays": [3, 4], "closed_weekdays": [], "holiday_dates": ["2026-10-20"],
      "closed_dates": [], "open_dates": [], "min_days_ahead": 0, "max_days_ahead": 30, "same_day_lead_minutes": 30,
      "hold_minutes": 10, "max_karts_per_reservation": 10, "max_active_holds_per_customer": 1, "daily_booking_limit_mode": "both",
      "daily_people_limit": 80, "daily_ticket_limit": 30,
    }),
    "GET $base/system/status": const FakeResponse({
      "overall": "degraded", "checked_at": "2026-10-16T10:00:00Z",
      "services": [
        {"key": "db", "group": "زیرساخت", "label": "پایگاه داده", "level": "ok", "summary": "متصل و سالم", "latency_ms": 4, "parts": [], "checked_at": "x"},
        {"key": "sms", "group": "سرویس‌های بیرونی", "label": "پیامک", "level": "test", "summary": "در حالت آزمایشی است", "latency_ms": null,
          "parts": [{"label": "سرویس‌دهنده", "level": "test", "detail": "ضبط‌کننده"}], "checked_at": "x"},
      ],
    }),
  };
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUpAll(() async {
    await _loadFonts();
    // GetStorage needs a documents directory; point it at a temp folder.
    final tmp = Directory.systemTemp.createTempSync("davos_admin_test").path;
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger.setMockMethodCallHandler(
      const MethodChannel("plugins.flutter.io/path_provider"),
      (call) async => tmp,
    );
    await GetStorage.init();
    // Secure storage answers "nothing stored", so the splash decides immediately instead of hanging.
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger.setMockMethodCallHandler(
      const MethodChannel("plugins.it_nomads.com/flutter_secure_storage"),
      (call) async => null,
    );
  });

  testWidgets("screens render", (tester) async {
    if (_dir.isEmpty) return;
    tester.view.physicalSize = const Size(390 * 3, 844 * 3);
    tester.view.devicePixelRatio = 3;
    addTearDown(tester.view.reset);
    ApiService().useAdapter(FakeServer(_routes()));
    SessionHolder.clear();

    await tester.pumpWidget(const RepaintBoundary(child: AdminApp()));
    await tester.pump(const Duration(seconds: 1));
    final session = Get.find<SessionController>();
    // The splash waits on real platform channels, which never answer inside a widget test: go straight to the sign-in.
    Get.offAllNamed(NamedRouts.login);
    await tester.pump(const Duration(seconds: 1));
    await _shot(tester, "01_login");

    session.me.value = AdminMe.fromJson(meJson);
    Future<void> open(String route, String name, {int tab = -1, Size? size}) async {
      if (size != null) tester.view.physicalSize = size * 3;
      Get.offAllNamed(route);
      for (var i = 0; i < 6; i++) {
        await tester.pump(const Duration(milliseconds: 500));
      }
      if (tab >= 0) Get.find<ShellController>().open(tab);
      for (var i = 0; i < 6; i++) {
        await tester.pump(const Duration(milliseconds: 500));
      }
      // ignore: avoid_print
      print("SHOT $name route=${Get.currentRoute} me=${session.me.value != null}");
      await _shot(tester, name);
    }

    await open(NamedRouts.home, "02_today", size: const Size(390, 1250));
    await open(NamedRouts.home, "03_reservations", tab: 1, size: const Size(390, 1500));
    await open(NamedRouts.home, "04_finance", tab: 2, size: const Size(390, 1500));
    await open(NamedRouts.home, "05_more", tab: 3, size: const Size(390, 900));
    await open(NamedRouts.newReservation, "06_sell", size: const Size(390, 1250));
    await open(NamedRouts.search, "07_search", size: const Size(390, 844));
    await open(NamedRouts.sms, "08_sms", size: const Size(390, 844));
    await open(NamedRouts.system, "09_system", size: const Size(390, 844));
    Get.changeThemeMode(ThemeMode.dark);
    await open(NamedRouts.home, "10_today_dark", size: const Size(390, 1250));
    await open(NamedRouts.home, "11_reservations_dark", tab: 1, size: const Size(390, 1100));
    await open(NamedRouts.newReservation, "12_sell_dark", size: const Size(390, 1000));
  });
}
