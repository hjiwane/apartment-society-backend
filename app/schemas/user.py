from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str  

class UserOut(BaseModel):
    id:int
    email: EmailStr
    created_at: datetime   
    model_config = ConfigDict(from_attributes=True) 

    # class Config:
    #     from_attributes = True