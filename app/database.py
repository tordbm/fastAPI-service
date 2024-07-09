import os
from dotenv import load_dotenv
import databases
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
)
Base = declarative_base()

database = databases.Database(DATABASE_URL)

metadata = Base.metadata

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session