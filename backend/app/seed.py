"""Demo accounts for reviewers. Idempotent: re-running restores the demo accounts' password,
verified status and posts, so a defaced live demo heals on the next restart.

    python -m app.seed
"""

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .db import Base, SessionLocal, engine
from .models import Comment, RefreshToken, Skill, SwapRequest, User
from .security import hash_password

# Public on purpose: the README lists them. Mail to example.com is never delivered,
# so nobody can take these accounts over through a password reset.
DEMO_ACCOUNTS = [
    {"email": "demo.teacher@example.com", "name": "Demo Teacher", "password": "skillswap-demo-1"},
    {"email": "demo.learner@example.com", "name": "Demo Learner", "password": "skillswap-demo-2"},
]

DEMO_SKILLS = [
    (
        "demo.teacher@example.com",
        "Guitar Lessons",
        "offer",
        "Acoustic guitar for beginners. Weekends and evenings.",
    ),
    (
        "demo.teacher@example.com",
        "Vegetable Gardening",
        "offer",
        "Growing vegetables in small spaces: soil, seeds, watering.",
    ),
    (
        "demo.learner@example.com",
        "Spanish Conversation",
        "request",
        "Intermediate level, looking for weekly conversation practice.",
    ),
]


def seed_demo(db: Session) -> None:
    users = {}
    for account in DEMO_ACCOUNTS:
        user = db.scalar(select(User).where(User.email == account["email"]))
        if user is None:
            user = User(email=account["email"], name=account["name"], password_hash="")
            db.add(user)
        user.name = account["name"]
        user.password_hash = hash_password(account["password"])
        user.email_verified = True
        db.flush()
        users[account["email"]] = user

    ids = [u.id for u in users.values()]
    own_skills = select(Skill.id).where(Skill.owner_id.in_(ids))
    db.execute(delete(SwapRequest).where(SwapRequest.skill_id.in_(own_skills)))
    db.execute(delete(SwapRequest).where(SwapRequest.requester_id.in_(ids)))
    db.execute(delete(Comment).where(Comment.skill_id.in_(own_skills)))
    db.execute(delete(Comment).where(Comment.author_id.in_(ids)))
    db.execute(delete(Skill).where(Skill.owner_id.in_(ids)))
    db.execute(delete(RefreshToken).where(RefreshToken.user_id.in_(ids)))

    for email, skill, kind, description in DEMO_SKILLS:
        db.add(
            Skill(
                owner_id=users[email].id,
                skill=skill,
                type=kind,
                description=description,
                contact=email,
            )
        )
    db.commit()


if __name__ == "__main__":
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        seed_demo(session)
    print(f"seeded {len(DEMO_ACCOUNTS)} demo accounts")
