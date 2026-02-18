# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.session import get_db
from app.db.base import Base
from app.core.security import get_current_user
from app.models.user import User
from app.core import config


TEST_DATABASE_URL = (
    f"postgresql://{config.settings.database_username}:"
    f"{config.settings.database_password}@"
    f"{config.settings.database_hostname}:"
    f"{config.settings.database_port}/"
    f"{config.settings.database_name}_test"
)

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    d = TestingSessionLocal()
    try:
        yield d
    finally:
        d.close()


@pytest.fixture(autouse=True)
def clean_db(db):
    db.execute(text("""
        TRUNCATE TABLE
          maintenance_votes,
          maintenance_requests,
          memberships,
          units,
          buildings,
          users
        RESTART IDENTITY CASCADE;
    """))
    db.commit()
    yield


@pytest.fixture()
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def seed_users():
    db = TestingSessionLocal()
    try:
        for (uid, email) in [(1, "tenant@test.com"), (2, "manager@test.com"), (3, "owner@test.com")]:
            u = db.query(User).filter(User.id == uid).first()
            if not u:
                db.add(User(id=uid, email=email, password="fake_hash"))
        db.commit()
        yield
    finally:
        db.close()


class RoleClient:
    def __init__(self, raw_client: TestClient, user_id: int):
        self._c = raw_client
        self._user_id = user_id

    def _with_user(self):
        db = TestingSessionLocal()
        u = db.query(User).filter(User.id == self._user_id).first()
        db.close()
        app.dependency_overrides[get_current_user] = lambda: u

    def get(self, *args, **kwargs):
        self._with_user()
        return self._c.get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self._with_user()
        return self._c.post(*args, **kwargs)

    def patch(self, *args, **kwargs):
        self._with_user()
        return self._c.patch(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self._with_user()
        return self._c.delete(*args, **kwargs)


@pytest.fixture()
def as_tenant(client, seed_users):
    return RoleClient(client, 1)


@pytest.fixture()
def as_manager(client, seed_users):
    return RoleClient(client, 2)


@pytest.fixture()
def as_owner(client, seed_users):
    return RoleClient(client, 3)
