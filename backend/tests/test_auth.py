from datetime import timedelta

import jwt
from sqlalchemy import select

from app import mailer
from app.config import settings
from app.models import EmailToken, RefreshToken, User
from app.security import (
    create_access_token,
    hash_password,
    legacy_hash,
    sha256,
    utcnow,
)

from .conftest import PASSWORD, auth, login, register, token_from_mail


def test_register_hashes_with_argon2id_and_sends_verification(client, session_factory):
    register(client, "a@example.com")
    with session_factory() as db:
        user = db.scalar(select(User))
        assert user.password_hash.startswith("$argon2id$")
        assert not user.email_verified
    assert mailer.outbox[-1].to == "a@example.com"


def test_duplicate_email_rejected(client):
    register(client, "a@example.com")
    r = client.post(
        "/auth/register", json={"email": "A@example.com", "name": "x", "password": PASSWORD}
    )
    assert r.status_code == 409


def test_short_password_rejected(client):
    r = client.post(
        "/auth/register", json={"email": "a@example.com", "name": "x", "password": "short"}
    )
    assert r.status_code == 422


def test_login_wrong_password_and_unknown_email_look_the_same(client):
    register(client, "a@example.com")
    bad = client.post("/auth/login", json={"email": "a@example.com", "password": "nope-nope-nope"})
    unknown = client.post("/auth/login", json={"email": "z@example.com", "password": PASSWORD})
    assert bad.status_code == unknown.status_code == 401
    assert bad.json() == unknown.json()


def test_unverified_user_can_log_in_but_not_post(client):
    register(client, "a@example.com")
    headers = auth(login(client, "a@example.com"))
    r = client.post(
        "/skills", headers=headers, json={"skill": "x", "type": "offer", "description": "y"}
    )
    assert r.status_code == 403


def test_email_verification_unlocks_posting_and_token_is_single_use(client):
    register(client, "a@example.com")
    token = token_from_mail()
    assert client.post("/auth/verify-email", json={"token": token}).json()["email_verified"]
    assert client.post("/auth/verify-email", json={"token": token}).status_code == 400
    headers = auth(login(client, "a@example.com"))
    r = client.post(
        "/skills", headers=headers, json={"skill": "x", "type": "offer", "description": "y"}
    )
    assert r.status_code == 201


def test_expired_verification_token_rejected(client, session_factory):
    register(client, "a@example.com")
    with session_factory() as db:
        row = db.scalar(select(EmailToken))
        row.expires_at = utcnow() - timedelta(minutes=1)
        db.commit()
    assert client.post("/auth/verify-email", json={"token": token_from_mail()}).status_code == 400


def test_garbage_and_wrong_purpose_tokens_rejected(client):
    register(client, "a@example.com")
    assert client.post("/auth/verify-email", json={"token": "x" * 40}).status_code == 400
    # a verification token must not work as a password-reset token
    r = client.post(
        "/auth/reset-password", json={"token": token_from_mail(), "new_password": "another long pw"}
    )
    assert r.status_code == 400


def test_access_token_expiry(client, make_user):
    headers, user_id = make_user("a@example.com")
    assert client.get("/auth/me", headers=headers).status_code == 200
    expired = jwt.encode(
        {"sub": str(user_id), "type": "access", "exp": utcnow() - timedelta(seconds=5)},
        settings.jwt_secret,
        algorithm="HS256",
    )
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert r.status_code == 401


