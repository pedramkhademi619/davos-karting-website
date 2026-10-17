import "package:davos_admin/shared/models/json_read.dart";

/// All amounts from the accounting API are Rial (`*_irr`); requests take Toman (`*_toman`).
const Map<String, String> accountTypeLabels = {
  "asset": "دارایی",
  "liability": "بدهی",
  "equity": "حقوق صاحبان سرمایه",
  "revenue": "درآمد",
  "expense": "هزینه",
};

const Map<String, String> entrySourceLabels = {
  "manual": "سند دستی",
  "opening": "افتتاحیه",
  "online_sale": "فروش آنلاین",
  "counter_sale": "فروش حضوری",
  "recognition": "شناسایی درآمد",
  "refund": "استرداد",
  "expense": "هزینه",
  "income": "درآمد متفرقه",
  "vendor_payment": "پرداخت به تامین‌کننده",
  "transfer": "انتقال / پرداخت",
  "asset_purchase": "خرید دارایی",
  "depreciation": "استهلاک",
  "cash_close": "صندوق‌گردانی",
  "payroll": "حقوق",
  "reversal": "ابطال",
  "closing": "بستن سال",
};

/// Roles of accounts that hold money (the ones a payment can come from or go to).
const List<String> moneyRoles = ["cash", "bank", "pos", "gateway"];

class Account {
  const Account({
    required this.id,
    required this.code,
    required this.name,
    required this.type,
    required this.parentId,
    required this.isGroup,
    required this.role,
    required this.active,
    required this.isSystem,
  });

  factory Account.fromJson(Json j) => Account(
    id: j.str("id"),
    code: j.str("code"),
    name: j.str("name"),
    type: j.str("type"),
    parentId: j.strOrNull("parent_id"),
    isGroup: j.flag("is_group"),
    role: j.strOrNull("role"),
    active: j.flag("active", true),
    isSystem: j.flag("is_system"),
  );

  final String id;
  final String code;
  final String name;
  final String type;
  final String? parentId;
  final bool isGroup;
  final String? role;
  final bool active;
  final bool isSystem;

  String get label => "$code - $name";
  bool get holdsMoney => role != null && moneyRoles.contains(role);
}

class EntryLine {
  const EntryLine({
    required this.accountCode,
    required this.accountName,
    required this.debitIrr,
    required this.creditIrr,
    required this.memo,
    required this.vendorName,
  });

  factory EntryLine.fromJson(Json j) => EntryLine(
    accountCode: j.str("account_code"),
    accountName: j.str("account_name"),
    debitIrr: j.integer("debit_irr"),
    creditIrr: j.integer("credit_irr"),
    memo: j.str("memo"),
    vendorName: j.str("vendor_name"),
  );

  final String accountCode;
  final String accountName;
  final int debitIrr;
  final int creditIrr;
  final String memo;
  final String vendorName;
}

class Entry {
  const Entry({
    required this.id,
    required this.number,
    required this.fiscalYear,
    required this.date,
    required this.description,
    required this.source,
    required this.status,
    required this.createdBy,
    required this.totalIrr,
    required this.lines,
  });

  factory Entry.fromJson(Json j) => Entry(
    id: j.str("id"),
    number: j.integer("number"),
    fiscalYear: j.integer("fiscal_year"),
    date: j.str("date"),
    description: j.str("description"),
    source: j.str("source"),
    status: j.str("status"),
    createdBy: j.str("created_by"),
    totalIrr: j.integer("total_irr"),
    lines: j.list("lines").map(EntryLine.fromJson).toList(),
  );

  final String id;
  final int number;
  final int fiscalYear;
  final String date;
  final String description;
  final String source;

  /// "posted" or "reversed".
  final String status;
  final String createdBy;
  final int totalIrr;
  final List<EntryLine> lines;

  bool get reversed => status == "reversed";
  String get sourceLabel => entrySourceLabels[source] ?? source;
}

