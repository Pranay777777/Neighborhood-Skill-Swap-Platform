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


def test_dev_secret_allowed_for_local_sqlite():
    check_secret(Settings(database_url="sqlite:///./swap.db", jwt_secret=DEV_SECRET))
