from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..deps import current_user
from ..mailer import send_mail
from ..models import EmailToken, RefreshToken, User
from ..schemas import (
    ForgotIn,
    LoginIn,
    RefreshIn,
    RegisterIn,
    ResetIn,
    TokenIn,
    TokensOut,
    UserOut,
)
from ..security import (
    as_utc,
    create_access_token,
    hash_password,
    new_opaque_token,
    sha256,
    utcnow,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])

_DUMMY_HASH = hash_password("not-a-real-password")  # equalises timing for unknown emails


def _issue_tokens(db: Session, user: User, family: str | None = None) -> TokensOut:
    refresh = new_opaque_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            family=family or new_opaque_token(),
            token_hash=sha256(refresh),
            expires_at=utcnow() + timedelta(days=settings.refresh_ttl_days),
        )
    )
    db.commit()
    return TokensOut(access_token=create_access_token(user.id), refresh_token=refresh)


def _revoke_all(db: Session, user_id: int) -> None:
    db.execute(update(RefreshToken).where(RefreshToken.user_id == user_id).values(revoked=True))


def _email_token(db: Session, user: User, purpose: str, ttl: timedelta) -> str:
    token = new_opaque_token()
    db.add(
        EmailToken(
            user_id=user.id, purpose=purpose, token_hash=sha256(token), expires_at=utcnow() + ttl
        )
    )
    db.commit()
    return token


def send_verification(db: Session, user: User) -> None:
    token = _email_token(db, user, "verify", timedelta(hours=settings.verify_ttl_hours))
    send_mail(
        user.email,
        "Verify your Skill Swap email",
        f"Hi {user.name}, confirm your email:\n{settings.app_url}/verify-email?token={token}\n",
    )


def _consume(db: Session, raw: str, purpose: str) -> User:
    """Mark a single-use token as used and return its user, or 400 if invalid/expired/used."""
    row = db.scalar(
        select(EmailToken).where(
            EmailToken.token_hash == sha256(raw), EmailToken.purpose == purpose
        )
    )
    if row is None or row.used_at is not None or as_utc(row.expires_at) < utcnow():
        raise HTTPException(400, "Invalid or expired token")
    # Atomic claim: only one concurrent request can flip used_at from NULL.
    claimed = db.execute(
        update(EmailToken)
        .where(EmailToken.id == row.id, EmailToken.used_at.is_(None))
        .values(used_at=utcnow())
    )
    if claimed.rowcount != 1:
        raise HTTPException(400, "Invalid or expired token")
    user = db.get_one(User, row.user_id)
    return user


@router.post("/register", status_code=201, response_model=UserOut)
def register(body: RegisterIn, db: Session = Depends(get_db)) -> User:
    user = User(
        email=body.email.lower(), name=body.name.strip(), password_hash=hash_password(body.password)
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Email already registered") from None
    send_verification(db, user)
    return user


@router.post("/verify-email", response_model=UserOut)
def verify_email(body: TokenIn, db: Session = Depends(get_db)) -> User:
    user = _consume(db, body.token, "verify")
    user.email_verified = True
    db.commit()
    return user


@router.post("/resend-verification", status_code=202)
def resend_verification(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    if not user.email_verified:
        send_verification(db, user)
    return {"detail": "If your email is unverified, a new link was sent."}


@router.post("/login", response_model=TokensOut)
def login(body: LoginIn, db: Session = Depends(get_db)) -> TokensOut:
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    valid, needs_rehash = verify_password(
        body.password, user.password_hash if user else _DUMMY_HASH
    )
    if user is None or not valid:
        raise HTTPException(401, "Wrong email or password")
    if needs_rehash:
        user.password_hash = hash_password(body.password)
        db.commit()
    return _issue_tokens(db, user)


@router.post("/refresh", response_model=TokensOut)
def refresh(body: RefreshIn, db: Session = Depends(get_db)) -> TokensOut:
    row = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == sha256(body.refresh_token))
    )
    if row is None:
        raise HTTPException(401, "Invalid refresh token")
    if row.used or row.revoked:
        # A rotated token came back: someone has a copy. Kill the whole family.
        db.execute(
            update(RefreshToken).where(RefreshToken.family == row.family).values(revoked=True)
        )
        db.commit()
        raise HTTPException(401, "Refresh token reuse detected; sign in again")
    if as_utc(row.expires_at) < utcnow():
        raise HTTPException(401, "Refresh token expired")
    claimed = db.execute(
        update(RefreshToken)
        .where(RefreshToken.id == row.id, RefreshToken.used.is_(False))
        .values(used=True)
    )
    if claimed.rowcount != 1:  # lost a race with a concurrent refresh of the same token
        db.execute(
            update(RefreshToken).where(RefreshToken.family == row.family).values(revoked=True)
        )
        db.commit()
        raise HTTPException(401, "Refresh token reuse detected; sign in again")
    user = db.get_one(User, row.user_id)
    return _issue_tokens(db, user, family=row.family)


@router.post("/logout", status_code=204)
def logout(body: RefreshIn, db: Session = Depends(get_db)) -> None:
    row = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == sha256(body.refresh_token))
    )
    if row is not None:
        db.execute(
            update(RefreshToken).where(RefreshToken.family == row.family).values(revoked=True)
        )
        db.commit()


@router.post("/forgot-password", status_code=202)
def forgot_password(body: ForgotIn, db: Session = Depends(get_db)) -> dict:
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if user is not None:
        token = _email_token(db, user, "reset", timedelta(minutes=settings.reset_ttl_minutes))
        send_mail(
            user.email,
            "Reset your Skill Swap password",
            f"Reset link (valid {settings.reset_ttl_minutes} min, single use):\n"
            f"{settings.app_url}/reset-password?token={token}\n",
        )
    return {"detail": "If that email is registered, a reset link was sent."}  # same either way


@router.post("/reset-password", status_code=204)
def reset_password(body: ResetIn, db: Session = Depends(get_db)) -> None:
    user = _consume(db, body.token, "reset")
    user.password_hash = hash_password(body.new_password)
    _revoke_all(db, user.id)  # a reset signs out every device
    db.commit()


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)) -> User:
    return user