def test_forged_and_wrong_type_jwts_rejected(client, make_user):
    _, user_id = make_user("a@example.com")
    forged = jwt.encode(
        {"sub": str(user_id), "type": "access", "exp": utcnow() + timedelta(minutes=5)},
        "an-attacker-secret-that-is-long-enough",
        "HS256",
    )
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {forged}"}).status_code == 401
    none_alg = jwt.encode({"sub": str(user_id), "type": "access"}, None, algorithm="none")
    assert (
        client.get("/auth/me", headers={"Authorization": f"Bearer {none_alg}"}).status_code == 401
    )
    wrong = jwt.encode(
        {"sub": str(user_id), "type": "refresh", "exp": utcnow() + timedelta(minutes=5)},
        settings.jwt_secret,
        algorithm="HS256",
    )
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {wrong}"}).status_code == 401
    real = {"Authorization": f"Bearer {create_access_token(user_id)}"}
    assert client.get("/auth/me", headers=real).status_code == 200


def test_refresh_rotates_and_old_token_is_dead(client, make_user):
    make_user("a@example.com")
    first = login(client, "a@example.com")
    second = client.post("/auth/refresh", json={"refresh_token": first["refresh_token"]})
    assert second.status_code == 200
    assert second.json()["refresh_token"] != first["refresh_token"]
    assert client.get("/auth/me", headers=auth(second.json())).status_code == 200


def test_refresh_token_reuse_revokes_the_whole_family(client, make_user):
    make_user("a@example.com")
    t1 = login(client, "a@example.com")
    t2 = client.post("/auth/refresh", json={"refresh_token": t1["refresh_token"]}).json()
    # attacker replays the already-rotated t1
    replay = client.post("/auth/refresh", json={"refresh_token": t1["refresh_token"]})
    assert replay.status_code == 401
    # the legitimate newest token of that family is now revoked too
    assert (
        client.post("/auth/refresh", json={"refresh_token": t2["refresh_token"]}).status_code == 401
    )


def test_reuse_only_revokes_its_own_family(client, make_user):
    make_user("a@example.com")
    laptop = login(client, "a@example.com")
    phone = login(client, "a@example.com")
    client.post("/auth/refresh", json={"refresh_token": laptop["refresh_token"]})
    client.post("/auth/refresh", json={"refresh_token": laptop["refresh_token"]})  # reuse
    assert (
        client.post("/auth/refresh", json={"refresh_token": phone["refresh_token"]}).status_code
        == 200
    )


def test_expired_refresh_token_rejected(client, make_user, session_factory):
    make_user("a@example.com")
    tokens = login(client, "a@example.com")
    with session_factory() as db:
        for row in db.scalars(select(RefreshToken)):
            row.expires_at = utcnow() - timedelta(seconds=1)
        db.commit()
    r = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 401


def test_unknown_refresh_token_rejected(client):
    assert client.post("/auth/refresh", json={"refresh_token": "x" * 40}).status_code == 401


def test_logout_revokes_the_family(client, make_user):
    make_user("a@example.com")
    tokens = login(client, "a@example.com")
    assert (
        client.post("/auth/logout", json={"refresh_token": tokens["refresh_token"]}).status_code
        == 204
    )
    assert (
        client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code
        == 401
    )


def test_old_pbkdf2_hash_is_upgraded_on_login(client, session_factory):
    with session_factory() as db:
        db.add(
            User(
                email="old@example.com",
                name="Old",
                password_hash=legacy_hash(PASSWORD),
                email_verified=True,
            )
        )
        db.commit()
    login(client, "old@example.com")
    with session_factory() as db:
        assert db.scalar(select(User)).password_hash.startswith("$argon2id$")
    login(client, "old@example.com")  # still works with the new hash


def test_wrong_password_does_not_rehash_legacy(client, session_factory):
    stored = legacy_hash(PASSWORD)
    with session_factory() as db:
        db.add(User(email="old@example.com", name="Old", password_hash=stored))
        db.commit()
    r = client.post(
        "/auth/login", json={"email": "old@example.com", "password": "wrong-wrong-wrong"}
    )
    assert r.status_code == 401
    with session_factory() as db:
        assert db.scalar(select(User)).password_hash == stored


