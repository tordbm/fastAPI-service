from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from . import models, schemas
from .database import engine, get_db, database
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    async with engine.begin() as conn:
        await conn.run_sync(models.metadata.create_all)
    yield
    await database.disconnect()

app = FastAPI(lifespan=lifespan)

@app.get("/allusers/")
async def read_users():
    query = models.users.select()
    return await database.fetch_all(query)

@app.post("/get_user_by_id/")
async def get_user_by_id(UserId: schemas.UserId):
    query = models.users.select().where(models.users.c.id == UserId.id)
    return await database.fetch_all(query)

@app.post("/create_user/", response_model=schemas.UserResponse)
async def create_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    query = models.users.insert().values({"username": user.username, "email": user.email})
    result = await db.execute(query)
    await db.commit()
    return {"id": result.inserted_primary_key[0], "username": user.username, "email": user.email}
