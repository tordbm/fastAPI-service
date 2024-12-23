from contextlib import asynccontextmanager
from typing import Annotated, List
from uuid import UUID

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import delete, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from . import models, schemas
from .database import database, engine, get_db
from .utils import (
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    get_password_hash,
    oauth2_scheme,
    origins,
    verify_password,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await database.connect()
    async with engine.begin() as conn:
        await conn.run_sync(models.metadata.create_all)
    yield
    await database.disconnect()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def authenticate_user(username: str, password: str, db: AsyncSession):
    user = await get_user_by_username(username, db)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], db: AsyncSession = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        token_data = schemas.TokenData(username=username)
    except jwt.InvalidTokenError:
        raise credentials_exception
    user = await get_user_by_username(username=token_data.username, db=db)
    if user is None:
        raise credentials_exception
    return user


def get_current_active_user(
    current_user: Annotated[schemas.User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# Endpoints
@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db),
) -> schemas.Token:
    user = await authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return schemas.Token(access_token=access_token, token_type="bearer")


@app.get("/users/me/", response_model=schemas.UserResponse)
async def read_users_me(
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
):
    try:
        return current_user
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.get("/users/me/cities/", response_model=List[schemas.FavoriteCities])
async def read_own_cities(
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    query = models.favored_cities.select().where(
        current_user.id == models.favored_cities.c.id
    )
    result = await db.execute(query)
    cities = result.fetchall()
    if not cities:
        raise HTTPException(404, detail="No cities found")
    return cities


@app.get("/allusers/", response_model=List[schemas.UserResponse])
async def read_users(db: AsyncSession = Depends(get_db)):
    query = select(models.users)
    result = await db.execute(query)
    users = result.fetchall()
    if not users:
        raise HTTPException(404, detail="No users found")
    return users


@app.post("/get_user_by_username/", response_model=schemas.UserResponse)
async def get_user_by_username(username: str, db: AsyncSession = Depends(get_db)):
    query = models.users.select().where(models.users.c.username == username)
    result = await db.execute(query)
    user = result.fetchone()
    if user is None:
        raise HTTPException(404, detail="User not found")
    return user


@app.post("/get_user_by_id/", response_model=schemas.UserResponse)
async def get_user_by_id(User: schemas.UserById, db: AsyncSession = Depends(get_db)):
    query = models.users.select().where(models.users.c.id == User.id)
    result = await db.execute(query)
    user = result.fetchone()
    if user is None:
        raise HTTPException(404, detail="User not found")
    return user


@app.post("/add_favorite_city/", response_model=schemas.UserFavoredCityResponse)
async def add_favorite_city(
    request: schemas.UserAddFavoriteCity,
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    try:
        query = insert(models.favored_cities).values(
            id=current_user.id, city=request.city
        )
        result = await db.execute(query)
        await db.commit()
        return {
            "favored_id": result.inserted_primary_key[0],
            "username": current_user.username,
            "city": request.city,
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(400, detail="Could not add city: " + str(e))


@app.post("/create_user/")
async def create_user(request: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        query = insert(models.users).values(
            username=request.username,
            email=request.email,
            hashed_password=get_password_hash(request.password),
        )
        result = await db.execute(query)
        await db.commit()
        return {
            "id": result.inserted_primary_key[0],
            "username": request.username,
            "email": request.email,
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(400, detail="User already exists: " + str(e))


@app.delete("/delete_favored_city/")
async def delete_favored_city(
    favored_id: UUID,
    _: Annotated[schemas.User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    try:
        query = delete(models.favored_cities).where(
            models.favored_cities.c.favored_id == favored_id
        )
        result = await db.execute(query)
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="City not found")
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/users/delete_user/")
async def delete_user(
    id: UUID,
    _: Annotated[schemas.User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    try:
        query = delete(models.users).where(models.users.c.id == id)
        result = await db.execute(query)
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
