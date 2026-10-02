"""Failure paths found on the live deployment: a delete racing a new comment on Postgres,
and a 500 that reached the browser without CORS headers (seen only as a network error)."""

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.deps import optional_user
from app.main import app

ORIGIN = settings.cors_origins.split(",")[0].strip()


def _fail_commits(monkeypatch, times: int) -> None:
    """Make the next `times` commits fail like a foreign-key violation from a concurrent write."""
    real = Session.commit
    left = {"n": times}

    def commit(self):
        if left["n"] > 0:
            left["n"] -= 1
            raise IntegrityError("DELETE FROM skills", {}, Exception("violates foreign key"))
        return real(self)

    monkeypatch.setattr(Session, "commit", commit)


@pytest.fixture()
def skill(client, make_user):
    headers, _ = make_user("owner@example.com")
    sid = client.post(
        "/skills", headers=headers, json={"skill": "Guitar", "type": "offer", "description": "x"}
    ).json()["id"]
    client.post(f"/skills/{sid}/comments", headers=headers, json={"content": "hi"})
    return headers, sid


def test_delete_retries_when_a_comment_lands_mid_delete(client, skill, monkeypatch):
    headers, sid = skill
    _fail_commits(monkeypatch, 1)
    assert client.delete(f"/skills/{sid}", headers=headers).status_code == 204
    assert client.get(f"/skills/{sid}").status_code == 404


def test_delete_gives_up_with_409_not_500(client, skill, monkeypatch):
    headers, sid = skill
    _fail_commits(monkeypatch, 2)
    r = client.delete(f"/skills/{sid}", headers=headers)
    assert r.status_code == 409
    monkeypatch.undo()
    assert client.get(f"/skills/{sid}").status_code == 200  # nothing half-deleted


@pytest.mark.parametrize("path", ["comments", "requests"])
def test_posting_onto_a_skill_deleted_meanwhile_is_404(client, skill, make_user, monkeypatch, path):
    _, sid = skill
    other, _ = make_user("neighbour@example.com")
    _fail_commits(monkeypatch, 1)
    body = {"content": "x"} if path == "comments" else {"message": "x"}
    r = client.post(f"/skills/{sid}/{path}", headers=other, json=body)
    assert r.status_code == 404


def test_unhandled_error_is_json_and_keeps_cors_headers(client):
    def boom():
        raise RuntimeError("database fell over")

    app.dependency_overrides[optional_user] = boom
    r = client.get("/skills", headers={"Origin": ORIGIN})
    assert r.status_code == 500
    assert r.json() == {"detail": "Something went wrong on our side"}
    assert r.headers["access-control-allow-origin"] == ORIGIN
    assert "database fell over" not in r.text  # internals stay in the log
