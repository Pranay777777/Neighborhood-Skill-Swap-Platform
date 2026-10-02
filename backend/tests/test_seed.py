from sqlalchemy import func, select

from app.models import Skill, User
from app.seed import DEMO_ACCOUNTS, DEMO_SKILLS, seed_demo

from .conftest import auth, login


def test_demo_accounts_log_in_and_can_post(client, session_factory):
    with session_factory() as db:
        seed_demo(db)
    for account in DEMO_ACCOUNTS:
        me = client.get(
            "/auth/me", headers=auth(login(client, account["email"], account["password"]))
        ).json()
        assert me["email_verified"]
    assert len(client.get("/skills").json()) == len(DEMO_SKILLS)


def test_reseeding_heals_a_defaced_demo(client, session_factory):
    with session_factory() as db:
        seed_demo(db)
    teacher = DEMO_ACCOUNTS[0]
    headers = auth(login(client, teacher["email"], teacher["password"]))
    for skill in client.get("/skills").json():
        if skill["owner_id"] == client.get("/auth/me", headers=headers).json()["id"]:
            client.delete(f"/skills/{skill['id']}", headers=headers)
    client.post(
        "/skills", headers=headers, json={"skill": "spam", "type": "offer", "description": "x"}
    )
    with session_factory() as db:
        seed_demo(db)
        assert db.scalar(select(func.count()).select_from(User)) == len(DEMO_ACCOUNTS)
        assert sorted(db.scalars(select(Skill.skill))) == sorted(s[1] for s in DEMO_SKILLS)


def test_reseeding_leaves_other_users_alone(client, session_factory, make_user):
    headers, _ = make_user("neighbour@example.com")
    client.post(
        "/skills", headers=headers, json={"skill": "Bread", "type": "offer", "description": "x"}
    )
    with session_factory() as db:
        seed_demo(db)
        seed_demo(db)
        assert "Bread" in set(db.scalars(select(Skill.skill)))
