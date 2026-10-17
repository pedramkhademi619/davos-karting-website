part of "api_service.dart";

/// The accounting module. Amounts come back in Rial (`*_irr`) and go out in Toman (`*_toman`).
extension ApiServiceAccounting on ApiService {
  Json _asJson(Object? data) => Map<String, dynamic>.from(data as Map);

  // ---- chart of accounts ----
  Future<List<Account>> getAccounts() async => asJsonList(await get(Urls.accounts)).map(Account.fromJson).toList();

  Future<void> saveAccount({
    String? id,
    required String code,
    required String name,
    required String type,
    String? parentId,
    required bool isGroup,
    required bool active,
  }) {
    final body = {"code": code, "name": name, "type": type, "parent_id": parentId, "is_group": isGroup, "active": active};
    return id == null ? post(Urls.accounts, body: body) : put("${Urls.accountItem}$id", body: body);
  }

  Future<void> deleteAccount(String id) => delete("${Urls.accountItem}$id");

  // ---- settings, sync, fiscal years ----
  Future<AccountingSettings> getAccountingSettings() async =>
      AccountingSettings.fromJson(_asJson(await get(Urls.accountingSettings)));

  Future<AccountingSettings> saveAccountingSettings(AccountingSettings settings) async =>
      AccountingSettings.fromJson(_asJson(await put(Urls.accountingSettings, body: settings.toJson())));

  /// Books reservations that have no sale entry yet. Returns (sales booked, revenue recognized).
  Future<(int, int)> syncAccounting(String from, String to) async {
    final data = _asJson(await post(Urls.accountingSync, body: {"date_from": from, "date_to": to}));
    return (data.integer("sales_booked"), data.integer("revenue_recognized"));
  }

  Future<bool> isFiscalYearClosed(int year) async => _asJson(await get("${Urls.fiscalYearItem}$year")).flag("closed");

  Future<void> closeFiscalYear(int year) => post("${Urls.fiscalYearItem}$year/close");

  // ---- journal ----
  Future<PageResult<Entry>> getJournal({
    String q = "",
    String? accountId,
    String source = "",
    String? from,
    String? to,
    int offset = 0,
    int limit = 30,
  }) async => PageResult.parse(
    await get(
      Urls.journal,
      query: {"q": q, "account_id": accountId, "source": source, "from": from, "to": to, "offset": offset, "limit": limit},
    ),
    Entry.fromJson,
  );

  Future<Entry> postJournalEntry({
    required String date,
    required String description,
    required bool opening,
    required List<Map<String, dynamic>> lines,
  }) async => Entry.fromJson(
    _asJson(await post(Urls.journal, body: {"date": date, "description": description, "opening": opening, "lines": lines})),
  );

  Future<void> reverseEntry(String id, String reason) => post("${Urls.journalItem}$id/reverse", body: {"reason": reason});

  // ---- quick entries ----
  Future<Entry> recordExpense({
    required String date,
    required int amountToman,
    required String description,
    required String expenseAccountId,
    required int vatToman,
    String? paidFromAccountId,
    String? vendorId,
  }) async => Entry.fromJson(
    _asJson(
      await post(
        Urls.expenses,
        body: {
          "date": date,
          "amount_toman": amountToman,
          "description": description,
          "expense_account_id": expenseAccountId,
          "vat_toman": vatToman,
          "paid_from_account_id": paidFromAccountId,
          "vendor_id": vendorId,
        },
      ),
    ),
  );

  Future<Entry> recordIncome({
    required String date,
    required int amountToman,
    required String description,
    required String revenueAccountId,
    required int vatToman,
    required String depositAccountId,
  }) async => Entry.fromJson(
    _asJson(
      await post(
        Urls.income,
        body: {
          "date": date,
          "amount_toman": amountToman,
          "description": description,
          "revenue_account_id": revenueAccountId,
          "vat_toman": vatToman,
          "deposit_account_id": depositAccountId,
        },
      ),
    ),
  );

  Future<Entry> recordTransfer({
    required String date,
    required int amountToman,
    required String description,
    required String fromAccountId,
    required String toAccountId,
  }) async => Entry.fromJson(
    _asJson(
      await post(
        Urls.transfers,
        body: {
          "date": date,
          "amount_toman": amountToman,
          "description": description,
          "from_account_id": fromAccountId,
          "to_account_id": toAccountId,
        },
      ),
    ),
  );