class AccountingSettings {
  AccountingSettings({
    required this.autoPostingEnabled,
    required this.vatPercent,
    required this.gatewayFeePercent,
    required this.revenueRecognition,
    required this.lockedThrough,
  });

  factory AccountingSettings.fromJson(Json j) => AccountingSettings(
    autoPostingEnabled: j.flag("auto_posting_enabled"),
    vatPercent: j.number("vat_percent"),
    gatewayFeePercent: j.number("gateway_fee_percent"),
    revenueRecognition: j.str("revenue_recognition", "on_payment"),
    lockedThrough: j.strOrNull("locked_through"),
  );

  bool autoPostingEnabled;
  double vatPercent;
  double gatewayFeePercent;

  /// "on_payment" or "on_session".
  String revenueRecognition;
  String? lockedThrough;

  Json toJson() => {
    "auto_posting_enabled": autoPostingEnabled,
    "vat_percent": vatPercent,
    "gateway_fee_percent": gatewayFeePercent,
    "revenue_recognition": revenueRecognition,
    "locked_through": lockedThrough,
  };
}

class Vendor {
  const Vendor({
    required this.id,
    required this.name,
    required this.phone,
    required this.note,
    required this.active,
    required this.owedIrr,
    required this.age0to30Irr,
    required this.age31to60Irr,
    required this.age61to90Irr,
    required this.ageOver90Irr,
    required this.advanceIrr,
  });

  factory Vendor.fromJson(Json j) => Vendor(
    id: j.str("id"),
    name: j.str("name"),
    phone: j.str("phone"),
    note: j.str("note"),
    active: j.flag("active", true),
    owedIrr: j.integer("owed_irr"),
    age0to30Irr: j.integer("age_0_30_irr"),
    age31to60Irr: j.integer("age_31_60_irr"),
    age61to90Irr: j.integer("age_61_90_irr"),
    ageOver90Irr: j.integer("age_over_90_irr"),
    advanceIrr: j.integer("advance_irr"),
  );

  final String id;
  final String name;
  final String phone;
  final String note;
  final bool active;
  final int owedIrr;
  final int age0to30Irr;
  final int age31to60Irr;
  final int age61to90Irr;
  final int ageOver90Irr;
  final int advanceIrr;
}

class Asset {
  const Asset({
    required this.id,
    required this.name,
    required this.costIrr,
    required this.salvageIrr,
    required this.inServiceDate,
    required this.lifeMonths,
    required this.status,
    required this.note,
    required this.accumulatedIrr,
    required this.bookValueIrr,
  });

  factory Asset.fromJson(Json j) => Asset(
    id: j.str("id"),
    name: j.str("name"),
    costIrr: j.integer("cost_irr"),
    salvageIrr: j.integer("salvage_irr"),
    inServiceDate: j.str("in_service_date"),
    lifeMonths: j.integer("life_months"),
    status: j.str("status"),
    note: j.str("note"),
    accumulatedIrr: j.integer("accumulated_irr"),
    bookValueIrr: j.integer("book_value_irr"),
  );

  final String id;
  final String name;
  final int costIrr;
  final int salvageIrr;
  final String inServiceDate;
  final int lifeMonths;

  /// "active" or "disposed".
  final String status;
  final String note;
  final int accumulatedIrr;
  final int bookValueIrr;

  bool get disposed => status == "disposed";
}

class StatementLine {
  const StatementLine({required this.code, required this.name, required this.group, required this.amountIrr});

  factory StatementLine.fromJson(Json j) => StatementLine(
    code: j.str("code"),
    name: j.str("name"),
    group: j.str("group"),
    amountIrr: j.integer("amount_irr"),
  );

  final String code;
  final String name;
  final String group;
  final int amountIrr;
}

class IncomeStatementPeriod {
  const IncomeStatementPeriod({
    required this.from,
    required this.to,
    required this.revenue,
    required this.expenses,
    required this.totalRevenueIrr,
    required this.totalExpensesIrr,
    required this.netProfitIrr,
  });

