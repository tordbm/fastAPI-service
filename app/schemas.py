from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    created_at: datetime
    disabled_at: datetime = None
    disabled: bool
    model_config = {
        'from_attributes': True
    }

class UserFavoredCityResponse(BaseModel):
    favored_id: UUID
    id: UUID
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

class UserAddFavoriteCity(BaseModel):
    id: UUID
    city: str

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None
