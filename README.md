# Neighborhood Skill Swap

Neighbours post skills they can teach or want to learn, comment, and send private swap
requests. React frontend (`project/`) and FastAPI backend (`backend/`).

## Run the backend

```bash
cd backend
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt   # .venv/bin/python on Linux/macOS
.venv/Scripts/python.exe -m pytest -q
docker compose up -d mailpit        # from the repo root; inbox at http://localhost:8025
.venv/Scripts/python.exe -m uvicorn app.main:app --reload
```

## Security

### Authentication

| Mechanism | Details |
|---|---|
| Access token | JWT (HS256), 15 min, `type=access` claim checked; `alg=none` and foreign keys rejected |
| Refresh token | Opaque random token; only its SHA-256 is stored. Rotated on every use |
| Reuse detection | Presenting an already-rotated refresh token revokes its whole token family (the thief and the victim are both signed out); other devices are unaffected |
| Passwords | Argon2id. Legacy PBKDF2 hashes and Argon2 hashes with weaker parameters are re-hashed on the next successful login |
| Email verification | Single-use, 24 h, hashed token; unverified users can sign in but not post |
| Password reset | Single-use, 30 min, hashed token; the response is identical for unknown emails; a reset revokes every session |
| Startup guard | The API refuses to start against a real database with the dev signing key or a key under 32 characters |

### Authorization (route → rule)

Every route that reads or changes an owned object is enforced server-side.
[`backend/tests/test_authz.py`](backend/tests/test_authz.py) runs each one as another user
(must get 403/404 and change nothing), anonymously (401) and as the rightful user (success),
and fails if a new route is added without being classified here.

| Route | Rule | Other user gets |
|---|---|---|
| `PATCH /skills/{id}` | skill owner only | 403 |
| `DELETE /skills/{id}` | skill owner only | 403 |
| `DELETE /comments/{id}` | comment author only | 403 |
| `GET /requests/{id}` | requester or skill owner | 404 (same as a missing id, so ids can't be probed) |
| `PATCH /requests/{id}` | skill owner only (the requester gets 403) | 404 |
| `GET /me/requests` | scoped to the caller in the query | only their own |
| `GET /auth/me` | the caller, from the token | — |
| `GET /skills`, `GET /skills/{id}` | public; contact details only for signed-in users | — |
| `POST /skills/{id}/comments` | any verified user | — |
| `POST /skills/{id}/requests` | any verified user except the skill's owner | — |

### Known limitations

- Refresh tokens are returned in the JSON body, not an `HttpOnly` cookie.
- No rate limiting on login or reset yet.
