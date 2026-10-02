from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..db import get_db
from ..deps import optional_user, verified_user
from ..models import Comment, Skill, User
from ..schemas import CommentIn, CommentOut, SkillIn, SkillOut, SkillPatch

router = APIRouter(tags=["skills"])


def _comment_out(c: Comment) -> CommentOut:
    return CommentOut(
        id=c.id,
        author_id=c.author_id,
        author=c.author.name,
        content=c.content,
        created_at=c.created_at,
    )


def _skill_out(s: Skill, viewer: User | None) -> SkillOut:
    return SkillOut(
        id=s.id,
        owner_id=s.owner_id,
        name=s.owner.name,
        skill=s.skill,
        type=s.type,
        description=s.description,
        contact=s.contact if viewer else None,  # contact details are for signed-in neighbours
        created_at=s.created_at,
        comments=[_comment_out(c) for c in s.comments],
    )


def _load(db: Session, skill_id: int) -> Skill:
    skill = db.scalar(
        select(Skill)
        .where(Skill.id == skill_id)
        .options(selectinload(Skill.comments).selectinload(Comment.author))
    )
    if skill is None:
        raise HTTPException(404, "Skill not found")
    return skill


def _owned_skill(db: Session, skill_id: int, user: User) -> Skill:
    skill = _load(db, skill_id)
    if skill.owner_id != user.id:
        raise HTTPException(403, "Not your skill")
    return skill


@router.get("/skills", response_model=list[SkillOut])
def list_skills(db: Session = Depends(get_db), viewer: User | None = Depends(optional_user)):
    rows = db.scalars(
        select(Skill)
        .order_by(Skill.id.desc())
        .options(selectinload(Skill.comments).selectinload(Comment.author))
    ).all()
    return [_skill_out(s, viewer) for s in rows]


@router.get("/skills/{skill_id}", response_model=SkillOut)
def get_skill(
    skill_id: int, db: Session = Depends(get_db), viewer: User | None = Depends(optional_user)
):
    return _skill_out(_load(db, skill_id), viewer)


@router.post("/skills", status_code=201, response_model=SkillOut)
def create_skill(body: SkillIn, db: Session = Depends(get_db), user: User = Depends(verified_user)):
    skill = Skill(owner_id=user.id, **body.model_dump())
    db.add(skill)
    db.commit()
    return _skill_out(_load(db, skill.id), user)


@router.patch("/skills/{skill_id}", response_model=SkillOut)
def update_skill(
    skill_id: int,
    body: SkillPatch,
    db: Session = Depends(get_db),
    user: User = Depends(verified_user),
):
    skill = _owned_skill(db, skill_id, user)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(skill, field, value)
    db.commit()
    return _skill_out(skill, user)


@router.delete("/skills/{skill_id}", status_code=204)
def delete_skill(
    skill_id: int, db: Session = Depends(get_db), user: User = Depends(verified_user)
) -> None:
    db.delete(_owned_skill(db, skill_id, user))
    db.commit()


@router.post("/skills/{skill_id}/comments", status_code=201, response_model=CommentOut)
def add_comment(
    skill_id: int,
    body: CommentIn,
    db: Session = Depends(get_db),
    user: User = Depends(verified_user),
):
    _load(db, skill_id)
    comment = Comment(skill_id=skill_id, author_id=user.id, content=body.content.strip())
    db.add(comment)
    db.commit()
    comment.author = user
    return _comment_out(comment)


@router.delete("/comments/{comment_id}", status_code=204)
def delete_comment(
    comment_id: int, db: Session = Depends(get_db), user: User = Depends(verified_user)
) -> None:
    comment = db.get(Comment, comment_id)
    if comment is None:
        raise HTTPException(404, "Comment not found")
    if comment.author_id != user.id:
        raise HTTPException(403, "Not your comment")
    db.delete(comment)
    db.commit()
