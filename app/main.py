from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from . import models, schemas
from passlib.context import CryptContext
from .database import engine, get_db, database
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
import json

load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES'))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@asynccontextmanager
async def lifespan(_: FastAPI):
    await database.connect()
    async with engine.begin() as conn:
        await conn.run_sync(models.metadata.create_all)
    yield
    await database.disconnect()

app = FastAPI(lifespan=lifespan)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


async def authenticate_user(username: str, password: str):
    user = await get_user_by_username(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except jwt.InvalidTokenError:
        raise credentials_exception
    user = await get_user_by_username(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[schemas.User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> schemas.Token:
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return schemas.Token(access_token=access_token, token_type="bearer")


@app.get("/users/me/", response_model=schemas.UserResponse)
async def read_users_me(
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
):
    return current_user


@app.get("/users/me/items/")
async def read_own_items(
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
):
    return [{"item_id": "Foo", "owner": current_user.username}]

@app.get("/allusers/", response_model=[schemas.UserResponse])
async def read_users():
    try:
        query = models.users.select()
        return await database.fetch_all(query)
    except:
        raise HTTPException(500)

@app.post("/get_user_by_username", response_model=schemas.UserResponse)
async def get_user_by_username(username: str):
    try:
        query = models.users.select().where(models.users.c.username == username)
        return await database.fetch_one(query)
    except:
        raise HTTPException(404, "User not found")

@app.post("/get_user_by_id/")
async def get_user_by_id(User: schemas.User):
    try:
        query = models.users.select().where(models.users.c.id == User.id)
        return await database.fetch_all(query)
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/add_favorite_city/", response_model=schemas.UserFavoredCityResponse)
async def add_favorite_city(request: schemas.UserAddFavoriteCity, db: AsyncSession = Depends(get_db)):
    try:
        query = models.favored_cities.insert().values(id=request.id, city=request.city)
        result = await db.execute(query)
        await db.commit()
        return {"favored_id": result.inserted_primary_key[0], "id": request.id, "city": request.city}
    except Exception as e:
        await db.rollback()
        raise HTTPException(400, "Could not add city: " + str(e))

@app.post("/create_user/", response_model=schemas.UserResponse)
async def create_user(request: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        query = models.users.insert().values(username=request.username, email=request.email)
        result = await db.execute(query)
        await db.commit()
        return {"id": result.inserted_primary_key[0], "username": request.username, "email": request.email}
    except Exception as e:
        await db.rollback()
        raise HTTPException(400, "User already exists: " + str(e))
   
