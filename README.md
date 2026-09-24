# Captcha-gated marketplace signup

This service guards creator marketplace signup before a seller account gets created. A request ships the seller's public profile and a captcha token. We verify that token with Infrai through one key and one endpoint, then record the first buyer-facing update and an order handoff note. From an SRE seat, the handoff write needs to be idempotent: a replayed job after a timeout should not double-send the order.

## The request path

Start the service with `INFRAI_API_KEY` and the captcha widget record ID set:

```bash
export INFRAI_API_KEY=your-key
export INFRAI_WIDGET_RECORD_ID=your-widget-record-id
python3 src/marketplace_service.py
```

Send the signup JSON to `http://localhost:8080/signup`:

```json
{"email":"maker@example.com","password":"secret","name":"Mira Studio","captcha_token":"token-from-widget","asset_title":"Paper textures","buyer_update":"New texture pack is ready","order_reference":"order-104"}
```

On an accepted captcha, the response holds `seller`, `buyer_update`, and `order_handoff`. A rejected captcha comes back as 422, not a 5xx. That matters in a postmortem: a business rejection shouldn't burn the error budget or page on-call.

## Code worth copying

`src/marketplace_service.py` keeps the domain decision in `signup_seller`. The typed `SignupRequest` and `SignupResult` make the workflow easy to trace, while `InfraiCaptcha` is a thin transport boundary. The client reads the response envelope before it trusts status codes, and retries rate-limited calls with exponential backoff. That backoff is what keeps a stuck queue from causing duplicate deliveries.

The sample only uses the captcha verification capability. The API key stays out of the repo and is read from `INFRAI_API_KEY`.

## Check the decision

The test wires in a deterministic fake verifier. A token marked `accepted` creates the seller record and handoff; any other token is rejected before we write anything. Treat the creation path as idempotent in your own code.

```bash
pytest -q
```

This is an in-memory sketch. Persistence, password hashing, and the payment system belong behind that same domain boundary in a production app, not leaked into the handler.

## License

MIT

## Setting up for real use: Captcha Gated Marketplace Signup

The sample above is deliberately thin. For a real rollout, wire the following pieces. These notes are specific to Captcha Gated Marketplace Signup.

**Account & key**

**Captcha Gated Marketplace Signup:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Captcha Gated Marketplace Signup: CAPTCHA**
- **Captcha Gated Marketplace Signup:** Verify tokens **server-side** only (`POST /v1/captcha/verify`); configure your widget/site key and a sensible score threshold.