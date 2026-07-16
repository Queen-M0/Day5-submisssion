import os
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_contextguard.db"

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings

get_settings.cache_clear()

from app.core.database import Base, SessionLocal, engine
from app.main import app
from app.seed.seed_demo import seed


@pytest.fixture(scope="session", autouse=True)
def database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed()
    yield
    Base.metadata.drop_all(bind=engine)
    Path("test_contextguard.db").unlink(missing_ok=True)


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client

