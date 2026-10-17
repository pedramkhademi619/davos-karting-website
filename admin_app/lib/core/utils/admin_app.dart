import "package:flutter/material.dart";
import "package:flutter_localizations/flutter_localizations.dart";
import "package:get/get.dart";

import "package:davos_admin/core/constants/named_routs.dart";
import "package:davos_admin/core/theme/app_theme.dart";
import "package:davos_admin/core/utils/app_bindings.dart";
import "package:davos_admin/core/utils/theme_controller.dart";
import "package:davos_admin/features/accounting/controller/accounting_data_controller.dart";
import "package:davos_admin/features/accounting/controller/accounting_hub_controller.dart";
import "package:davos_admin/features/accounting/controller/accounting_settings_controller.dart";
import "package:davos_admin/features/accounting/controller/assets_controller.dart";
import "package:davos_admin/features/accounting/controller/budget_controller.dart";
import "package:davos_admin/features/accounting/controller/cash_controller.dart";
import "package:davos_admin/features/accounting/controller/journal_controller.dart";
import "package:davos_admin/features/accounting/controller/reports_controller.dart";
import "package:davos_admin/features/accounting/page/accounting_settings_page.dart";
import "package:davos_admin/features/accounting/page/assets_page.dart";
import "package:davos_admin/features/accounting/page/budget_page.dart";
import "package:davos_admin/features/accounting/page/cash_page.dart";
import "package:davos_admin/features/accounting/page/chart_page.dart";
import "package:davos_admin/features/accounting/page/journal_page.dart";
import "package:davos_admin/features/accounting/page/quick_entry_page.dart";
import "package:davos_admin/features/accounting/page/reports_page.dart";
import "package:davos_admin/features/accounting/page/vendors_page.dart";
import "package:davos_admin/features/assistant/controller/assistant_controller.dart";
import "package:davos_admin/features/assistant/page/assistant_page.dart";
import "package:davos_admin/features/auth/page/change_password_page.dart";
import "package:davos_admin/features/auth/page/login_page.dart";
import "package:davos_admin/features/customers/controller/customers_controller.dart";
import "package:davos_admin/features/customers/page/customers_page.dart";
import "package:davos_admin/features/dashboard/controller/dashboard_controller.dart";
import "package:davos_admin/features/search/controller/ticket_search_controller.dart";
import "package:davos_admin/features/search/page/search_page.dart";
import "package:davos_admin/features/shell/shell_controller.dart";
import "package:davos_admin/features/shell/shell_page.dart";
import "package:davos_admin/features/payments/controller/payments_controller.dart";
import "package:davos_admin/features/payments/page/payments_page.dart";
import "package:davos_admin/features/reservations/controller/reservations_controller.dart";
import "package:davos_admin/features/reservations/page/new_reservation_page.dart";
import "package:davos_admin/features/settings/controller/settings_controller.dart";
import "package:davos_admin/features/settings/page/settings_page.dart";
import "package:davos_admin/features/sms/controller/sms_controller.dart";
import "package:davos_admin/features/sms/page/sms_page.dart";
import "package:davos_admin/features/splash/splash_page.dart";
import "package:davos_admin/features/system/controller/system_controller.dart";
import "package:davos_admin/features/system/page/system_page.dart";
import "package:davos_admin/features/users/controller/users_controller.dart";
import "package:davos_admin/features/users/page/users_page.dart";

/// Root widget: theme, Persian (right-to-left) locale and the route table.
///
/// Every route that has a controller registers it in its own binding, so the controller (and its timers and text
/// fields) is created when the screen opens and disposed when it closes.
class AdminApp extends StatelessWidget {
  const AdminApp({super.key});

  /// The accounting screens share the chart of accounts and the supplier list.
  static void _accountingData() => Get.lazyPut<AccountingDataController>(AccountingDataController.new, fenix: true);

