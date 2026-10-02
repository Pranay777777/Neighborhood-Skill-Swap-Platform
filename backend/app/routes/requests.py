from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import current_user, verified_user
from ..models import Skill, SwapRequest, User
from ..schemas import RequestIn, RequestOut, RequestPatch

router = APIRouter(tags=["swap requests"])


def _out(r: SwapRequest) -> RequestOut:
    return RequestOut(
        id=r.id,
        skill_id=r.skill_id,
        skill=r.skill.skill,
        requester_id=r.requester_id,
        requester=r.requester.name,
        message=r.message,
        status=r.status,
        created_at=r.created_at,
    )


def _visible(db: Session, request_id: int, user: User) -> SwapRequest:
    """A request is private to its requester and the skill's owner. Anyone else gets a 404,
    the same answer as for an id that does not exist, so ids cannot be probed."""
    r = db.get(SwapRequest, request_id)
    if r is None or user.id not in (r.requester_id, r.skill.owner_id):
        raise HTTPException(404, "Request not found")
    return r


@router.post("/skills/{skill_id}/requests", status_code=201, response_model=RequestOut)
def create_request(
    skill_id: int,
    body: RequestIn,
    db: Session = Depends(get_db),
    user: User = Depends(verified_user),
):
    skill = db.get(Skill, skill_id)
    if skill is None:
        raise HTTPException(404, "Skill not found")
    if skill.owner_id == user.id:
        raise HTTPException(400, "You cannot request your own skill")
    r = SwapRequest(skill_id=skill_id, requester_id=user.id, message=body.message.strip())
    db.add(r)
    db.commit()
    return _out(r)


@router.get("/me/requests", response_model=list[RequestOut])
def my_requests(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.scalars(
        select(SwapRequest)
        .join(Skill)
        .where(or_(SwapRequest.requester_id == user.id, Skill.owner_id == user.id))
        .order_by(SwapRequest.id.desc())
    ).all()
    return [_out(r) for r in rows]


@router.get("/requests/{request_id}", response_model=RequestOut)
def get_request(request_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return _out(_visible(db, request_id, user))


@router.patch("/requests/{request_id}", response_model=RequestOut)
def answer_request(
    request_id: int,
    body: RequestPatch,
    db: Session = Depends(get_db),
    user: User = Depends(verified_user),
):
    r = _visible(db, request_id, user)
    if r.skill.owner_id != user.id:  # the requester can see it but only the owner can answer
        raise HTTPException(403, "Only the skill owner can answer")
    r.status = body.status
    db.commit()
    return _out(r)
