from pydantic import BaseModel
from datetime import datetime

class BuildingCreate(BaseModel):
    name: str
    address: str 

class BuildingOut(BaseModel):
    id: int
    name: str
    address: str 
    created_at: datetime

    class Config:
        from_attributes = True
