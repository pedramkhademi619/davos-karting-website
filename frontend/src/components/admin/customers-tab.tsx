"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useAdmin } from "@/components/admin/admin-session";
import { Pager, TabHeader, Table, cell } from "@/components/admin/admin-ui";
import { buttonClasses } from "@/components/button-link";
import { SearchIcon } from "@/components/icons";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { errorMessage } from "@/lib/api";
import { dateTime, fa, mobile, toLatinDigits } from "@/lib/format";
import type { Customer, Page } from "@/lib/types";

const LIMIT = 50;

export function CustomersTab() {
  const { call, isOwner } = useAdmin();
  const [query, setQuery] = useState("");
  const [submitted, setSubmitted] = useState("");
  const [offset, setOffset] = useState(0);
  const [page, setPage] = useState<Page<Customer> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [version, setVersion] = useState(0);

  useEffect(() => {
    let cancelled = false;
    call<Page<Customer>>("/customers", { query: { q: submitted, offset, limit: LIMIT } })
      .then((result) => !cancelled && setPage(result))
      .catch((err) => !cancelled && setError(errorMessage(err)));
    return () => {
      cancelled = true;
    };
  }, [call, submitted, offset, version]);

  function search(event: FormEvent) {
    event.preventDefault();
    setOffset(0);
    setSubmitted(toLatinDigits(query.trim()));
  }

  async function toggle(customer: Customer) {
    const next = customer.status === "active" ? "blocked" : "active";
    try {
      await call(`/customers/${customer.user_id}/status`, { method: "POST", body: { status: next } });
      setVersion((v) => v + 1);
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  return (
    <div>
      <TabHeader
        title="مشتریان"
        lead={page ? `${fa(page.total)} مشتری. هر کس با موبایل وارد سایت شود اینجا دیده می‌شود.` : undefined}
        actions={
          <form onSubmit={search} className="flex items-center gap-2">
            <input className="field h-11 w-60" placeholder="نام یا موبایل" value={query} onChange={(e) => setQuery(e.target.value)} aria-label="جستجوی مشتری" />
            <button type="submit" className={buttonClasses("dark", "sm", "h-11")} aria-label="جستجو">
              <SearchIcon className="h-5 w-5" />
            </button>
          </form>
        }
      />
      {error && (
        <Alert tone="error" className="mb-6">
          {error}
        </Alert>
      )}
      {!page ? (
        <Spinner className="h-8 w-8" />
      ) : (
        <>
          <Table head={["نام", "موبایل", "خبرنامه پیامکی", "عضویت", "وضعیت", ""]} empty={page.items.length === 0}>
            {page.items.map((c) => (
              <tr key={c.user_id}>
                <td className={`${cell} font-bold`}>{c.full_name || "—"}</td>
                <td className={cell} dir="ltr">
                  {mobile(c.mobile)}
                </td>
                <td className={cell}>{c.marketing_opt_in ? "بله" : "خیر"}</td>
                <td className={cell}>{dateTime(c.created_at)}</td>
                <td className={cell}>
                  <span className={`rounded-full px-3 py-1 text-xs font-bold ${c.status === "active" ? "bg-go-soft text-[#064d29]" : "bg-signal-soft text-[#7a0600]"}`}>
                    {c.status === "active" ? "فعال" : "مسدود"}
                  </span>
                </td>
                <td className={cell}>
                  {isOwner && (
                    <button type="button" onClick={() => toggle(c)} className="text-xs font-bold underline">
                      {c.status === "active" ? "مسدود کردن" : "رفع مسدودی"}
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </Table>
          <Pager offset={offset} limit={LIMIT} total={page.total} onChange={setOffset} />
        </>
      )}
    </div>
  );
}
