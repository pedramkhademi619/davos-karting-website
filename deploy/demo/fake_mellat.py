"""A stand-in for Bank Mellat's web service, for testing the payment flow on a development machine only.

It speaks the same SOAP operations the adapter calls (bpPayRequest, bpVerifyRequest, bpInquiryRequest, bpSettleRequest,
bpReversalRequest) with the documented result codes, keeps every sale in memory, and has a small control API a test
script uses in place of the customer's browser:

    POST /control/pay      {"ref_id": ..., "ok": true}  -> the "customer" pays or abandons; returns the callback fields
    POST /control/mode     {"mode": "normal" | "timeout" | "error500" | "garbage"}   fault injection for the SOAP side
    GET  /control/state    every sale, for assertions (amounts, how often each operation was called)

Nothing here talks to a real bank, and it must never be reachable from outside the machine.
"""

from __future__ import annotations

import json
import re
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LOCK = threading.Lock()
SALES: dict[str, dict] = {}  # ref_id -> sale
BY_ORDER: dict[int, str] = {}  # order id -> ref_id
CALLS: dict[str, int] = {}
MODE = {"value": "normal"}

SOAP_OK = (
    '<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">'
    '<soap:Body><ns:{op}Response xmlns:ns="http://interfaces.core.sw.bps.com/"><return>{value}</return>'
    "</ns:{op}Response></soap:Body></soap:Envelope>"
)


def field(body: str, name: str) -> str:
    match = re.search(rf"<{name}>([^<]*)</{name}>", body)
    return match.group(1) if match else ""


def handle_soap(body: str) -> str:
    operation = re.search(r"<(?:\w+:)?(bp\w+Request)", body)
    if not operation:
        return "34"
    op = operation.group(1)
    with LOCK:
        CALLS[op] = CALLS.get(op, 0) + 1
        if op == "bpPayRequest":
            order_id, amount = int(field(body, "orderId")), int(field(body, "amount"))
            if order_id in BY_ORDER:
                return "51"  # the same order id sent twice: the bank refuses it
            ref_id = secrets.token_hex(8).upper()
            SALES[ref_id] = {
                "ref_id": ref_id,
                "order_id": order_id,
                "amount": amount,
                "callback": field(body, "callBackUrl"),
                "state": "created",
                "sale_reference": None,
            }
            BY_ORDER[order_id] = ref_id
            return f"0,{ref_id}"
        order_id, sale_ref = int(field(body, "saleOrderId") or 0), field(body, "saleReferenceId")
        sale = SALES.get(BY_ORDER.get(order_id, ""))
        if sale is None or sale["sale_reference"] != sale_ref or sale["state"] == "created":
            return "42"  # no such paid sale
        if op == "bpVerifyRequest":
            if sale["state"] == "verified" or sale["state"] == "settled":
                return "43"
            if sale["state"] == "reversed":
                return "48"
            sale["state"] = "verified"
            return "0"
        if op == "bpInquiryRequest":
            return "0" if sale["state"] in {"paid", "verified", "settled"} else "48"
        if op == "bpSettleRequest":
            if sale["state"] == "settled":
                return "45"
            if sale["state"] == "reversed":
                return "48"
            if sale["state"] != "verified":
                return "46"
            sale["state"] = "settled"
            return "0"
        if op == "bpReversalRequest":
            if sale["state"] == "reversed":
                return "48"
            if sale["state"] == "settled":
                return "55"
            sale["state"] = "reversed"
            return "0"
    return "34"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args) -> None:  # keep the test output quiet
        return

    def _send(self, status: int, payload: str, content_type: str = "text/xml") -> None:
        data = payload.encode()
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _json(self, status: int, value: object) -> None:
        self._send(status, json.dumps(value), "application/json")

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8", errors="replace")
        if self.path.startswith("/pgwchannel/services/pgw"):
            mode = MODE["value"]
            if mode == "timeout":
                time.sleep(60)
            if mode == "error500":
                return self._send(500, "boom")
            if mode == "garbage":
                return self._send(200, "<html>not soap</html>")
            op = re.search(r"<(?:\w+:)?(bp\w+Request)", body)
            value = handle_soap(body)
            return self._send(200, SOAP_OK.format(op=op.group(1)[:-7] if op else "bp", value=value))
        if self.path == "/control/pay":
            request = json.loads(body or "{}")
            with LOCK:
                sale = SALES.get(request.get("ref_id", ""))
                if sale is None:
                    return self._json(404, {"error": "unknown ref_id"})
                if request.get("ok", True):
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
                return self._json(200, {"callback": sale["callback"], "fields": fields})
        if self.path == "/control/mode":
            MODE["value"] = json.loads(body or "{}").get("mode", "normal")
            return self._json(200, {"mode": MODE["value"]})
        self._json(404, {"error": "not found"})

    def do_GET(self) -> None:
        if self.path == "/control/state":
            with LOCK:
                return self._json(200, {"sales": list(SALES.values()), "calls": CALLS, "mode": MODE["value"]})
        self._send(200, "<html><body>fake bank</body></html>", "text/html")


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 9099), Handler).serve_forever()
