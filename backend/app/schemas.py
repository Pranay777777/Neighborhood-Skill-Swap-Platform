from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterIn(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=10, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(max_length=128)


class TokenIn(BaseModel):
    token: str = Field(min_length=10, max_length=200)


class RefreshIn(BaseModel):
    refresh_token: str = Field(min_length=10, max_length=200)


class ForgotIn(BaseModel):
    email: EmailStr


class ResetIn(BaseModel):
    token: str = Field(min_length=10, max_length=200)
    new_password: str = Field(min_length=10, max_length=128)


class TokensOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    name: str
    email_verified: bool


class SkillIn(BaseModel):
    skill: str = Field(min_length=1, max_length=120)
    type: Literal["offer", "request"]
    description: str = Field(min_length=1, max_length=2000)
    contact: str | None = Field(default=None, max_length=255)


class SkillPatch(BaseModel):
    skill: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, min_length=1, max_length=2000)
    contact: str | None = Field(default=None, max_length=255)


class CommentIn(BaseModel):
    content: str = Field(min_length=1, max_length=1000)


class CommentOut(BaseModel):
    id: int
    author_id: int
    author: str
    content: str
    created_at: datetime


class SkillOut(BaseModel):
    id: int
    owner_id: int
    name: str
    skill: str
    type: str
    description: str
    contact: str | None
    created_at: datetime
    comments: list[CommentOut]


class RequestIn(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


class RequestPatch(BaseModel):
    status: Literal["accepted", "declined"]


class RequestOut(BaseModel):
    id: int
    skill_id: int
    skill: str
    requester_id: int
    requester: str
    message: str
    status: str
    created_at: datetime