  /// Pays a supplier (or hands a refund back to a customer when [vendorId] is null).
  Future<Entry> recordPayment({
    required String date,
    required int amountToman,
    required String description,
    required String fromAccountId,
    String? vendorId,
  }) async => Entry.fromJson(
    _asJson(
      await post(
        Urls.vendorPayments,
        body: {
          "date": date,
          "amount_toman": amountToman,
          "description": description,
          "from_account_id": fromAccountId,
          "vendor_id": vendorId,
        },
      ),
    ),
  );

  // ---- vendors ----
  Future<List<Vendor>> getVendors() async => asJsonList(await get(Urls.vendors)).map(Vendor.fromJson).toList();

  Future<void> saveVendor({String? id, required String name, required String phone, required String note, required bool active}) {
    final body = {"name": name, "phone": phone, "note": note, "active": active};
    return id == null ? post(Urls.vendors, body: body) : put("${Urls.vendorItem}$id", body: body);
  }

  // ---- fixed assets ----
  Future<List<Asset>> getAssets() async => asJsonList(await get(Urls.assets)).map(Asset.fromJson).toList();

  Future<void> addAsset({
    required String name,
    required String assetAccountId,
    required int costToman,
    required int salvageToman,
    required String inServiceDate,
    required int lifeMonths,
    required bool postPurchase,
    String? paidFromAccountId,
    String? vendorId,
  }) => post(
    Urls.assets,
    body: {
      "name": name,
      "asset_account_id": assetAccountId,
      "cost_toman": costToman,
      "salvage_toman": salvageToman,
      "in_service_date": inServiceDate,
      "life_months": lifeMonths,
      "post_purchase": postPurchase,
      "paid_from_account_id": paidFromAccountId,
      "vendor_id": vendorId,
    },
  );

  Future<void> disposeAsset(String id) => post("${Urls.assetItem}$id/dispose");

  /// Books one month's depreciation. Returns the total in Rial.
  Future<int> runDepreciation(int year, int month) async =>
      _asJson(await post(Urls.depreciation, body: {"year": year, "month": month})).integer("total_irr");

  // ---- budget ----
  Future<List<BudgetRow>> getBudget(int year, int monthFrom, int monthTo) async =>
      asJsonList(await get(Urls.budget, query: {"year": year, "month_from": monthFrom, "month_to": monthTo}))
          .map(BudgetRow.fromJson)
          .toList();

  Future<void> setBudget({required String accountId, required int year, int? month, required int amountToman}) =>
      put(Urls.budget, body: {"account_id": accountId, "year": year, "month": month, "amount_toman": amountToman});

  // ---- cash ----
  Future<CashState> getCash(String date) async => CashState.fromJson(_asJson(await get(Urls.cash, query: {"date": date})));

  Future<CashClosing> closeCash({required String date, required int countedToman, required String note}) async =>
      CashClosing.fromJson(_asJson(await post(Urls.cash, body: {"date": date, "counted_toman": countedToman, "note": note})));

  // ---- reports ----
  Future<AccountingDashboard> getAccountingDashboard() async =>
      AccountingDashboard.fromJson(_asJson(await get(Urls.reportDashboard)));

  Future<TrialBalance> getTrialBalance(String from, String to) async =>
      TrialBalance.fromJson(_asJson(await get(Urls.reportTrialBalance, query: {"date_from": from, "date_to": to})));

  Future<Ledger> getLedger(String accountId, String from, String to) async => Ledger.fromJson(
    _asJson(await get(Urls.reportLedger, query: {"account_id": accountId, "date_from": from, "date_to": to})),
  );

  Future<IncomeStatement> getIncomeStatement(String from, String to) async =>
      IncomeStatement.fromJson(_asJson(await get(Urls.reportIncomeStatement, query: {"date_from": from, "date_to": to})));

  Future<BalanceSheet> getBalanceSheet(String asOf) async =>
      BalanceSheet.fromJson(_asJson(await get(Urls.reportBalanceSheet, query: {"as_of": asOf})));

  Future<SalesReport> getSalesReport(String from, String to) async =>
      SalesReport.fromJson(_asJson(await get(Urls.reportSales, query: {"date_from": from, "date_to": to})));

  Future<VatReport> getVatReport(String from, String to) async =>
      VatReport.fromJson(_asJson(await get(Urls.reportVat, query: {"date_from": from, "date_to": to})));

  Future<List<StatementLine>> getCashPosition(String asOf) async =>
      asJsonList(await get(Urls.reportCashPosition, query: {"as_of": asOf})).map(StatementLine.fromJson).toList();
}
