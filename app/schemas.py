from uuid import UUID
from pydantic import BaseModel

class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
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
    created_at: str = None
    deleted_at: str = None
    deleted: bool = None

class UserCreate(BaseModel):
    username: str
    email: str

class UserAddFavoriteCity(BaseModel):
    id: UUID
    city: str
