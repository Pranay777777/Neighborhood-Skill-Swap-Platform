import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from .config import DEV_SECRET, Settings, settings
from .db import Base, SessionLocal, engine
from .ratelimit import limiter, too_many
from .routes import auth, requests, skills
from .seed import seed_demo


def check_secret(cfg: Settings) -> None:
    """Never run a real database with the published dev signing key."""
    if not cfg.database_url.startswith("sqlite") and (
        cfg.jwt_secret == DEV_SECRET or len(cfg.jwt_secret) < 32
    ):
        raise RuntimeError("Set SWAP_JWT_SECRET to a random value of 32+ characters")


@asynccontextmanager
async def lifespan(_: FastAPI):
    check_secret(settings)
    Base.metadata.create_all(engine)
    if settings.seed_demo:
        with SessionLocal() as db:
            seed_demo(db)
    yield


log = logging.getLogger("api")

app = FastAPI(title="Neighborhood Skill Swap API", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, too_many)


@app.middleware("http")
async def json_500(request: Request, call_next):
    """Turn an unhandled error into a JSON 500 *inside* the CORS middleware (registered
    after this, so it wraps it). Starlette's own 500 skips CORS, so a browser saw only a
    network error and the UI could not say what went wrong."""
    try:
        return await call_next(request)
    except Exception:
        log.exception("unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse({"detail": "Something went wrong on our side"}, status_code=500)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router)
app.include_router(skills.router)
app.include_router(requests.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
