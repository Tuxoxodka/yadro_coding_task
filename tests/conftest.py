import os
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.main import app
from app.database import Base, get_db

# Используем переменную окружения для подключения к тестовой базе
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://graphuser:graphpass@db:5432/graphdb_test")

# Создаём движок SQLAlchemy
engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Переопределяем зависимость
@pytest.fixture()
def db_session() -> Session:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


async def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Подменяем зависимость FastAPI
#app.dependency_overrides[get_db] = db_session


# Создаём схему в тестовой БД
@pytest.fixture(scope="session", autouse=True)
def create_test_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


@pytest.fixture()
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
async def async_client():
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
