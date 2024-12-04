import databases
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .utils import DATABASE_URL

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_size=20,
    max_overflow=10,
)
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