  @override
  Widget build(BuildContext context) {
    final theme = Get.put<ThemeController>(ThemeController(), permanent: true);
    return GetMaterialApp(
      title: "داووس کارتینگ",
      debugShowCheckedModeBanner: false,
      locale: const Locale("fa", "IR"),
      supportedLocales: const [Locale("fa", "IR")],
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,
      themeMode: theme.mode.value,
      defaultTransition: Transition.fade,
      transitionDuration: Durations.medium1,
      initialBinding: AppBindings(),
      initialRoute: NamedRouts.splash,
      // A route that no longer exists restarts through the splash, which decides where the user belongs.
      unknownRoute: GetPage(name: "/unknown", page: () => const SplashPage()),
      getPages: [
        GetPage(name: NamedRouts.splash, page: () => const SplashPage()),
        GetPage(name: NamedRouts.login, page: () => const LoginPage()),
        GetPage(
          name: NamedRouts.home,
          page: () => const ShellPage(),
          binding: BindingsBuilder(() {
            _accountingData();
            Get.put(ShellController());
            Get.lazyPut(TodayController.new);
            Get.lazyPut(ReservationsController.new);
            Get.lazyPut(AccountingHubController.new);
          }),
        ),
        GetPage(name: NamedRouts.search, page: () => const SearchPage(), binding: BindingsBuilder(() => Get.lazyPut(TicketSearchController.new))),
        GetPage(name: NamedRouts.changePassword, page: () => const ChangePasswordPage()),
        GetPage(name: NamedRouts.newReservation, page: () => const NewReservationPage()),
        GetPage(
          name: NamedRouts.customers,
          page: () => const CustomersPage(),
          binding: BindingsBuilder(() => Get.lazyPut(CustomersController.new)),
        ),
        GetPage(
          name: NamedRouts.payments,
          page: () => const PaymentsPage(),
          binding: BindingsBuilder(() => Get.lazyPut(PaymentsController.new)),
        ),
        GetPage(
          name: NamedRouts.sms,
          page: () => const SmsPage(),
          binding: BindingsBuilder(() => Get.lazyPut(SmsController.new)),
        ),
        GetPage(
          name: NamedRouts.assistant,
          page: () => const AssistantPage(),
          binding: BindingsBuilder(() {
            Get.lazyPut(AssistantOverviewController.new);
            Get.lazyPut(AssistantReviewController.new);
            Get.lazyPut(AssistantCacheController.new);
            Get.lazyPut(AssistantKnowledgeController.new);
          }),
        ),
        GetPage(
          name: NamedRouts.settings,
          page: () => const SettingsPage(),
          binding: BindingsBuilder(() => Get.lazyPut(SettingsController.new)),
        ),
        GetPage(
          name: NamedRouts.system,
          page: () => const SystemPage(),
          binding: BindingsBuilder(() => Get.lazyPut(SystemController.new)),
        ),
        GetPage(
          name: NamedRouts.users,
          page: () => const UsersPage(),
          binding: BindingsBuilder(() => Get.lazyPut(UsersController.new)),
        ),
        // ---- accounting ----
        GetPage(name: NamedRouts.accountingQuickEntry, page: () => const QuickEntryPage(), binding: BindingsBuilder(_accountingData)),
        GetPage(
          name: NamedRouts.accountingJournal,
          page: () => const JournalPage(),
          binding: BindingsBuilder(() {
            _accountingData();
            Get.lazyPut(JournalController.new);
          }),
        ),
        GetPage(name: NamedRouts.accountingChart, page: () => const ChartPage(), binding: BindingsBuilder(_accountingData)),
        GetPage(name: NamedRouts.accountingVendors, page: () => const VendorsPage(), binding: BindingsBuilder(_accountingData)),
        GetPage(
          name: NamedRouts.accountingAssets,
          page: () => const AssetsPage(),
          binding: BindingsBuilder(() {
            _accountingData();
            Get.lazyPut(AssetsController.new);
          }),
        ),
        GetPage(
          name: NamedRouts.accountingCash,
          page: () => const CashPage(),
          binding: BindingsBuilder(() => Get.lazyPut(CashController.new)),
        ),
        GetPage(
          name: NamedRouts.accountingBudget,
          page: () => const BudgetPage(),
          binding: BindingsBuilder(() {
            _accountingData();
            Get.lazyPut(BudgetController.new);
          }),
        ),
        GetPage(
          name: NamedRouts.accountingReports,
          page: () => const ReportsPage(),
          binding: BindingsBuilder(() {
            _accountingData();
            Get.lazyPut(ReportsController.new);
          }),
        ),
        GetPage(
          name: NamedRouts.accountingSettings,
          page: () => const AccountingSettingsPage(),
          binding: BindingsBuilder(() => Get.lazyPut(AccountingSettingsController.new)),
        ),
      ],
    );
  }
}
