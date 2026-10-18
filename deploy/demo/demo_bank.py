"""A stand-in payment page for the client demo. NO real bank and NO money: it plays the part of Bank Mellat so a visitor can
finish a booking. The SOAP side is fake_mellat (the same file the payment tests use); this adds the page the customer sees.

    browser --POST RefId--> /demo-bank/pay        (the page: "pay" or "cancel")
    browser --POST--------> /demo-bank/finish     (marks the sale paid/abandoned, then posts the result to the site's callback,
                                                   exactly as the bank would)

Served under /demo-bank/ by the server's nginx (the prefix is stripped). Must never be used for a real shop.
"""

from __future__ import annotations

import html
import secrets
from urllib.parse import parse_qs, urlsplit

import fake_mellat as fm

PAGE = """<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>درگاه آزمایشی پرداخت</title>
<style>
body{{margin:0;min-height:100vh;display:grid;place-items:center;background:#0f1013;color:#f4f4f5;font-family:Tahoma,sans-serif}}
main{{width:min(92vw,420px);background:#191b20;border:1px solid #2a2d34;border-radius:24px;padding:28px;text-align:center}}
.tag{{display:inline-block;background:#ffc400;color:#111;border-radius:99px;padding:4px 12px;font-size:12px;font-weight:700}}
h1{{font-size:20px;margin:16px 0 6px}}p{{color:#a1a1aa;line-height:1.9;font-size:14px;margin:6px 0}}
.amount{{font-size:30px;font-weight:700;margin:18px 0;color:#ffc400}}
button{{width:100%;height:52px;border-radius:99px;border:0;font-size:16px;font-weight:700;cursor:pointer;margin-top:10px}}
.ok{{background:#ffc400;color:#111}}.no{{background:transparent;color:#f4f4f5;border:1px solid #3a3d45}}
</style></head><body><main>{body}</main></body></html>"""


def page(body: str) -> str:
    return PAGE.format(body=body)


def pay_page(ref_id: str, amount_rial: int) -> str:
    toman = f"{amount_rial // 10:,}"
    ref = html.escape(ref_id)
    return page(
        f"""<span class="tag">نسخه‌ی نمایشی</span><h1>درگاه آزمایشی پرداخت</h1>
<p>این صفحه بانک واقعی نیست و هیچ پولی برداشته نمی‌شود؛ فقط برای دیدن مراحل رزرو است.</p>
<div class="amount">{toman} تومان</div>
<form method="post" action="/demo-bank/finish"><input type="hidden" name="RefId" value="{ref}">
<button class="ok" name="result" value="ok">پرداخت موفق</button>
<button class="no" name="result" value="cancel">انصراف از پرداخت</button></form>"""
    )


def message_page(text: str) -> str:
    return page(f'<span class="tag">نسخه‌ی نمایشی</span><h1>{html.escape(text)}</h1>')


def callback_page(url: str, fields: dict[str, str]) -> str:
    inputs = "".join(f'<input type="hidden" name="{html.escape(k)}" value="{html.escape(v)}">' for k, v in fields.items())
    return (
        '<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"></head>'
        f'<body onload="document.forms[0].submit()"><form method="post" action="{html.escape(url)}">{inputs}'
        '<noscript><button>ادامه</button></noscript></form></body></html>'
    )


def finish(ref_id: str, ok: bool) -> tuple[str, dict[str, str]] | None:
    """Same bookkeeping as fake_mellat's /control/pay; returns the callback address and the form the bank would post."""
    with fm.LOCK:
        sale = fm.SALES.get(ref_id)
        if sale is None:
            return None
        if ok:
            sale["state"] = "paid"
            sale["sale_reference"] = str(secrets.randbelow(10**11) + 10**11)
            fields = {
                "RefId": sale["ref_id"],
                "ResCode": "0",
                "SaleOrderId": str(sale["order_id"]),
                "SaleReferenceId": sale["sale_reference"],
            }
        else:
            sale["state"] = "abandoned"
            fields = {"RefId": sale["ref_id"], "ResCode": "17", "SaleOrderId": str(sale["order_id"])}
        return sale["callback"], fields


class DemoHandler(fm.Handler):
    def _html(self, text: str, status: int = 200) -> None:
        self._send(status, text, "text/html")

    def _form(self) -> dict[str, str]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(min(length, 8192)).decode("utf-8", errors="replace")
        return {k: v[0] for k, v in parse_qs(raw, max_num_fields=20).items() if v}

    def do_GET(self) -> None:
        parts = urlsplit(self.path)
        if parts.path == "/pay":
            ref_id = parse_qs(parts.query).get("RefId", [""])[0]
            return self._pay(ref_id)
        if parts.path.startswith("/control/"):
            return self._json(404, {"error": "not found"})  # the fault-injection API is not exposed here
        return super().do_GET()

    def do_POST(self) -> None:
        path = urlsplit(self.path).path
        if path == "/pay":
            return self._pay(self._form().get("RefId", ""))
        if path == "/finish":
            form = self._form()
            outcome = finish(form.get("RefId", ""), form.get("result") == "ok")
            if outcome is None:
                return self._html(message_page("این پرداخت پیدا نشد یا منقضی شده است."), 404)
            return self._html(callback_page(*outcome))
        if path.startswith("/control/"):
            return self._json(404, {"error": "not found"})
        return super().do_POST()

    def _pay(self, ref_id: str) -> None:
        with fm.LOCK:
            sale = fm.SALES.get(ref_id)
            amount = sale["amount"] if sale and sale["state"] == "created" else None
        if amount is None:
            return self._html(message_page("این پرداخت پیدا نشد یا قبلاً انجام شده است."), 404)
        return self._html(pay_page(ref_id, amount))


if __name__ == "__main__":
    fm.ThreadingHTTPServer(("0.0.0.0", 9099), DemoHandler).serve_forever()
