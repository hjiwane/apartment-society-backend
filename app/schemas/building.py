from pydantic import BaseModel, ConfigDict
from datetime import datetime

class BuildingCreate(BaseModel):
    name: str
    address: str 

class BuildingOut(BaseModel):
    id: int
    name: str
    address: str 
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
    # class Config:
    #     from_attributes = True    