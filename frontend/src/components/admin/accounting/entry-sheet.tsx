"use client";

import { useEffect, useMemo, useState, type FormEvent } from "react";
import { useAdmin } from "@/components/admin/admin-session";
import { SingleDatePicker } from "@/components/admin/date-picker-field";
import { CategoryChips, Field, MoneyInput, Segmented } from "@/components/admin/accounting/accounting-fields";
import { buttonClasses } from "@/components/button-link";
import { CloseIcon } from "@/components/icons";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { errorMessage } from "@/lib/api";
import { categories, toman, walletAccount, WALLET_LABEL, type Account, type Wallet } from "@/lib/accounting";
import { currentBusinessDay } from "@/lib/jalali";

export type EntryKind = "expense" | "income" | "move" | "owner" | "refund";

const KINDS: { id: EntryKind; label: string }[] = [
  { id: "expense", label: "هزینه" },
  { id: "income", label: "درآمد" },
  { id: "move", label: "جابجایی" },
  { id: "owner", label: "شخصی" },
];

const WALLETS: { id: Wallet; label: string }[] = [
  { id: "cash", label: WALLET_LABEL.cash },
  { id: "bank", label: WALLET_LABEL.bank },
];

/**
 * Records money in plain words: an expense, an income that is not a ticket, cash taken to the bank (or back), or a
 * refund handed back to a customer. Amount, category, till or bank, done; the date defaults to today.
 */
