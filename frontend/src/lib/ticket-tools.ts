import { dateTime, fa, jalali, karts, toman } from "@/lib/format";
import { venue } from "@/lib/venue";
import type { AccountPayment, Reservation } from "@/lib/types";

const ICS_STAMP = (date: Date) => date.toISOString().replace(/[-:]/g, "").replace(/\.\d{3}/, "");

function icsText(value: string): string {
  return value.replace(/\\/g, "\\\\").replace(/;/g, "\;").replace(/,/g, "\\,").replace(/\r?\n/g, "\\n");
}

/** Saves a file the browser generated itself (nothing is uploaded anywhere). */
function saveFile(name: string, type: string, content: string): void {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/** An .ics file for the ticket's session, with a reminder an hour before, for any calendar app. */
export function downloadCalendarEvent(ticket: Reservation): void {
  const start = new Date(ticket.starts_at);
  const end = new Date(start.getTime() + 30 * 60_000);
  const lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Davos Karting//FA",
    "CALSCALE:GREGORIAN",
    "BEGIN:VEVENT",
    `UID:${ticket.id}@davos-karting`,
    `DTSTAMP:${ICS_STAMP(new Date())}`,
    `DTSTART:${ICS_STAMP(start)}`,
    `DTEND:${ICS_STAMP(end)}`,
    `SUMMARY:${icsText(`کارتینگ داووس - بلیت ${ticket.ticket_number}`)}`,
    `DESCRIPTION:${icsText(`${karts(ticket.single_count, ticket.double_count)}\nشماره بلیت: ${ticket.ticket_number}\nتلفن: ${venue.phone.display}`)}`,
    `LOCATION:${icsText("پیست کارتینگ داووس")}`,
    `GEO:${venue.geo.latitude};${venue.geo.longitude}`,
    "BEGIN:VALARM",
    "TRIGGER:-PT60M",
    "ACTION:DISPLAY",
    `DESCRIPTION:${icsText("یک ساعت تا سانس کارتینگ")}`,
    "END:VALARM",
    "END:VEVENT",
    "END:VCALENDAR",
  ];
  saveFile(`davos-ticket-${ticket.ticket_number}.ics`, "text/calendar;charset=utf-8", lines.join("\r\n"));
}

const escapeHtml = (value: string) =>
  value.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");

/** Prints a one-page document through a hidden frame, so the page itself is left untouched. */
function printHtml(title: string, rows: [string, string][], footer: string): void {
  const body = rows
    .map(([label, value]) => `<tr><th>${escapeHtml(label)}</th><td>${escapeHtml(value)}</td></tr>`)
    .join("");
  const html = `<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><title>${escapeHtml(title)}</title>
<style>body{font-family:Tahoma,Vazirmatn,sans-serif;margin:32px;color:#0c0d10}h1{font-size:22px;border-bottom:3px solid #ffc400;padding-bottom:10px}
table{width:100%;border-collapse:collapse;margin-top:18px}th,td{padding:10px 8px;border-bottom:1px solid #ddd;text-align:right;font-size:14px}th{width:36%;color:#555;font-weight:600}
p{margin-top:24px;color:#555;font-size:12px;line-height:1.9}</style></head><body><h1>${escapeHtml(title)}</h1><table>${body}</table><p>${escapeHtml(footer)}</p></body></html>`;
  const frame = document.createElement("iframe");
  frame.setAttribute("aria-hidden", "true");
  frame.style.cssText = "position:fixed;width:0;height:0;border:0;right:0;bottom:0";
  frame.srcdoc = html;
  frame.onload = () => {
    frame.contentWindow?.focus();
    frame.contentWindow?.print();
    window.setTimeout(() => frame.remove(), 2000);
  };
  document.body.appendChild(frame);
}

export function printTicket(ticket: Reservation): void {
  printHtml(
    "بلیت داووس کارتینگ",
    [
      ["شماره بلیت", fa(ticket.ticket_number)],
      ["روز و ساعت", `${ticket.weekday} ${jalali(ticket.date_jalali)}، ساعت ${fa(ticket.time)}`],
      ["خودرو", karts(ticket.single_count, ticket.double_count)],
      ["نام", ticket.contact_name || "—"],
      ["مبلغ", toman(ticket.amount_toman)],
    ],
    "این برگه را همراه داشته باشید یا شماره بلیت را در پیست اعلام کنید.",
  );
}

export function printReceipt(payment: AccountPayment, ticket: Reservation | undefined): void {
  const rows: [string, string][] = [
    ["مبلغ پرداخت‌شده", toman(payment.amount_toman)],
    ["شماره پیگیری بانک", payment.reference_id ? fa(payment.reference_id) : "—"],
    ["زمان پرداخت", dateTime(payment.updated_at)],
  ];
  if (ticket) rows.push(["شماره بلیت", fa(ticket.ticket_number)], ["سانس", `${ticket.weekday} ${jalali(ticket.date_jalali)}، ${fa(ticket.time)}`]);
  printHtml("رسید پرداخت داووس کارتینگ", rows, "این رسید فقط برای اطلاع مشتری است.");
}
