from uuid import UUID
from pydantic import BaseModel

class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    model_config = {
        'from_attributes': True
    }

class UserCreate(BaseModel):
    username: str
    email: str

class UserId(BaseModel):
    id: str
