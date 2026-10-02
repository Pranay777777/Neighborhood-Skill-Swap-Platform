import pytest

from app.config import settings

from .conftest import PASSWORD, register

ORIGIN = settings.cors_origins.split(",")[0].strip()
BAD_LOGIN = {"email": "a@example.com", "password": "wrong-password-x"}


def _limit(rule: str) -> int:
    return int(rule.split("/")[0])


def test_login_is_limited_per_client(client):
    for _ in range(_limit(settings.rate_limit_login)):
        assert client.post("/auth/login", json=BAD_LOGIN).status_code == 401
    r = client.post("/auth/login", json=BAD_LOGIN, headers={"Origin": ORIGIN})
    assert r.status_code == 429
    assert r.json() == {"detail": "Too many attempts. Wait a minute and try again."}
    assert r.headers["retry-after"] == "60"
    assert r.headers["access-control-allow-origin"] == ORIGIN  # the UI can show the message


def test_a_correct_password_is_limited_too(client):
    register(client, "a@example.com")
    good = {"email": "a@example.com", "password": PASSWORD}
    for _ in range(_limit(settings.rate_limit_login)):
        client.post("/auth/login", json=BAD_LOGIN)
    assert client.post("/auth/login", json=good).status_code == 429  # no free guess at the end


def test_register_is_limited(client):
    n = _limit(settings.rate_limit_register)
    for i in range(n):
        body = {"email": f"u{i}@example.com", "name": "x", "password": PASSWORD}
        assert client.post("/auth/register", json=body).status_code == 201
    body = {"email": "one-more@example.com", "name": "x", "password": PASSWORD}
    assert client.post("/auth/register", json=body).status_code == 429


def test_forgot_password_is_limited(client):
    for _ in range(_limit(settings.rate_limit_forgot)):
        assert (
            client.post("/auth/forgot-password", json={"email": "a@example.com"}).status_code == 202
        )
    r = client.post("/auth/forgot-password", json={"email": "a@example.com"})
    assert r.status_code == 429


def test_other_endpoints_are_not_limited(client):
    for _ in range(_limit(settings.rate_limit_login) + 5):
        assert client.get("/skills").status_code == 200


@pytest.fixture()
def behind_proxy(monkeypatch):
    monkeypatch.setattr(settings, "trust_proxy", True)


def _exhaust(client, headers):
    for _ in range(_limit(settings.rate_limit_login)):
        client.post("/auth/login", json=BAD_LOGIN, headers=headers)


def test_behind_the_proxy_each_client_has_its_own_budget(client, behind_proxy):
    _exhaust(client, {"X-Forwarded-For": "203.0.113.7"})
    blocked = client.post("/auth/login", json=BAD_LOGIN, headers={"X-Forwarded-For": "203.0.113.7"})
    other = client.post("/auth/login", json=BAD_LOGIN, headers={"X-Forwarded-For": "198.51.100.9"})
    assert (blocked.status_code, other.status_code) == (429, 401)


def test_a_forged_left_entry_does_not_buy_a_new_budget(client, behind_proxy):
    _exhaust(client, {"X-Forwarded-For": "203.0.113.7"})
    # the proxy appends the real address on the right; whatever the client sent sits left of it
    forged = {"X-Forwarded-For": "1.2.3.4, 203.0.113.7"}
    assert client.post("/auth/login", json=BAD_LOGIN, headers=forged).status_code == 429


def test_without_a_trusted_proxy_the_header_is_ignored(client):
    _exhaust(client, {"X-Forwarded-For": "203.0.113.7"})
    r = client.post("/auth/login", json=BAD_LOGIN, headers={"X-Forwarded-For": "198.51.100.9"})
    assert r.status_code == 429
