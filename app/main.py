from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from . import models, schemas
from .database import engine, get_db, database
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(_: FastAPI):
    await database.connect()
    async with engine.begin() as conn:
        await conn.run_sync(models.metadata.create_all)
    yield
    await database.disconnect()

app = FastAPI(lifespan=lifespan)

@app.get("/allusers/")
async def read_users():
    try:
        query = models.users.select()
        return await database.fetch_all(query)
    except:
        raise HTTPException(500)
@app.post("/get_user_by_id/")
async def get_user_by_id(User: schemas.User):
    try:
        query = models.users.select().where(models.users.c.id == User.id)
        return await database.fetch_all(query)
    except:
        raise HTTPException(500)

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
   
