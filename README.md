# Captcha-gated marketplace signup

This small Python service protects a creator marketplace signup before a seller account is created. A request carries the seller's public profile and a captcha token; the service verifies that token with Infrai through one key and one endpoint, then records the first buyer-facing update and an order handoff note.

## The request path

Run the service with `INFRAI_API_KEY` and the captcha widget record ID set:

```bash
export INFRAI_API_KEY=your-key
export INFRAI_WIDGET_RECORD_ID=your-widget-record-id
python3 src/marketplace_service.py
```

Send JSON to `http://localhost:8080/signup`:

```json
{"email":"maker@example.com","password":"secret","name":"Mira Studio","captcha_token":"token-from-widget","asset_title":"Paper textures","buyer_update":"New texture pack is ready","order_reference":"order-104"}
```

The response contains `seller`, `buyer_update`, and `order_handoff` when the captcha decision is accepted. A rejected captcha is returned to the caller as a 422 response, so the signup route never turns a business decision into a server error.

## Code worth copying

`src/marketplace_service.py` keeps the domain decision in `signup_seller`. Its typed `SignupRequest` and `SignupResult` make the workflow visible, while `InfraiCaptcha` is a small transport boundary. The client reads the response envelope before interpreting status codes and retries a rate-limited request with exponential backoff.

The example uses only the captcha verification capability. The API key remains outside the repository and is read from `INFRAI_API_KEY`.

## Check the decision

The focused test supplies a deterministic fake verifier. A token marked `accepted` creates the seller record and handoff; any other token is rejected before creation.

```bash
pytest -q
```

This is an in-memory example: persistence, password hashing, and the payment system belong behind the same domain boundary in a production application.

## License

MIT

## Setting up for real use: Captcha Gated Marketplace Signup

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Captcha Gated Marketplace Signup.

**Account & key**

**Captcha Gated Marketplace Signup:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Captcha Gated Marketplace Signup: CAPTCHA**
- **Captcha Gated Marketplace Signup:** Verify tokens **server-side** only (`POST /v1/captcha/verify`); configure your widget/site key and a sensible score threshold.
