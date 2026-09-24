import json

import marketplace_service
from marketplace_service import CaptchaRejected, InfraiCaptcha, SignupRequest, signup_seller


class FakeCaptcha:
    def __init__(self, accepted: bool):
        self.accepted = accepted

    def verify(self, token: str, ip: str, action: str) -> None:
        if not self.accepted:
            raise CaptchaRejected({"message": "captcha rejected"})


def request() -> SignupRequest:
    return SignupRequest("maker@example.com", "secret", "Mira Studio", "accepted", "Paper textures", "Pack ready", "order-104")


def test_accepted_captcha_creates_seller_and_handoff() -> None:
    result = signup_seller(request(), FakeCaptcha(True))
    assert result.seller["asset_title"] == "Paper textures"
    assert result.order_handoff["status"] == "ready"


def test_rejected_captcha_stops_signup() -> None:
    try:
        signup_seller(request(), FakeCaptcha(False))
    except CaptchaRejected as exc:
        assert exc.status == 422
    else:
        raise AssertionError("signup should stop when captcha is rejected")


def test_infrai_captcha_sends_widget_record_id(monkeypatch) -> None:
    captured = {}

    class Response:
        status = 200
        headers = {}

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self):
            return b'{"ok": true}'

    def fake_urlopen(request, timeout):
        captured.update(json.loads(request.data))
        return Response()

    monkeypatch.setattr(marketplace_service, "urlopen", fake_urlopen)
    InfraiCaptcha("api-key", "widget-123").verify("token", "127.0.0.1", "marketplace_signup")

    assert captured["widget_record_id"] == "widget-123"
