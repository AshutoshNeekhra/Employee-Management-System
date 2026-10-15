from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401
from app.database import Base, get_db
from app.main import app
from app.schemas import EmployeeCreate


@pytest.fixture()
def session_factory():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, autoflush=False)
    Base.metadata.drop_all(engine)


@pytest.fixture()
def db(session_factory):
    session = session_factory()
    yield session
    session.close()


@pytest.fixture()
def make_create():
    counter = {"n": 0}

    def factory(**overrides) -> EmployeeCreate:
        counter["n"] += 1
        data = dict(
            full_name=f"Test User {counter['n']}",
            email=f"user{counter['n']}@example.com",
            phone="+91 98765 43210",
            department="Engineering",
            designation="Engineer",
            date_of_joining=date(2023, 1, 15),
            salary=500000,
            status="Active",
        )
        data.update(overrides)
        return EmployeeCreate(**data)

    return factory


@pytest.fixture()
def client(session_factory):
    def override():
        s = session_factory()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = override
    yield TestClient(app)
    app.dependency_overrides.clear()
