import "package:davos_admin/shared/models/json_read.dart";

/// All amounts from the accounting API are Rial (`*_irr`); requests take Toman (`*_toman`).
const Map<String, String> entrySourceLabels = {
  "manual": "سند دستی",
  "opening": "موجودی اول دوره",
  "online_sale": "فروش آنلاین",
  "counter_sale": "فروش حضوری",
  "refund": "استرداد بلیت",
  "expense": "هزینه",
  "income": "درآمد",
  "vendor_payment": "پرداخت بدهی",
  "transfer": "جابجایی پول",
  "asset_purchase": "خرید تجهیزات",
  "cash_close": "شمارش صندوق",
  "payroll": "حقوق",
};

/// The entries the day book lists one by one; ticket sales are one line per day instead.
const List<String> dayBookSources = [
  "expense",
  "income",
  "transfer",
  "payroll",
  "vendor_payment",
  "manual",
  "opening",
  "cash_close",
  "asset_purchase",
  "refund",
];

/// Entries the owner may delete from the day book (the books keep a reversing entry).
const Set<String> deletableSources = {"expense", "income", "transfer", "payroll", "vendor_payment", "manual"};

/// Where money is kept: the till, or the bank (card-reader and gateway balances are bank money on its way).
enum Wallet { cash, bank }

const Map<Wallet, String> walletLabels = {Wallet.cash: "صندوق", Wallet.bank: "بانک"};
const Map<String, Wallet> _walletOfRole = {"cash": Wallet.cash, "bank": Wallet.bank, "pos": Wallet.bank, "gateway": Wallet.bank};

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

  Wallet? get wallet => role == null ? null : _walletOfRole[role];

  /// An income or expense category the owner picks from (system accounts are booked automatically).
  bool isCategory(String kind) => type == kind && !isGroup && !isSystem;
}

class EntryLine {
  const EntryLine({required this.accountId, required this.debitIrr, required this.creditIrr});

  factory EntryLine.fromJson(Json j) =>
      EntryLine(accountId: j.str("account_id"), debitIrr: j.integer("debit_irr"), creditIrr: j.integer("credit_irr"));

  final String accountId;
  final int debitIrr;
  final int creditIrr;
}

class Entry {
  const Entry({
    required this.id,
    required this.date,
    required this.description,
    required this.source,
    required this.status,
    required this.totalIrr,
    required this.lines,
  });

  factory Entry.fromJson(Json j) => Entry(
    id: j.str("id"),
    date: j.str("date"),
    description: j.str("description"),
    source: j.str("source"),
    status: j.str("status"),
    totalIrr: j.integer("total_irr"),
    lines: j.list("lines").map(EntryLine.fromJson).toList(),
  );

  final String id;
  final String date;
  final String description;
  final String source;

  /// "posted" or "reversed".
  final String status;
  final int totalIrr;
  final List<EntryLine> lines;

  bool get reversed => status == "reversed";
  bool get deletable => !reversed && deletableSources.contains(source);
}

/// Which way the money of an entry went.
enum Flow { moneyIn, moneyOut, move, other }

/// One journal entry in plain words: direction, amount, title, category, and the till or bank it touched.
class EntryView {
  const EntryView({required this.flow, required this.amountIrr, required this.title, this.category, this.wallet});

  factory EntryView.of(Entry entry, Map<String, Account> byId) {
    var moneyNet = 0;
    final wallets = <Wallet>{};
    Wallet? paidFrom;
    String? category;
    for (final line in entry.lines) {
      final account = byId[line.accountId];
      final wallet = account?.wallet;
      if (wallet != null) {
        moneyNet += line.debitIrr - line.creditIrr;
        wallets.add(wallet);
        if (line.creditIrr > 0) paidFrom = wallet;
      } else if (account != null && (account.type == "expense" || account.type == "revenue")) {
        category ??= account.name;
      }
    }
    final title = entry.description.isNotEmpty ? entry.description : (category ?? entrySourceLabels[entry.source] ?? "سند");
    if (entry.source == "transfer" && wallets.length == 2) {
      final from = paidFrom ?? Wallet.cash;
      final to = from == Wallet.cash ? Wallet.bank : Wallet.cash;
      return EntryView(flow: Flow.move, amountIrr: entry.totalIrr, title: title, wallet: "${walletLabels[from]} ← ${walletLabels[to]}");
    }
    final walletText = wallets.map((w) => walletLabels[w]).join("، ");
    if (moneyNet > 0) return EntryView(flow: Flow.moneyIn, amountIrr: moneyNet, title: title, category: category, wallet: walletText);
    if (moneyNet < 0) return EntryView(flow: Flow.moneyOut, amountIrr: -moneyNet, title: title, category: category, wallet: walletText);
    return EntryView(flow: Flow.other, amountIrr: entry.totalIrr, title: title, category: category);
  }