export function EntrySheet({
  accounts,
  kind: initialKind,
  amountToman = 0,
  refundsOwedIrr = 0,
  onClose,
  onSaved,
}: {
  accounts: Account[];
  kind: EntryKind;
  amountToman?: number;
  refundsOwedIrr?: number;
  onClose: () => void;
  onSaved: (message: string) => void;
}) {
  const { call } = useAdmin();
  const [kind, setKind] = useState<EntryKind>(initialKind);
  const [amount, setAmount] = useState(amountToman);
  const [category, setCategory] = useState("");
  const [wallet, setWallet] = useState<Wallet>(initialKind === "income" || initialKind === "expense" ? "cash" : "bank");
  const [day, setDay] = useState(currentBusinessDay());
  const [description, setDescription] = useState("");
  const [ownerDraw, setOwnerDraw] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const options = useMemo(
    () => (kind === "expense" || kind === "income" ? categories(accounts, kind === "expense" ? "expense" : "revenue") : []),
    [accounts, kind],
  );

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => event.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const needsCategory = kind === "expense" || kind === "income";
  const ready = amount > 0 && (!needsCategory || options.some((o) => o.id === category));

  async function submit(event: FormEvent) {
    event.preventDefault();
    const till = walletAccount(accounts, "cash");
    const bank = walletAccount(accounts, "bank");
    const chosen = walletAccount(accounts, wallet);
    if (!till || !bank || !chosen) {
      setError("حساب صندوق یا بانک پیدا نشد.");
      return;
    }
    setBusy(true);
    setError(null);
    const base = { date: day, amount_toman: amount, description: description.trim() };
    try {
      if (kind === "expense") {
        await call("/accounting/expenses", { method: "POST", body: { ...base, expense_account_id: category, paid_from_account_id: chosen.id } });
      } else if (kind === "income") {
        await call("/accounting/income", { method: "POST", body: { ...base, revenue_account_id: category, deposit_account_id: chosen.id } });
      } else if (kind === "move") {
        const [from, to] = wallet === "cash" ? [till, bank] : [bank, till];
        await call("/accounting/transfers", { method: "POST", body: { ...base, from_account_id: from.id, to_account_id: to.id } });
      } else if (kind === "owner") {
        // the owner's own money: taking profit out, or putting money in; not an expense or income of the business
        const capital = accounts.find((a) => a.role === "capital");
        if (!capital) throw new Error("حساب سرمایه پیدا نشد.");
        const [debit, credit] = ownerDraw ? [capital, chosen] : [chosen, capital];
        await call("/accounting/journal", {
          method: "POST",
          body: {
            date: day,
            description: base.description || (ownerDraw ? "برداشت شخصی مالک" : "آورده‌ی مالک"),
            lines: [
              { account_id: debit.id, debit_toman: amount },
              { account_id: credit.id, credit_toman: amount },
            ],
          },
        });
      } else {
        await call("/accounting/payments", { method: "POST", body: { ...base, from_account_id: chosen.id, vendor_id: null } });
      }
      const name = options.find((o) => o.id === category)?.name;
      onSaved(
        kind === "expense"
          ? `هزینه «${name}» به مبلغ ${toman(amount * 10)} تومان ثبت شد.`
          : kind === "income"
            ? `درآمد «${name}» به مبلغ ${toman(amount * 10)} تومان ثبت شد.`
            : kind === "move"
              ? `${toman(amount * 10)} تومان از ${WALLET_LABEL[wallet]} به ${WALLET_LABEL[wallet === "cash" ? "bank" : "cash"]} رفت.`
              : kind === "owner"
                ? `${ownerDraw ? "برداشت" : "آورده‌ی"} شخصی ${toman(amount * 10)} تومان ثبت شد.`
                : `پرداخت استرداد ${toman(amount * 10)} تومان ثبت شد.`,
      );
    } catch (err) {
      setError(errorMessage(err));
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 z-[60] flex items-end justify-center sm:items-center" role="dialog" aria-modal="true" aria-labelledby="entry-title">
      <button type="button" aria-label="بستن" onClick={onClose} className="absolute inset-0 bg-black/50 backdrop-blur-sm" tabIndex={-1} />
      <form
        onSubmit={submit}
        className="relative max-h-[92dvh] w-full max-w-xl overflow-y-auto rounded-t-[2rem] bg-surface p-5 pb-[max(1.25rem,env(safe-area-inset-bottom))] shadow-2xl ring-1 ring-line sm:rounded-[2rem] sm:p-7"
      >
        <div className="mb-5 flex items-center justify-between gap-3">
          <h2 id="entry-title" className="text-xl font-black">
            {kind === "refund" ? "پرداخت استرداد به مشتری" : "ثبت دخل و خرج"}
          </h2>
          <button type="button" onClick={onClose} aria-label="بستن" className="grid h-10 w-10 place-items-center rounded-full ring-1 ring-line-strong">
            <CloseIcon className="h-4 w-4" />
          </button>
        </div>

        <div className="space-y-5">
          {kind !== "refund" && (
            <Segmented
              label="نوع"
              options={KINDS}
              value={kind}
              onChange={(next) => {
                setKind(next);
                setCategory("");
                setError(null);
              }}
            />
          )}
          <MoneyInput label="مبلغ" value={amount} onChange={setAmount} big autoFocus={amountToman === 0} />
          {kind === "refund" && refundsOwedIrr > 0 && (
            <p className="-mt-3 text-xs text-fg-subtle">مانده‌ی استرداد پرداخت‌نشده: {toman(refundsOwedIrr)} تومان</p>
          )}

          {needsCategory &&
            (options.length ? (
              <CategoryChips label={kind === "expense" ? "بابت" : "از محل"} options={options} value={category} onChange={setCategory} />
            ) : (
              <Alert tone="info">هنوز دسته‌ای ندارید؛ از بخش «دسته‌ها» یکی اضافه کنید.</Alert>
            ))}

          {kind === "owner" && (
            <>
              <Segmented
                label="کدام"
                options={[
                  { id: "draw", label: "برداشت برای خودم" },
                  { id: "put", label: "آورده به مجموعه" },
                ]}
                value={ownerDraw ? "draw" : "put"}
                onChange={(id) => setOwnerDraw(id === "draw")}
              />
              <p className="-mt-3 text-xs leading-6 text-fg-subtle">پول شخصی مالک؛ هزینه یا درآمد مجموعه حساب نمی‌شود و سود را تغییر نمی‌دهد.</p>
            </>
          )}

          {kind === "move" ? (
            <Segmented
              label="جهت"
              options={[
                { id: "cash", label: "صندوق ← بانک" },
                { id: "bank", label: "بانک ← صندوق" },
              ]}
              value={wallet}
              onChange={setWallet}
            />
          ) : (
            <Segmented
              label={kind === "income" || (kind === "owner" && !ownerDraw) ? "واریز به" : "پرداخت از"}
              options={WALLETS}
              value={wallet}
              onChange={setWallet}
            />
          )}

          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="تاریخ">
              <SingleDatePicker value={day} onChange={setDay} label="تاریخ" />
            </Field>
            <Field label="توضیح (اختیاری)">
              <input className="field" value={description} onChange={(e) => setDescription(e.target.value)} maxLength={300} placeholder={kind === "expense" ? "مثلاً تعویض لنت کارت ۴" : ""} />
            </Field>
          </div>

          {error && <Alert tone="error">{error}</Alert>}
          <button type="submit" disabled={busy || !ready} className={buttonClasses("primary", "lg", "w-full")}>
            {busy ? <Spinner /> : "ثبت"}
          </button>
        </div>
      </form>
    </div>
  );
}
