part of "api_service.dart";

/// The accounting module. Amounts come back in Rial (`*_irr`) and go out in Toman (`*_toman`).
extension ApiServiceAccounting on ApiService {
  Json _asJson(Object? data) => Map<String, dynamic>.from(data as Map);

  // ---- accounts: the till, the bank, and the income and expense categories ----
  Future<List<Account>> getAccounts() async => asJsonList(await get(Urls.accounts)).map(Account.fromJson).toList();

  Future<void> saveAccount({String? id, required String code, required String name, required String type, String? parentId, required bool active}) {
    final body = {"code": code, "name": name, "type": type, "parent_id": parentId, "is_group": false, "active": active};
    return id == null ? post(Urls.accounts, body: body) : put("${Urls.accountItem}$id", body: body);
  }

  // ---- the day book ----
  Future<PageResult<Entry>> getJournal({required String from, required String to, required List<String> sources, int offset = 0, int limit = 200}) async =>
      PageResult.parse(
        await get(Urls.journal, query: {"from": from, "to": to, "source": sources.join(","), "offset": offset, "limit": limit}),
        Entry.fromJson,
      );

  /// A two-line manual entry: used for the owner's own money (taking profit out, or putting money in).
  Future<void> postJournalEntry({required String date, required String description, required String debitAccountId, required String creditAccountId, required int amountToman}) =>
      post(
        Urls.journal,
        body: {
          "date": date,
          "description": description,
          "lines": [
            {"account_id": debitAccountId, "debit_toman": amountToman},
            {"account_id": creditAccountId, "credit_toman": amountToman},
          ],
        },
      );

  Future<void> reverseEntry(String id, String reason) => post("${Urls.journalItem}$id/reverse", body: {"reason": reason});

  // ---- everyday entries ----
  Future<void> recordExpense({required String date, required int amountToman, required String description, required String expenseAccountId, required String paidFromAccountId}) =>
      post(
        Urls.expenses,
        body: {
          "date": date,
          "amount_toman": amountToman,
          "description": description,
          "expense_account_id": expenseAccountId,
          "paid_from_account_id": paidFromAccountId,
        },
      );

  Future<void> recordIncome({required String date, required int amountToman, required String description, required String revenueAccountId, required String depositAccountId}) =>
      post(
        Urls.income,
        body: {
          "date": date,
          "amount_toman": amountToman,
          "description": description,
          "revenue_account_id": revenueAccountId,
          "deposit_account_id": depositAccountId,
        },
      );

  Future<void> recordTransfer({required String date, required int amountToman, required String description, required String fromAccountId, required String toAccountId}) =>
      post(
        Urls.transfers,
        body: {"date": date, "amount_toman": amountToman, "description": description, "from_account_id": fromAccountId, "to_account_id": toAccountId},
      );

  /// Hands a cancelled ticket's money back to the customer.
  Future<void> payRefund({required String date, required int amountToman, required String description, required String fromAccountId}) =>
      post(
        Urls.refundPayments,
        body: {"date": date, "amount_toman": amountToman, "description": description, "from_account_id": fromAccountId, "vendor_id": null},
      );

  // ---- the till ----
  Future<CashState> getCash(String date) async => CashState.fromJson(_asJson(await get(Urls.cash, query: {"date": date})));

  Future<CashClosing> closeCash({required String date, required int countedToman, required String note}) async =>
      CashClosing.fromJson(_asJson(await post(Urls.cash, body: {"date": date, "counted_toman": countedToman, "note": note})));

  // ---- reports ----
  Future<AccountingDashboard> getAccountingDashboard() async => AccountingDashboard.fromJson(_asJson(await get(Urls.reportDashboard)));

  Future<IncomeStatement> getIncomeStatement(String from, String to) async =>
      IncomeStatement.fromJson(_asJson(await get(Urls.reportIncomeStatement, query: {"from": from, "to": to})));

  Future<SalesReport> getSalesReport(String from, String to) async =>
      SalesReport.fromJson(_asJson(await get(Urls.reportSales, query: {"from": from, "to": to})));
}
