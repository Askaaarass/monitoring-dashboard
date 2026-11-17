# AQ Assistant and donations setup

## AQ Assistant

The public chat calls Django at `POST /api/assistant/chat/`; the Gemini key is
never sent to the browser. The official Google GenAI Python SDK uses the
Interactions API v1. Requests use `store=False`; the browser sends a bounded
conversation transcript for context, and Django supplies the project
knowledge base from `knowledge/*.md` plus active admin additions.

1. Copy `.env.example` to a local environment file or set the variables in the
   deployment environment. Do not commit credentials.
2. Set `DJANGO_SECRET_KEY` and `GEMINI_API_KEY` on the server.
3. Optionally select an account-enabled stable model with `GEMINI_MODEL`.
   The documented default is `gemini-3.6-flash`.
4. Install dependencies, run migrations, and restart Django.
5. In `/admin/`, staff can edit the assistant model, welcome message and
   requests-per-minute limit, and add supplemental knowledge documents.

The Markdown files in `knowledge/` are the editable baseline source. Do not put
secrets, personal information, unverified specifications or live sensor data
in the knowledge base.

## Donations and payment-provider onboarding

Public donations and payments are **disabled by default**. The project does
not yet have confirmed recipient legal details, a selected/approved merchant
account, or a provider adapter. Do not set `DONATIONS_ENABLED=true` until the
project owner has supplied and verified:

- The legal recipient, contact details, and authority to receive donations.
- The applicable public offer/agreement, privacy notice, cancellation and
  refund terms.
- The selected provider (for example Freedom Pay Kazakhstan or Halyk ePay)
  and written confirmation that its merchant account supports this voluntary
  donation use case.
- Sandbox credentials, callback signature rules, payment-status lookup
  access, and the exact hosted-checkout HTTPS hostname.

No recipient identity, provider approval, credentials, legal terms, or tax
status are asserted by this project. The current donation section explicitly
states that payments are unavailable.

`apps/donations/providers.py` defines the `PaymentProvider` contract. An
approved adapter must implement `createPayment`, `getPaymentStatus`,
`verifyCallback`, and (if authorized and supported) `processRefund`. The
backend accepts a provider class using `PAYMENT_PROVIDER_CLASS` and requires
the hosted checkout hostname in `PAYMENT_CHECKOUT_ALLOWED_HOSTS`. Set
`PUBLIC_SITE_URL` to the canonical HTTPS origin of the deployed site; payment
return and callback URLs use this configured origin rather than the incoming
browser `Host` header. Callback
verification must validate the provider's signature and independently fetch
the authoritative payment status. Never trust a browser return URL as proof
of payment; only a verified callback can update a donation to `PAID`.

The create-payment endpoint rejects requests until payments are enabled and
an adapter is configured. Even when enabling a completed adapter, use only
its sandbox first; use HTTPS in production and keep all credentials server
side. The application stores no card number or CVV.

## Endpoints

- `GET /api/assistant/config/` — public welcome text and availability only.
- `POST /api/assistant/chat/` — validated, rate-limited assistant request.
- `POST /api/donations/create/` — creates a hosted checkout session only when
  an approved adapter is configured and donations are enabled.
- `POST /api/donations/callback/` — provider-only callback, signature and
  status verification required in the adapter.
- `GET /api/donations/status/<uuid>/` — donation status without donor data.
- `GET /api/donations/statistics/` — aggregates confirmed payments only.
- `/api/donations/result/?id=<uuid>` — displays the server-side payment status.

## Validation

```powershell
$env:DJANGO_SECRET_KEY = "local-development-key"
python manage.py check
python manage.py test apps.assistant apps.donations
```

Tests mock the Gemini and payment providers. They do not make real API calls or
payments. Production credentials and merchant onboarding are not included.
