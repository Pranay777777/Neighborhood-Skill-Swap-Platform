import os

os.environ["SWAP_MAIL_BACKEND"] = "memory"
os.environ["SWAP_DATABASE_URL"] = "sqlite://"

import re  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app import mailer  # noqa: E402
from app.db import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

PASSWORD = "correct horse battery"


@pytest.fixture()
def session_factory():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture()
def client(session_factory):
    def override():
        with session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override
    mailer.outbox.clear()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def token_from_mail(index: int = -1) -> str:
    return re.search(r"token=([\w-]+)", mailer.outbox[index].body).group(1)


def register(client, email: str, name: str = "Test User") -> None:
    r = client.post("/auth/register", json={"email": email, "name": name, "password": PASSWORD})
    assert r.status_code == 201, r.text


def login(client, email: str, password: str = PASSWORD) -> dict:
    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()


def auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture()
def make_user(client):
    """Create a verified user and return (headers, user_id)."""

    def _make(email: str, name: str = "Test User"):
        register(client, email, name)
        r = client.post("/auth/verify-email", json={"token": token_from_mail()})
        assert r.status_code == 200
        headers = auth(login(client, email))
        return headers, r.json()["id"]

    return _make