  factory IncomeStatementPeriod.fromJson(Json j) => IncomeStatementPeriod(
    from: j.str("from"),
    to: j.str("to"),
    revenue: j.list("revenue").map(StatementLine.fromJson).toList(),
    expenses: j.list("expenses").map(StatementLine.fromJson).toList(),
    totalRevenueIrr: j.integer("total_revenue_irr"),
    totalExpensesIrr: j.integer("total_expenses_irr"),
    netProfitIrr: j.integer("net_profit_irr"),
  );

  final String from;
  final String to;
  final List<StatementLine> revenue;
  final List<StatementLine> expenses;
  final int totalRevenueIrr;
  final int totalExpensesIrr;
  final int netProfitIrr;
}

class IncomeStatement {
  const IncomeStatement({required this.current, required this.previous});

  factory IncomeStatement.fromJson(Json j) => IncomeStatement(
    current: IncomeStatementPeriod.fromJson(j),
    previous: IncomeStatementPeriod.fromJson(j.obj("previous")),
  );

  final IncomeStatementPeriod current;
  final IncomeStatementPeriod previous;
}

class BalanceSheet {
  const BalanceSheet({
    required this.asOf,
    required this.assets,
    required this.liabilities,
    required this.equity,
    required this.currentEarningsIrr,
    required this.totalAssetsIrr,
    required this.totalLiabilitiesIrr,
    required this.totalEquityIrr,
    required this.differenceIrr,
  });

  factory BalanceSheet.fromJson(Json j) => BalanceSheet(
    asOf: j.str("as_of"),
    assets: j.list("assets").map(StatementLine.fromJson).toList(),
    liabilities: j.list("liabilities").map(StatementLine.fromJson).toList(),
    equity: j.list("equity").map(StatementLine.fromJson).toList(),
    currentEarningsIrr: j.integer("current_earnings_irr"),
    totalAssetsIrr: j.integer("total_assets_irr"),
    totalLiabilitiesIrr: j.integer("total_liabilities_irr"),
    totalEquityIrr: j.integer("total_equity_irr"),
    differenceIrr: j.integer("difference_irr"),
  );

  final String asOf;
  final List<StatementLine> assets;
  final List<StatementLine> liabilities;
  final List<StatementLine> equity;
  final int currentEarningsIrr;
  final int totalAssetsIrr;
  final int totalLiabilitiesIrr;
  final int totalEquityIrr;
  final int differenceIrr;
}

class TrialBalanceRow {
  const TrialBalanceRow({
    required this.code,
    required this.name,
    required this.debitIrr,
    required this.creditIrr,
    required this.closingDebitIrr,
    required this.closingCreditIrr,
  });

  factory TrialBalanceRow.fromJson(Json j) => TrialBalanceRow(
    code: j.str("code"),
    name: j.str("name"),
    debitIrr: j.integer("debit_irr"),
    creditIrr: j.integer("credit_irr"),
    closingDebitIrr: j.integer("closing_debit_irr"),
    closingCreditIrr: j.integer("closing_credit_irr"),
  );

  final String code;
  final String name;
  final int debitIrr;
  final int creditIrr;
  final int closingDebitIrr;
  final int closingCreditIrr;
}

class TrialBalance {
  const TrialBalance({
    required this.rows,
    required this.totalDebitIrr,
    required this.totalCreditIrr,
    required this.totalClosingDebitIrr,
    required this.totalClosingCreditIrr,
  });

  factory TrialBalance.fromJson(Json j) => TrialBalance(
    rows: j.list("rows").map(TrialBalanceRow.fromJson).toList(),
    totalDebitIrr: j.integer("total_debit_irr"),
    totalCreditIrr: j.integer("total_credit_irr"),
    totalClosingDebitIrr: j.integer("total_closing_debit_irr"),
    totalClosingCreditIrr: j.integer("total_closing_credit_irr"),
  );

  final List<TrialBalanceRow> rows;
  final int totalDebitIrr;
  final int totalCreditIrr;
  final int totalClosingDebitIrr;
  final int totalClosingCreditIrr;
}

