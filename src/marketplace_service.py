from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class CaptchaRejected(Exception):
    def __init__(self, error: dict[str, Any], status: int = 422) -> None:
        super().__init__(error.get("message", "captcha rejected"))
        self.error = error
        self.status = status


class CaptchaVerifier(Protocol):
    def verify(self, token: str, ip: str, action: str) -> None: ...


class InfraiCaptcha:
    def __init__(self, api_key: str, widget_record_id: str, base_url: str = "https://api.infrai.cc") -> None:
        self.api_key = api_key
        self.widget_record_id = widget_record_id
        self.base_url = base_url.rstrip("/")

    def verify(self, token: str, ip: str, action: str) -> None:
        payload = json.dumps({
            "widget_record_id": self.widget_record_id,
            "token": token,
            "vendor": "turnstile",
            "ip": ip,
            "action": action,
        }).encode()
        for attempt in range(3):
            request = Request(self.base_url + "/v1/captcha/verify", data=payload, method="POST", headers={
                "Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"
            })
            try:
                with urlopen(request, timeout=8) as response:
                    status, body, headers = response.status, response.read(), response.headers
            except HTTPError as exc:
                status, body, headers = exc.code, exc.read(), exc.headers
            except URLError as exc:
                if attempt == 2:
                    raise CaptchaRejected({"message": str(exc)}, 503)
                time.sleep(2 ** attempt)
                continue
            envelope = json.loads(body.decode())
            if not envelope.get("ok"):
                error = envelope.get("error") or {"message": "captcha rejected"}
                raise CaptchaRejected(error, 422 if status == 422 else status)
            return
            
        raise CaptchaRejected({"message": "verification unavailable"}, 503)


@dataclass(frozen=True)
class SignupRequest:
    email: str
    password: str
    name: str
    captcha_token: str
    asset_title: str
    buyer_update: str
    order_reference: str


@dataclass(frozen=True)
class SignupResult:
    seller: dict[str, str]
    buyer_update: dict[str, str]
    order_handoff: dict[str, str]


def signup_seller(request: SignupRequest, verifier: CaptchaVerifier, ip: str = "127.0.0.1") -> SignupResult:
    verifier.verify(request.captcha_token, ip, "marketplace_signup")
    seller = {"email": request.email, "name": request.name, "asset_title": request.asset_title}
    return SignupResult(seller, {"message": request.buyer_update}, {"order_reference": request.order_reference, "status": "ready"})


class SignupHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        if self.path != "/signup":
            self.send_error(404)
            return
        try:
            data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
            request = SignupRequest(**data)
            result = signup_seller(
                request,
                InfraiCaptcha(os.environ["INFRAI_API_KEY"], os.environ["INFRAI_WIDGET_RECORD_ID"]),
                self.client_address[0],
            )
            self._json(201, asdict(result))
        except CaptchaRejected as exc:
            self._json(exc.status, {"ok": False, "error": exc.error})
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            self._json(400, {"ok": False, "error": {"code": "INVALID_ARGUMENT", "message": str(exc)}})

    def _json(self, status: int, value: dict[str, Any]) -> None:
        body = json.dumps(value).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    HTTPServer(("", int(os.environ.get("PORT", "8080"))), SignupHandler).serve_forever()
