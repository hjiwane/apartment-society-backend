from pydantic import BaseModel
from datetime import datetime

class UnitCreate(BaseModel):
    building_id: int
    unit_number: str  # "3B"

class UnitOut(BaseModel):
    id: int
    building_id: int
    unit_number: str
    created_at: datetime

    class Config:
        from_attributes = True
