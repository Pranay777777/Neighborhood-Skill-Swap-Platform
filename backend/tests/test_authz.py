"""Authorization: user B must never read or change user A's objects (IDOR).

OWNED lists every route that reads or changes an owned object. Each case runs as an
attacker (403/404 expected, object unchanged) and as the rightful user (success), so a
route that is simply broken cannot pass. test_every_route_is_classified fails when a
new route is added without deciding which list it belongs to.
"""

from dataclasses import dataclass

import pytest
from fastapi.routing import APIRoute

from app.main import app


@dataclass(frozen=True)
class Case:
    method: str
    path: str  # {skill}, {comment}, {request} are filled from the fixture
    rule: str  # the README's route -> rule table is this column
    owner: str  # which fixture user may do it: "alice" (skill owner) | "carol" (requester)
    body: dict | None = None
    ok: int = 200


OWNED = [
    Case("PATCH", "/skills/{skill}", "skill owner only", "alice", {"description": "hacked"}),
    Case("DELETE", "/skills/{skill}", "skill owner only", "alice", ok=204),
    Case("DELETE", "/comments/{comment}", "comment author only", "alice", ok=204),
    Case("GET", "/requests/{request}", "requester or skill owner", "carol"),
    Case("PATCH", "/requests/{request}", "skill owner only", "alice", {"status": "accepted"}),
]

# Routes that take an id or act on "me" but are open by design (no owned object to leak).
PUBLIC = {
    ("GET", "/skills/{skill_id}"): "anyone; contact hidden unless signed in",
    ("POST", "/skills/{skill_id}/comments"): "any verified user",
    ("POST", "/skills/{skill_id}/requests"): "any verified user except the owner",
    ("GET", "/me/requests"): "scoped to the caller in the query",
    ("GET", "/auth/me"): "the caller only (from the token)",
}


@pytest.fixture()
def world(client, make_user):
    alice, _ = make_user("alice@example.com", "Alice")
    bob, _ = make_user("bob@example.com", "Bob")  # the attacker
    carol, _ = make_user("carol@example.com", "Carol")
    skill = client.post(
        "/skills",
        headers=alice,
        json={"skill": "Guitar", "type": "offer", "description": "Beginners", "contact": "a@x"},
    ).json()["id"]
    comment = client.post(
        f"/skills/{skill}/comments", headers=alice, json={"content": "Weekends only"}
    ).json()["id"]
    request = client.post(
        f"/skills/{skill}/requests", headers=carol, json={"message": "Private: my number is 555"}
    ).json()["id"]
    return {
        "users": {"alice": alice, "bob": bob, "carol": carol},
        "ids": {"skill": skill, "comment": comment, "request": request},
    }


def _call(client, case: Case, headers: dict, ids: dict):
    return client.request(case.method, case.path.format(**ids), headers=headers, json=case.body)


def _snapshot(client, world) -> dict:
    ids, users = world["ids"], world["users"]
    return {
        "skill": client.get(f"/skills/{ids['skill']}").json(),
        "request": client.get(f"/requests/{ids['request']}", headers=users["alice"]).json(),
    }


@pytest.mark.parametrize("case", OWNED, ids=lambda c: f"{c.method} {c.path}")
def test_other_user_is_refused_and_nothing_changes(client, world, case):
    before = _snapshot(client, world)
    r = _call(client, case, world["users"]["bob"], world["ids"])
    assert r.status_code in (403, 404), r.text
    assert "555" not in r.text  # the private message never leaks
    assert _snapshot(client, world) == before


@pytest.mark.parametrize("case", OWNED, ids=lambda c: f"{c.method} {c.path}")
def test_anonymous_is_refused(client, world, case):
    r = _call(client, case, {}, world["ids"])
    assert r.status_code == 401


@pytest.mark.parametrize("case", OWNED, ids=lambda c: f"{c.method} {c.path}")
def test_rightful_user_succeeds(client, world, case):
    r = _call(client, case, world["users"][case.owner], world["ids"])
    assert r.status_code == case.ok, r.text


def test_requester_can_read_but_not_answer_own_request(client, world):
    carol, rid = world["users"]["carol"], world["ids"]["request"]
    assert client.get(f"/requests/{rid}", headers=carol).status_code == 200
    r = client.patch(f"/requests/{rid}", headers=carol, json={"status": "accepted"})
    assert r.status_code == 403


def test_missing_and_forbidden_requests_look_identical(client, world):
    bob = world["users"]["bob"]
    forbidden = client.get(f"/requests/{world['ids']['request']}", headers=bob)
    missing = client.get("/requests/999999", headers=bob)
    assert forbidden.status_code == missing.status_code == 404
    assert forbidden.json() == missing.json()


def test_my_requests_only_lists_my_own(client, world):
    users = world["users"]
    assert client.get("/me/requests", headers=users["bob"]).json() == []
    assert len(client.get("/me/requests", headers=users["alice"]).json()) == 1  # received
    assert len(client.get("/me/requests", headers=users["carol"]).json()) == 1  # sent


def test_contact_details_hidden_from_anonymous(client, world):
    sid = world["ids"]["skill"]
    assert client.get(f"/skills/{sid}").json()["contact"] is None
    signed_in = client.get(f"/skills/{sid}", headers=world["users"]["bob"]).json()
    assert signed_in["contact"] == "a@x"


def test_owner_cannot_request_own_skill(client, world):
    r = client.post(
        f"/skills/{world['ids']['skill']}/requests",
        headers=world["users"]["alice"],
        json={"message": "hi"},
    )
    assert r.status_code == 400


def test_deleting_a_skill_removes_its_private_requests(client, world):
    users, ids = world["users"], world["ids"]
    assert client.delete(f"/skills/{ids['skill']}", headers=users["alice"]).status_code == 204
    assert client.get(f"/requests/{ids['request']}", headers=users["carol"]).status_code == 404
    assert client.get("/me/requests", headers=users["carol"]).json() == []


def test_every_route_is_classified():
    owned = {
        (
            c.method,
            c.path.replace("{skill}", "{skill_id}")
            .replace("{comment}", "{comment_id}")
            .replace("{request}", "{request_id}"),
        )
        for c in OWNED
    }
    unclassified = []
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        if "{" not in route.path and not route.path.endswith("/me") and "/me/" not in route.path:
            continue
        for method in route.methods:
            key = (method, route.path)
            if key not in owned and key not in PUBLIC:
                unclassified.append(key)
    assert not unclassified, f"add these to OWNED or PUBLIC in test_authz.py: {unclassified}"
