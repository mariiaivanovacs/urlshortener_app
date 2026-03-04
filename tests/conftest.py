import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env.test as fallback defaults.
# override=False means env vars already in the environment (e.g. set by docker-compose) win.
# Locally: .env.test provides DATABASE_URL / BASE_DOMAIN.
# In Docker: docker-compose DATABASE_URL pointing to host "db" takes precedence.
load_dotenv(Path(__file__).parent.parent / ".env.test", override=False)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

import app.models.link  # noqa: F401 — registers Link with Base.metadata before create_all


@pytest.fixture
def db():
    from app.core.database import Base

    engine = create_engine(settings.database_url)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autoflush=False, autocommit=False, bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def client(db):
    from app.core.database import get_db
    from app.main import app

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()