  final Flow flow;
  final int amountIrr;
  final String title;
  final String? category;
  final String? wallet;
}

class StatementLine {
  const StatementLine({required this.code, required this.name, required this.amountIrr});

  factory StatementLine.fromJson(Json j) => StatementLine(code: j.str("code"), name: j.str("name"), amountIrr: j.integer("amount_irr"));

  final String code;
  final String name;
  final int amountIrr;
}

class IncomeStatementPeriod {
  const IncomeStatementPeriod({
    required this.revenue,
    required this.expenses,
    required this.totalRevenueIrr,
    required this.totalExpensesIrr,
    required this.netProfitIrr,
  });

  factory IncomeStatementPeriod.fromJson(Json j) => IncomeStatementPeriod(
    revenue: j.list("revenue").map(StatementLine.fromJson).toList(),
    expenses: j.list("expenses").map(StatementLine.fromJson).toList(),
    totalRevenueIrr: j.integer("total_revenue_irr"),
    totalExpensesIrr: j.integer("total_expenses_irr"),
    netProfitIrr: j.integer("net_profit_irr"),
  );

  final List<StatementLine> revenue;
  final List<StatementLine> expenses;
  final int totalRevenueIrr;
  final int totalExpensesIrr;
  final int netProfitIrr;
}

class IncomeStatement {
  const IncomeStatement({required this.current, required this.previous});

  factory IncomeStatement.fromJson(Json j) =>
      IncomeStatement(current: IncomeStatementPeriod.fromJson(j), previous: IncomeStatementPeriod.fromJson(j.obj("previous")));

  final IncomeStatementPeriod current;
  final IncomeStatementPeriod previous;
}

/// Ticket money of one day: online, counter cash (the till) and counter card/transfer (the bank).
class SalesDay {
  const SalesDay({required this.date, required this.onlineIrr, required this.cashIrr, required this.cardIrr, required this.receivedIrr});

  factory SalesDay.fromJson(Json j) => SalesDay(
    date: j.str("date"),
    onlineIrr: j.integer("online_irr"),
    cashIrr: j.integer("cash_irr"),
    cardIrr: j.integer("card_irr"),
    receivedIrr: j.integer("received_irr"),
  );

  final String date;
  final int onlineIrr;
  final int cashIrr;
  final int cardIrr;
  final int receivedIrr;
}

class SalesReport {
  const SalesReport({required this.days, required this.onlineIrr, required this.cashIrr, required this.cardIrr, required this.receivedIrr});

  factory SalesReport.fromJson(Json j) => SalesReport(
    days: j.list("days").map(SalesDay.fromJson).toList(),
    onlineIrr: j.integer("online_irr"),
    cashIrr: j.integer("cash_irr"),
    cardIrr: j.integer("card_irr"),
    receivedIrr: j.integer("received_irr"),
  );

  final List<SalesDay> days;
  final int onlineIrr;
  final int cashIrr;
  final int cardIrr;
  final int receivedIrr;
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
    required this.refundsPayableIrr,
    required this.todayRevenueIrr,
    required this.monthRevenueIrr,
    required this.monthExpensesIrr,
    required this.monthProfitIrr,
    required this.trend,
    required this.topExpenses,
  });

  factory AccountingDashboard.fromJson(Json j) => AccountingDashboard(
    cashIrr: j.integer("cash_irr"),
    // card-reader and gateway balances are bank money on its way (older books)
    bankIrr: j.integer("bank_irr") + j.integer("pos_irr") + j.integer("gateway_irr"),
    refundsPayableIrr: j.integer("refunds_payable_irr"),
    todayRevenueIrr: j.integer("today_revenue_irr"),
    monthRevenueIrr: j.integer("month_revenue_irr"),
    monthExpensesIrr: j.integer("month_expenses_irr"),
    monthProfitIrr: j.integer("month_profit_irr"),
    trend: j.list("trend").map(TrendPoint.fromJson).toList(),
    topExpenses: j.list("top_expenses").map(StatementLine.fromJson).toList(),
  );

  final int cashIrr;
  final int bankIrr;
  final int refundsPayableIrr;
  final int todayRevenueIrr;
  final int monthRevenueIrr;
  final int monthExpensesIrr;
  final int monthProfitIrr;
  final List<TrendPoint> trend;
  final List<StatementLine> topExpenses;

  int get liquidIrr => cashIrr + bankIrr;
}