class LedgerLine {
  const LedgerLine({
    required this.number,
    required this.fiscalYear,
    required this.date,
    required this.description,
    required this.debitIrr,
    required this.creditIrr,
    required this.balanceIrr,
  });

  factory LedgerLine.fromJson(Json j) => LedgerLine(
    number: j.integer("number"),
    fiscalYear: j.integer("fiscal_year"),
    date: j.str("date"),
    description: j.str("description"),
    debitIrr: j.integer("debit_irr"),
    creditIrr: j.integer("credit_irr"),
    balanceIrr: j.integer("balance_irr"),
  );

  final int number;
  final int fiscalYear;
  final String date;
  final String description;
  final int debitIrr;
  final int creditIrr;
  final int balanceIrr;
}

class Ledger {
  const Ledger({required this.account, required this.openingIrr, required this.closingIrr, required this.lines});

  factory Ledger.fromJson(Json j) => Ledger(
    account: Account.fromJson(j.obj("account")),
    openingIrr: j.integer("opening_irr"),
    closingIrr: j.integer("closing_irr"),
    lines: j.list("lines").map(LedgerLine.fromJson).toList(),
  );

  final Account account;
  final int openingIrr;
  final int closingIrr;
  final List<LedgerLine> lines;
}

class SalesDay {
  const SalesDay({
    required this.date,
    required this.onlineIrr,
    required this.cashIrr,
    required this.cardIrr,
    required this.transferIrr,
    required this.receivedIrr,
    required this.revenueIrr,
  });

  factory SalesDay.fromJson(Json j) => SalesDay(
    date: j.str("date"),
    onlineIrr: j.integer("online_irr"),
    cashIrr: j.integer("cash_irr"),
    cardIrr: j.integer("card_irr"),
    transferIrr: j.integer("transfer_irr"),
    receivedIrr: j.integer("received_irr"),
    revenueIrr: j.integer("revenue_irr"),
  );

  final String date;
  final int onlineIrr;
  final int cashIrr;
  final int cardIrr;
  final int transferIrr;
  final int receivedIrr;
  final int revenueIrr;
}

class SalesReport {
  const SalesReport({
    required this.days,
    required this.onlineIrr,
    required this.cashIrr,
    required this.cardIrr,
    required this.transferIrr,
    required this.receivedIrr,
    required this.revenueIrr,
  });

  factory SalesReport.fromJson(Json j) => SalesReport(
    days: j.list("days").map(SalesDay.fromJson).toList(),
    onlineIrr: j.integer("online_irr"),
    cashIrr: j.integer("cash_irr"),
    cardIrr: j.integer("card_irr"),
    transferIrr: j.integer("transfer_irr"),
    receivedIrr: j.integer("received_irr"),
    revenueIrr: j.integer("revenue_irr"),
  );

  final List<SalesDay> days;
  final int onlineIrr;
  final int cashIrr;
  final int cardIrr;
  final int transferIrr;
  final int receivedIrr;
  final int revenueIrr;
}

class VatReport {
  const VatReport({
    required this.collectedIrr,
    required this.paidIrr,
    required this.openingBalanceIrr,
    required this.netPayableIrr,
  });

  factory VatReport.fromJson(Json j) => VatReport(
    collectedIrr: j.integer("collected_irr"),
    paidIrr: j.integer("paid_irr"),
    openingBalanceIrr: j.integer("opening_balance_irr"),
    netPayableIrr: j.integer("net_payable_irr"),
  );

  final int collectedIrr;
  final int paidIrr;
  final int openingBalanceIrr;
  final int netPayableIrr;
}

class BudgetRow {
  const BudgetRow({
    required this.accountId,
    required this.code,
    required this.name,
    required this.type,
    required this.budgetIrr,
    required this.actualIrr,
    required this.varianceIrr,
  });

  factory BudgetRow.fromJson(Json j) => BudgetRow(
    accountId: j.str("account_id"),
    code: j.str("code"),
    name: j.str("name"),
    type: j.str("type"),
    budgetIrr: j.integer("budget_irr"),
    actualIrr: j.integer("actual_irr"),
    varianceIrr: j.integer("variance_irr"),
  );