def test_argon2_hash_with_weaker_parameters_is_upgraded(client, session_factory):
    from argon2 import PasswordHasher

    weak = PasswordHasher(time_cost=1, memory_cost=8, parallelism=1).hash(PASSWORD)
    with session_factory() as db:
        db.add(User(email="w@example.com", name="W", password_hash=weak))
        db.commit()
    login(client, "w@example.com")
    with session_factory() as db:
        assert db.scalar(select(User)).password_hash != weak


def test_password_reset_flow(client, make_user):
    make_user("a@example.com")
    old_tokens = login(client, "a@example.com")
    r = client.post("/auth/forgot-password", json={"email": "a@example.com"})
    assert r.status_code == 202
    token = token_from_mail()
    new_pw = "a brand new password"
    assert (
        client.post(
            "/auth/reset-password", json={"token": token, "new_password": new_pw}
        ).status_code
        == 204
    )
    # old password dead, new one works, old sessions revoked
    bad = client.post("/auth/login", json={"email": "a@example.com", "password": PASSWORD})
    assert bad.status_code == 401
    login(client, "a@example.com", new_pw)
    assert (
        client.post(
            "/auth/refresh", json={"refresh_token": old_tokens["refresh_token"]}
        ).status_code
        == 401
    )


def test_reset_token_is_single_use(client, make_user):
    make_user("a@example.com")
    client.post("/auth/forgot-password", json={"email": "a@example.com"})
    token = token_from_mail()
    body = {"token": token, "new_password": "a brand new password"}
    assert client.post("/auth/reset-password", json=body).status_code == 204
    assert client.post("/auth/reset-password", json=body).status_code == 400


def test_reset_token_expires(client, make_user, session_factory):
    make_user("a@example.com")
    client.post("/auth/forgot-password", json={"email": "a@example.com"})
    with session_factory() as db:
        row = db.scalars(select(EmailToken).where(EmailToken.purpose == "reset")).one()
        row.expires_at = utcnow() - timedelta(seconds=1)
        db.commit()
    body = {"token": token_from_mail(), "new_password": "a brand new password"}
    assert client.post("/auth/reset-password", json=body).status_code == 400


def test_forgot_password_does_not_reveal_whether_an_email_exists(client, make_user):
    make_user("a@example.com")
    known = client.post("/auth/forgot-password", json={"email": "a@example.com"})
    before = len(mailer.outbox)
    unknown = client.post("/auth/forgot-password", json={"email": "nobody@example.com"})
    assert known.status_code == unknown.status_code == 202
    assert known.json() == unknown.json()
    assert len(mailer.outbox) == before  # nothing sent to an unregistered address


def test_only_token_hashes_are_stored(client, session_factory):
    register(client, "a@example.com")
    raw = token_from_mail()
    with session_factory() as db:
        row = db.scalar(select(EmailToken))
        assert row.token_hash == sha256(raw) and raw not in row.token_hash


def test_hash_password_is_salted():
    assert hash_password("same password here") != hash_password("same password here")


def test_documented_tradeoff_access_token_outlives_logout_until_expiry(client, make_user):
    """README 'Known limitations': logout revokes refresh tokens, not issued access tokens,
    which stay valid for at most access_ttl_minutes. If this changes, update the README."""
    make_user("a@example.com")
    tokens = login(client, "a@example.com")
    client.post("/auth/logout", json={"refresh_token": tokens["refresh_token"]})
    assert client.get("/auth/me", headers=auth(tokens)).status_code == 200
    claims = jwt.decode(tokens["access_token"], settings.jwt_secret, algorithms=["HS256"])
    assert claims["exp"] - claims["iat"] == settings.access_ttl_minutes * 60 == 15 * 60


def test_documented_tradeoff_register_reveals_existing_email(client):
    """README 'Known limitations': register answers 409 for a taken email (enumeration)."""
    register(client, "a@example.com")
    body = {"email": "a@example.com", "name": "x", "password": PASSWORD}
    assert client.post("/auth/register", json=body).status_code == 409
