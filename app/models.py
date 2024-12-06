from sqlalchemy import UUID, Boolean, DateTime, Table, Column, String, func
from .database import metadata

users = Table(
    "users",
    metadata,
    Column("id", UUID, primary_key=True, server_default=func.uuid_generate_v4()),
    Column("username", String(50), nullable=False, unique=True),
    Column("email", String(100), nullable=False, unique=True),
    Column("created_at", DateTime, server_default="now()"),
    Column("disabled_at", DateTime, nullable=True),
    Column("disabled", Boolean, nullable=True),
    Column("hashed_password", String, nullable=False)
)
favored_cities = Table(
    "favored_cities",
    metadata,
    Column("favored_id", UUID, primary_key=True, server_default=func.uuid_generate_v4()),
    Column("id", UUID, nullable=False),
    Column("city", String(50), nullable=False),
)
