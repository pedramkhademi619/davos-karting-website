import type { StartPayment } from "@/lib/types";

/**
 * Sends the browser to the bank. The amount and the bank reference come from our API (never from the page), and the target
 * must be one of the known payment hosts, so a tampered response cannot send a customer to a look-alike page.
 * Bank Mellat (Behpardakht) expects a POST form with RefId; Zarinpal a plain redirect.
 */
const PAYMENT_HOSTS = new Set(["bpm.shaparak.ir", "payment.zarinpal.com", "sandbox.zarinpal.com", "www.zarinpal.com"]);

export function goToGateway(start: StartPayment): void {
  const target = new URL(start.redirect_url, window.location.origin);
  const sameOrigin = target.origin === window.location.origin;
  if (!sameOrigin && (target.protocol !== "https:" || !PAYMENT_HOSTS.has(target.hostname))) {
    throw new Error("unexpected payment address");
  }

  if (start.method === "POST") {
    const form = document.createElement("form");
    form.method = "POST";
    form.action = target.toString();
    for (const [name, value] of Object.entries(start.form_fields)) {
      const input = document.createElement("input");
      input.type = "hidden";
      input.name = name;
      input.value = value;
      form.appendChild(input);
    }
    document.body.appendChild(form);
    form.submit();
    return;
  }
  window.location.assign(target.toString());
}