  final String accountId;
  final String code;
  final String name;
  final String type;
  final int budgetIrr;
  final int actualIrr;
  final int varianceIrr;
}

class CashClosing {
  const CashClosing({
    required this.id,
    required this.date,
    required this.expectedIrr,
    required this.countedIrr,
    required this.differenceIrr,
    required this.note,
    required this.closedBy,
  });

  factory CashClosing.fromJson(Json j) => CashClosing(
    id: j.str("id"),
    date: j.str("date"),
    expectedIrr: j.integer("expected_irr"),
    countedIrr: j.integer("counted_irr"),
    differenceIrr: j.integer("difference_irr"),
    note: j.str("note"),
    closedBy: j.str("closed_by"),
  );

  final String id;
  final String date;
  final int expectedIrr;
  final int countedIrr;
  final int differenceIrr;
  final String note;
  final String closedBy;
}

class CashState {
  const CashState({required this.date, required this.expectedIrr, required this.closings});

  factory CashState.fromJson(Json j) => CashState(
    date: j.str("date"),
    expectedIrr: j.integer("expected_irr"),
    closings: j.list("closings").map(CashClosing.fromJson).toList(),
  );

  final String date;
  final int expectedIrr;
  final List<CashClosing> closings;
}

class TrendPoint {
  const TrendPoint({required this.key, required this.revenueIrr, required this.expensesIrr, required this.profitIrr});

  factory TrendPoint.fromJson(Json j) => TrendPoint(
    key: j.str("key"),
    revenueIrr: j.integer("revenue_irr"),
    expensesIrr: j.integer("expenses_irr"),
    profitIrr: j.integer("profit_irr"),
  );

  /// "1405-07" (Jalali year-month).
  final String key;
  final int revenueIrr;
  final int expensesIrr;
  final int profitIrr;
}

class AccountingDashboard {
  const AccountingDashboard({
    required this.cashIrr,
    required this.bankIrr,
    required this.posIrr,
    required this.gatewayIrr,
    required this.liquidIrr,
    required this.payablesIrr,
    required this.refundsPayableIrr,
    required this.vatBalanceIrr,
    required this.todayRevenueIrr,
    required this.monthRevenueIrr,
    required this.monthExpensesIrr,
    required this.monthProfitIrr,
    required this.unrecognizedAdvancesIrr,
    required this.trend,
    required this.topExpenses,
  });

  factory AccountingDashboard.fromJson(Json j) => AccountingDashboard(
    cashIrr: j.integer("cash_irr"),
    bankIrr: j.integer("bank_irr"),
    posIrr: j.integer("pos_irr"),
    gatewayIrr: j.integer("gateway_irr"),
    liquidIrr: j.integer("liquid_irr"),
    payablesIrr: j.integer("payables_irr"),
    refundsPayableIrr: j.integer("refunds_payable_irr"),
    vatBalanceIrr: j.integer("vat_balance_irr"),
    todayRevenueIrr: j.integer("today_revenue_irr"),
    monthRevenueIrr: j.integer("month_revenue_irr"),
    monthExpensesIrr: j.integer("month_expenses_irr"),
    monthProfitIrr: j.integer("month_profit_irr"),
    unrecognizedAdvancesIrr: j.integer("unrecognized_advances_irr"),
    trend: j.list("trend").map(TrendPoint.fromJson).toList(),
    topExpenses: j.list("top_expenses").map(StatementLine.fromJson).toList(),
  );

  final int cashIrr;
  final int bankIrr;
  final int posIrr;
  final int gatewayIrr;
  final int liquidIrr;
  final int payablesIrr;
  final int refundsPayableIrr;
  final int vatBalanceIrr;
  final int todayRevenueIrr;
  final int monthRevenueIrr;
  final int monthExpensesIrr;
  final int monthProfitIrr;
  final int unrecognizedAdvancesIrr;
  final List<TrendPoint> trend;
  final List<StatementLine> topExpenses;
}
