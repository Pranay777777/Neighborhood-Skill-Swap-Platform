import pytest

from app.config import DEV_SECRET, Settings
from app.main import check_secret

PG = "postgresql+psycopg://u:p@db/swap"


@pytest.mark.parametrize("secret", [DEV_SECRET, "too-short"])
def test_weak_secret_refused_with_a_real_database(secret):
    with pytest.raises(RuntimeError):
        check_secret(Settings(database_url=PG, jwt_secret=secret))


def test_strong_secret_accepted():
    check_secret(Settings(database_url=PG, jwt_secret="x" * 48))


@pytest.mark.parametrize(
    "given",
    ["postgres://u:p@host/db?sslmode=require", "postgresql://u:p@host/db?sslmode=require"],
)
def test_hosted_postgres_urls_use_psycopg3(given):
    url = Settings(database_url=given).database_url
    assert url == "postgresql+psycopg://u:p@host/db?sslmode=require"


def test_explicit_driver_and_sqlite_urls_untouched():
    for url in (PG, "sqlite:///./swap.db"):
        assert Settings(database_url=url).database_url == url


def test_dev_secret_allowed_for_local_sqlite():
    check_secret(Settings(database_url="sqlite:///./swap.db", jwt_secret=DEV_SECRET))
