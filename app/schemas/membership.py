from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Literal

Role = Literal["tenant", "manager", "owner"]

class MembershipCreate(BaseModel):
    user_id: int
    unit_id: int
    role: Role

class MembershipOut(BaseModel):
    id: int
    user_id: int
    unit_id: int
    role: Role
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

    # class Config:
    #     from_attributes = True

class MembershipUpdate(BaseModel):
    role: Role        
