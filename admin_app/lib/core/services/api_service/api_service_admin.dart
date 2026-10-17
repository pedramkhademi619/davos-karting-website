part of "api_service.dart";

/// Sign-in, the dashboard and the other small admin areas: customers, payments, SMS, settings, system status, panel users.
extension ApiServiceAdmin on ApiService {
  Future<AdminMe> signIn(String username, String password) async {
    final data = await post(Urls.login, body: {"username": username, "password": password}, signIn: true);
    return AdminMe.fromJson(Map<String, dynamic>.from(data as Map));
  }

  Future<AdminMe> getMe() async =>
      AdminMe.fromJson(Map<String, dynamic>.from(await get(Urls.me) as Map));

  Future<void> signOut() => post(Urls.logout);

  Future<void> changePassword(String current, String next) =>
      post(Urls.changePassword, body: {"current_password": current, "new_password": next});

  Future<DashboardSummary> getDashboard() async =>
      DashboardSummary.fromJson(Map<String, dynamic>.from(await get(Urls.dashboard) as Map));

  // ---- customers ----
  Future<PageResult<Customer>> getCustomers({String q = "", int offset = 0, int limit = 30}) async =>
      PageResult.parse(await get(Urls.customers, query: {"q": q, "offset": offset, "limit": limit}), Customer.fromJson);

  Future<void> setCustomerStatus(String userId, String status) =>
      post("${Urls.customerItem}$userId/status", body: {"status": status});

  // ---- payments ----
  Future<PageResult<AdminPayment>> getPayments({String status = "", String q = "", int offset = 0, int limit = 30}) async =>
      PageResult.parse(
        await get(Urls.payments, query: {"status": status, "q": q, "offset": offset, "limit": limit}),
        AdminPayment.fromJson,
      );

  // ---- sms ----
  Future<SmsAccount> getSmsAccount() async =>
      SmsAccount.fromJson(Map<String, dynamic>.from(await get(Urls.smsAccount) as Map));

  Future<PageResult<SmsLog>> getSmsMessages({int offset = 0, int limit = 30}) async =>
      PageResult.parse(await get(Urls.smsMessages, query: {"offset": offset, "limit": limit}), SmsLog.fromJson);

  Future<SmsSent> sendSms({required String audience, required List<String> numbers, String? day, required String text}) async =>
      SmsSent.fromJson(
        Map<String, dynamic>.from(
          await post(Urls.smsSend, body: {"audience": audience, "numbers": numbers, "day": day, "text": text}) as Map,
        ),
      );

  // ---- booking settings ----
  Future<ScheduleSettings> getScheduleSettings() async =>
      ScheduleSettings.fromJson(Map<String, dynamic>.from(await get(Urls.scheduleSettings) as Map));

  Future<ScheduleSettings> saveScheduleSettings(ScheduleSettings settings) async =>
      ScheduleSettings.fromJson(Map<String, dynamic>.from(await put(Urls.scheduleSettings, body: settings.toJson()) as Map));

  // ---- system status ----
  Future<SystemStatus> getSystemStatus() async =>
      SystemStatus.fromJson(Map<String, dynamic>.from(await get(Urls.systemStatus) as Map));

  // ---- panel users ----
  Future<PermissionCatalog> getPermissionCatalog() async =>
      PermissionCatalog.fromJson(Map<String, dynamic>.from(await get(Urls.usersCatalog) as Map));

  Future<List<PanelUser>> getPanelUsers() async =>
      asJsonList(await get(Urls.users)).map(PanelUser.fromJson).toList();

  Future<void> addPanelUser({
    required String username,
    required String displayName,
    required String password,
    required String role,
    List<String>? permissions,
  }) => post(
    Urls.users,
    body: {"username": username, "display_name": displayName, "password": password, "role": role, "permissions": permissions},
  );

  Future<void> setPanelUserActive(String adminId, bool active) =>
      post("${Urls.userItem}$adminId/active", body: {"is_active": active});

  Future<void> setPanelUserPermissions(String adminId, List<String>? permissions) =>
      put("${Urls.userItem}$adminId/permissions", body: {"permissions": permissions});
}
