from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    created_at: datetime
    disabled_at: Optional[datetime]
    disabled: bool
    model_config = {
        'from_attributes': True
    }

class UserFavoredCityResponse(BaseModel):
    favored_id: UUID
    username: str
    city: str
    model_config = {
        'from_attributes': True
    }


class User(BaseModel):
    id: UUID
    username: str = None
    email: str = None
    created_at: datetime = None
    disabled_at: datetime = None
    disabled: bool = None

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserAddFavoriteCity(BaseModel):
    city: str

class FavoriteCities(BaseModel):
    city: str
class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None
