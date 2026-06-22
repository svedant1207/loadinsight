from pydantic import BaseModel, EmailStr
from datetime import datetime

# what the user sends when registering
class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str

# what we send back in responses (never expose password)
class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    is_active: bool
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}