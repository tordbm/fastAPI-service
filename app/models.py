from sqlalchemy import UUID, Boolean, Table, Column, String, TIMESTAMP, func
from .database import metadata

users = Table(
    "users",
    metadata,
    Column("id", UUID, primary_key=True, server_default=func.uuid_generate_v4()),
    Column("username", String(50), nullable=False),
    Column("email", String(100), nullable=False),
    Column("created_at", TIMESTAMP, server_default="now()"),
    Column("deleted_at", TIMESTAMP),
    Column("deleted", Boolean, nullable=False)
)