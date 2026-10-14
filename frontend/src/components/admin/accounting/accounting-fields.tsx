"use client";

import type { ChangeEvent, ReactNode } from "react";
import { ACCOUNT_TYPE_LABEL, type Account, type AccountType, type Vendor } from "@/lib/accounting";
import { fa, toLatinDigits } from "@/lib/format";

export function Field({ label, hint, children }: { label: string; hint?: ReactNode; children: ReactNode }) {
  return (
    <label className="block">
      <span className="label">{label}</span>
      {children}
      {hint && <span className="mt-1 block text-xs text-fg-subtle">{hint}</span>}
    </label>
  );
}

/** A Toman amount typed with any digits; shown grouped ("۱٬۲۵۰٬۰۰۰"). The value is a whole number of Toman. */
export function MoneyInput({ label, value, onChange, hint }: { label: string; value: number; onChange: (toman: number) => void; hint?: ReactNode }) {
  const handle = (event: ChangeEvent<HTMLInputElement>) => {
    const digits = toLatinDigits(event.target.value).replace(/[^\d]/g, "");
    onChange(digits ? Math.min(Number(digits), 100_000_000_000_000) : 0);
  };
  return (
    <Field label={label} hint={hint}>
      <input className="field" dir="ltr" inputMode="numeric" value={value ? fa(value.toLocaleString("en-US")).replace(/,/g, "٬") : ""} onChange={handle} placeholder="۰" />
    </Field>
  );
}

const TYPE_ORDER: AccountType[] = ["asset", "liability", "equity", "revenue", "expense"];

/** Postable accounts (never group headings) of the allowed types, grouped by type. */
export function AccountSelect({
  label,
  accounts,
  value,
  onChange,
  types,
  roles,
  allowEmpty,
}: {
  label: string;
  accounts: Account[];
  value: string;
  onChange: (id: string) => void;
  types?: AccountType[];
  roles?: string[];
  allowEmpty?: string;
}) {
  const usable = accounts.filter((a) => a.active && !a.is_group && (!types || types.includes(a.type)) && (!roles || (a.role !== null && roles.includes(a.role))));
  return (
    <Field label={label}>
      <select className="field" value={value} onChange={(e) => onChange(e.target.value)}>
        {allowEmpty !== undefined && <option value="">{allowEmpty}</option>}
        {allowEmpty === undefined && value === "" && <option value="">انتخاب کنید…</option>}
        {TYPE_ORDER.filter((t) => usable.some((a) => a.type === t)).map((type) => (
          <optgroup key={type} label={ACCOUNT_TYPE_LABEL[type]}>
            {usable
              .filter((a) => a.type === type)
              .map((a) => (
                <option key={a.id} value={a.id}>
                  {fa(a.code)} · {a.name}
                </option>
              ))}
          </optgroup>
        ))}
      </select>
    </Field>
  );
}

export function VendorSelect({ label, vendors, value, onChange, allowEmpty }: { label: string; vendors: Vendor[]; value: string; onChange: (id: string) => void; allowEmpty?: string }) {
  return (
    <Field label={label}>
      <select className="field" value={value} onChange={(e) => onChange(e.target.value)}>
        {allowEmpty !== undefined ? <option value="">{allowEmpty}</option> : value === "" && <option value="">انتخاب کنید…</option>}
        {vendors
          .filter((v) => v.active)
          .map((v) => (
            <option key={v.id} value={v.id}>
              {v.name}
            </option>
          ))}
      </select>
    </Field>
  );
}
