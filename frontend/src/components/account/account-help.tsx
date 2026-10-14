import Link from "next/link";
import { buttonClasses } from "@/components/button-link";
import { WorkingHours } from "@/components/working-hours";
import { ridingRules, site } from "@/content/site";

/** What a customer needs on the day: where, when, who may drive, who to call. */
export function AccountHelp() {
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <section className="panel space-y-4 p-6">
        <h3 className="text-xl font-black">پیست و ساعت کار</h3>
        <p className="leading-8 text-fg-muted">
          <WorkingHours />
        </p>
        <div className="flex flex-wrap gap-3">
          <a href={site.contact.phone.href} dir="ltr" className={buttonClasses("dark", "sm")}>
            {site.contact.phone.display}
          </a>
          <a href={site.contact.map.href} target="_blank" rel="noopener noreferrer" className={buttonClasses("ghost", "sm")}>
            {site.contact.map.label}
          </a>
        </div>
        <p className="text-sm leading-7 text-fg-muted">
          شماره بلیت را در پذیرش اعلام کنید. برای تغییر یا لغو بلیت قطعی با پیست تماس بگیرید.
        </p>
      </section>

      <section className="panel space-y-4 p-6">
        <h3 className="text-xl font-black">شرایط رانندگی</h3>
        <ul className="space-y-3">
          {ridingRules.map((rule) => (
            <li key={rule.badge} className="flex gap-3">
              <span className="race-number h-fit shrink-0 rounded-lg bg-accent px-2 py-1 text-xs font-black text-ink">{rule.badge}</span>
              <span className="text-sm leading-7 text-fg-muted">
                <strong className="text-fg">{rule.title}.</strong> {rule.text}
              </span>
            </li>
          ))}
        </ul>
      </section>

      <section className="panel-soft flex flex-wrap items-center justify-between gap-4 p-6 lg:col-span-2">
        <p className="font-bold">سوال دیگری دارید؟ پاسخ بیشتر در سوالات متداول و دستیار هوشمند سایت است.</p>
        <div className="flex flex-wrap gap-3">
          <Link href="/faq" className={buttonClasses("ghost", "sm")}>
            سوالات متداول
          </Link>
          <Link href={site.booking.href} className={buttonClasses("primary", "sm")}>
            رزرو جدید
          </Link>
        </div>
      </section>
    </div>
  );
}
