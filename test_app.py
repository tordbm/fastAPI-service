import pytest
import os
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import UUID, create_engine, select
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.models import users, favored_cities
from random import randint

load_dotenv()

TEST_DATABASE_URL = os.getenv('TEST_DATABASE_URL')

engine = create_engine(TEST_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_create_user(db):
    client = TestClient(app)
    username = f"testuser{randint(0, 1000)}"
    email = f"testuser{randint(0, 1000)}@example.com"
    response = client.post("/create_user/", json={"username": username, "email": email})

    assert response.status_code == 200
    
    assert response.json()["username"] == username
    assert response.json()["email"] == email

    query = select(users).where(users.c.username == username)
    result = db.execute(query).fetchone()
    
    assert result is not None
    print("Result from database query:", result)
    assert result.username == username
    assert result.email == email
    db.rollback()

def test_add_favored_city(db):
    client = TestClient(app)
    user_id = "d9739ef3-2d87-45ad-be6d-a1d3c7d123c3"
    city = "Bergen"
    response = client.post("/add_favorite_city/", json={"id": user_id, "city": city})

    assert response.status_code == 200
    
    assert response.json()["id"] == user_id
    assert response.json()["city"] == city
    
    query = select(favored_cities).where(
    (favored_cities.c.id == user_id) & (favored_cities.c.city == city)
    )
    result = db.execute(query).fetchone()
    
    assert result is not None
    print("Result from database query:", result)
    assert result.id == user_id
    assert result.city == city
    db.rollback()