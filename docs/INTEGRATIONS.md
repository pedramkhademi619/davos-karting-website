# Integrations

## Booking system (existing, not rebuilt here)

Feature flag: `BOOKING_INTEGRATION_ENABLED` (default `false`). While it is off, the webhook and return endpoints answer `404`
and the booking CTA is a plain redirect to `BOOKING_BASE_URL`. **No SSO is claimed or active.**

### Webhook contract (booking system -> us)

`POST /api/v1/integrations/booking/webhook` - header `X-Davos-Signature: t=<unix seconds>,v1=<hex>`.

```json
{
  "event_id": "evt-2026-000123",
  "external_booking_id": "bk-90210",
  "user_id": "0b0f3c3e-6d6b-4a53-9a55-2f2d0c8c7f11",
  "status": "confirmed",
  "amount_irr": 500000,
  "session_time": "2026-10-03T16:00:00+03:30",
  "updated_at": "2026-09-20T09:15:00+03:30"
}
```

`status` is one of `pending | confirmed | cancelled | attended | no_show | refunded`. All timestamps must carry a timezone.
`amount_irr` is an integer number of Rial.

Signature: `HMAC_SHA256(secret, "<t>." + <raw request body bytes>)`, hex. Reject window: `|now - t| > 300s` (configurable).
During key rotation set `BOOKING_WEBHOOK_SECRET_PREVIOUS`; either key is accepted.

```python
import hashlib, hmac, time
body = raw_json_bytes
t = int(time.time())
sig = hmac.new(secret.encode(), f"{t}.".encode() + body, hashlib.sha256).hexdigest()
headers = {"X-Davos-Signature": f"t={t},v1={sig}"}
```

Responses: `202 {"outcome": "accepted" | "duplicate" | "stale_ignored"}`; `401` bad/expired signature (generic body);
`413` over 64 KiB; `422` contract violation; `409` event names a different customer for a known booking (parked for review).
Providers should retry on `5xx`. Duplicates are always safe to resend.

### Return page (customer browser)

`GET /api/v1/bookings/return?booking=<external_booking_id>` (signed-in customer). Only the booking reference is read from the
URL. The response comes from **our verified data**: until the signed webhook has arrived (or when the booking belongs to someone
else) the state is `pending_confirmation` / «در انتظار تایید». Query parameters such as `status=success` are ignored.

### Not implemented

Server-to-server booking inquiry and periodic reconciliation polling (the `BookingGatewayPort`), OIDC Authorization-Code + PKCE
identity handoff (`IdentityHandoffPort`), redirect allow-list for return URLs, linking verified bookings to loyalty points and
notifications (the events `booking.BookingVerified` / `booking.BookingStatusChanged` are published to the outbox; no consumer
is registered yet).

## Zarinpal (payments)

Feature flag: `PAYMENTS_ENABLED` (default `false`). Contract used (from the official documentation):
`POST {host}/pg/v4/payment/request.json` and `.../verify.json`, redirect `{host}/pg/StartPay/{authority}`, success code `100`,
already-verified `101`; the request states `currency: "IRR"` explicitly (no reliance on provider defaults) and sends the stored
integer Rial amount. Card numbers/hashes in the verify response are discarded; only `ref_id` is kept.

Timeouts and outages are **never** treated as failure: the attempt becomes `UNKNOWN` and the reconciliation use case retries
verification. Refunds are not exposed.

Sandbox testing without inventing products: set `PAYMENTS_SANDBOX_ORDERS_ENABLED=true` (refused in production); only order
refs shaped `sandbox-test-<n>` are payable, for a fixed 10,000 IRR. Booking payments remain in the existing booking system;
main-site payments stay off until a real order contract implements `OrderQuotePort`.

**Blocked:** no merchant id is available, so nothing has been exercised against the live Zarinpal sandbox.
