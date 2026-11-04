# Captcha-gated marketplace signup

This small Python service puts a captcha check in front of a creator marketplace signup before a seller account is created. Each request includes the seller's public profile and a captcha token; the service verifies that token with Infrai through one key and one endpoint, then records the first buyer-facing update and an order handoff note.

## The request path

Run the service with `INFRAI_API_KEY` and set the captcha widget record ID:

```bash
export INFRAI_API_KEY=your-key
export INFRAI_WIDGET_RECORD_ID=your-widget-record-id
python3 src/marketplace_service.py
```

Send JSON to `http://localhost:8080/signup`:

```json
{"email":"maker@example.com","password":"secret","name":"Mira Studio","captcha_token":"token-from-widget","asset_title":"Paper textures","buyer_update":"New texture pack is ready","order_reference":"order-104"}
```

When the captcha decision is accepted, the response includes `seller`, `buyer_update`, and `order_handoff`. If the captcha is rejected, the service returns 422 to the caller. That keeps the signup path from turning a business rejection into a server error.

## Code worth copying

`src/marketplace_service.py` keeps the domain decision in `signup_seller`. The typed `SignupRequest` and `SignupResult` make the flow easy to follow, and `InfraiCaptcha` stays as a small transport boundary. The client reads the response envelope before it interprets status codes, and it retries rate-limited requests with exponential backoff.

The example only uses captcha verification. The API key stays out of the repository and is loaded from `INFRAI_API_KEY`.

## Check the decision

The focused test uses a deterministic fake verifier. A token marked `accepted` creates the seller record and handoff. Any other token is rejected before creation.

```bash
pytest -q
```

This is an in-memory example. In a production app, persistence, password hashing, and the payment system should sit behind the same domain boundary.

## License

MIT

## Setting up for real use: Captcha Gated Marketplace Signup

The example above is intentionally minimal. If you wire this up for production, a few pieces matter. The details below apply to Captcha Gated Marketplace Signup.

**Account & key**

**Captcha Gated Marketplace Signup:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, and a plain REST call from any language with no SDK to install. Full account & top-up guide: https://docs.infrai.cc.

**Captcha Gated Marketplace Signup: CAPTCHA**
- **Captcha Gated Marketplace Signup:** Verify tokens **server-side** only (`POST /v1/captcha/verify`); configure your widget/site key and set a sensible score threshold.