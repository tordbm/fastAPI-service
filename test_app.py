import pytest
import os
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.models import users

load_dotenv()

TEST_DATABASE_URL = os.getenv('TEST_DATABASE_URL')

engine = create_engine(TEST_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_create_user(db):
    # Test: send a POST request to create a user
    with TestClient(app) as client:
        username = "testuser"
        email = "testuser@example.com"
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
