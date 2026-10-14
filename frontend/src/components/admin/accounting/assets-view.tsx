"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { useAdmin } from "@/components/admin/admin-session";
import { Card, Table, cell } from "@/components/admin/admin-ui";
import { SingleDatePicker } from "@/components/admin/date-picker-field";
import { AccountSelect, Field, MoneyInput, VendorSelect } from "@/components/admin/accounting/accounting-fields";
import { buttonClasses } from "@/components/button-link";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { errorMessage } from "@/lib/api";
import { toman, type Account, type Asset, type Vendor } from "@/lib/accounting";
import { fa, toLatinDigits } from "@/lib/format";
import { JALALI_MONTHS, currentBusinessDay, isoToJalali, isoToJalaliParts } from "@/lib/jalali";

/** Karts and equipment: register them (booking the purchase), and book each month's depreciation. */
export function AssetsView({ accounts, vendors, onChanged }: { accounts: Account[]; vendors: Vendor[]; onChanged: () => void }) {
  const { call } = useAdmin();
  const [assets, setAssets] = useState<Asset[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);
  const now = isoToJalaliParts(currentBusinessDay());
  const [year, setYear] = useState(now.jy);
  const [month, setMonth] = useState(now.jm);

  const load = useCallback(async () => {
    try {
      setAssets(await call<Asset[]>("/accounting/assets"));
    } catch (err) {
      setError(errorMessage(err));
    }
  }, [call]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- the first fetch of this screen
    void load();
  }, [load]);

  async function depreciate() {
    setError(null);
    setMessage(null);
    try {
      const result = await call<{ total_irr: number }>("/accounting/depreciation", { method: "POST", body: { year, month } });
      setMessage(result.total_irr ? `استهلاک ${JALALI_MONTHS[month - 1]} ${fa(year)} ثبت شد: ${toman(result.total_irr)} تومان.` : "برای این ماه استهلاک ثبت‌نشده‌ای نبود.");
      await load();
      onChanged();
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  async function dispose(asset: Asset) {
    if (!window.confirm(`«${asset.name}» فروخته یا اسقاط شده و استهلاک آن متوقف شود؟ (سند فروش را جداگانه ثبت کنید.)`)) return;
    try {
      await call(`/accounting/assets/${asset.id}/dispose`, { method: "POST" });
      await load();
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  const cost = (assets ?? []).reduce((s, a) => s + a.cost_irr, 0);
  const book = (assets ?? []).filter((a) => a.status === "active").reduce((s, a) => s + a.book_value_irr, 0);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <p className="font-bold">
          بهای تمام‌شده: {toman(cost)} · ارزش دفتری فعال: {toman(book)} تومان
        </p>
        <div className="flex flex-wrap items-end gap-3">
          <Field label="سال">
            <input className="field w-24" dir="ltr" value={fa(year)} onChange={(e) => setYear(Number(toLatinDigits(e.target.value).replace(/\D/g, "")) || now.jy)} />
          </Field>
          <Field label="ماه">
            <select className="field w-36" value={month} onChange={(e) => setMonth(Number(e.target.value))}>
              {JALALI_MONTHS.map((name, index) => (
                <option key={name} value={index + 1}>
                  {name}
                </option>
              ))}
            </select>
          </Field>
          <button type="button" onClick={depreciate} className={buttonClasses("dark", "md")}>
            ثبت استهلاک این ماه
          </button>
          <button type="button" onClick={() => setAdding((v) => !v)} className={buttonClasses("primary", "md")}>
            {adding ? "بستن فرم" : "دارایی جدید"}
          </button>
        </div>
      </div>
      {message && <Alert tone="success">{message}</Alert>}
      {error && <Alert tone="error">{error}</Alert>}
      {adding && <RegisterAsset accounts={accounts} vendors={vendors} onDone={() => { setAdding(false); void load(); onChanged(); }} />}
      {!assets ? (
        <Spinner className="h-8 w-8" />
      ) : (
        <Table head={["دارایی", "تاریخ بهره‌برداری", "بهای تمام‌شده", "ارزش اسقاط", "عمر مفید", "استهلاک انباشته", "ارزش دفتری", "وضعیت", ""]} empty={assets.length === 0}>
          {assets.map((a) => (
            <tr key={a.id} className={a.status === "disposed" ? "opacity-50" : ""}>
              <td className={`${cell} font-bold`}>{a.name}</td>
              <td className={cell}>{fa(isoToJalali(a.in_service_date))}</td>
              <td className={cell}>{toman(a.cost_irr)}</td>
              <td className={cell}>{toman(a.salvage_irr)}</td>
              <td className={cell}>{fa(a.life_months)} ماه</td>
              <td className={cell}>{toman(a.accumulated_irr)}</td>
              <td className={`${cell} font-black`}>{toman(a.book_value_irr)}</td>
              <td className={cell}>{a.status === "active" ? "فعال" : "اسقاط / فروخته"}</td>
              <td className={cell}>
                {a.status === "active" && (
                  <button type="button" className="font-bold text-signal underline underline-offset-4" onClick={() => dispose(a)}>
                    اسقاط
                  </button>
                )}
              </td>
            </tr>
          ))}
        </Table>
      )}
    </div>
  );
}

function RegisterAsset({ accounts, vendors, onDone }: { accounts: Account[]; vendors: Vendor[]; onDone: () => void }) {
  const { call } = useAdmin();
  const [name, setName] = useState("");
  const [account, setAccount] = useState(accounts.find((a) => a.role === "fixed_asset_karts")?.id ?? "");
  const [cost, setCost] = useState(0);
  const [salvage, setSalvage] = useState(0);
  const [day, setDay] = useState(currentBusinessDay());
  const [life, setLife] = useState(60);
  const [post, setPost] = useState(true);
  const [paidFrom, setPaidFrom] = useState("");
  const [vendor, setVendor] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await call("/accounting/assets", {
        method: "POST",
        body: {
          name,
          asset_account_id: account,
          cost_toman: cost,
          salvage_toman: salvage,
          in_service_date: day,
          life_months: life,
          post_purchase: post,
          paid_from_account_id: paidFrom || null,
          vendor_id: vendor || null,
        },
      });
      onDone();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card title="ثبت دارایی جدید">
      <form onSubmit={submit} className="grid max-w-3xl gap-4 sm:grid-cols-2">
        <Field label="نام دارایی (مثلا: کارت شماره ۳)">
          <input className="field" value={name} onChange={(e) => setName(e.target.value)} maxLength={120} required />
        </Field>
        <AccountSelect label="حساب دارایی" accounts={accounts} value={account} onChange={setAccount} types={["asset"]} />
        <MoneyInput label="بهای تمام‌شده (تومان)" value={cost} onChange={setCost} />
        <MoneyInput label="ارزش اسقاط (تومان)" value={salvage} onChange={setSalvage} hint="ارزش تقریبی در پایان عمر مفید؛ می‌تواند صفر باشد." />
        <Field label="تاریخ بهره‌برداری">
          <SingleDatePicker value={day} onChange={setDay} label="تاریخ بهره‌برداری" />
        </Field>
        <Field label="عمر مفید (ماه)">
          <input className="field" dir="ltr" value={fa(life)} onChange={(e) => setLife(Number(toLatinDigits(e.target.value).replace(/\D/g, "")) || 1)} />
        </Field>
        <label className="flex items-center gap-3 text-sm font-bold sm:col-span-2">
          <input type="checkbox" className="h-5 w-5 accent-[#0c0d10]" checked={post} onChange={(e) => setPost(e.target.checked)} />
          سند خرید هم ثبت شود (اگر قبلاً در موجودی‌های اول کار آمده، خاموش کنید)
        </label>
        {post && (
          <>
            <AccountSelect label="پرداخت از" accounts={accounts} value={paidFrom} onChange={setPaidFrom} types={["asset"]} roles={["cash", "bank", "pos", "gateway"]} allowEmpty="نسیه (بدهی به تامین‌کننده)" />
            <VendorSelect label="تامین‌کننده" vendors={vendors} value={vendor} onChange={setVendor} allowEmpty="بدون تامین‌کننده" />
          </>
        )}
        {error && (
          <div className="sm:col-span-2">
            <Alert tone="error">{error}</Alert>
          </div>
        )}
        <div className="sm:col-span-2">
          <button type="submit" disabled={busy || cost <= 0} className={buttonClasses("primary", "md")}>
            {busy ? <Spinner /> : "ثبت دارایی"}
          </button>
        </div>
      </form>
    </Card>
  );
}
