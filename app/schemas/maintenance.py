from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Literal


Status = Literal["open", "in_progress", "resolved"]

class MaintenanceRequestCreate(BaseModel):
    building_id: int
    unit_id: Optional[int] = None
    title: str
    description: Optional[str] = None 

class MaintenanceRequestOut(BaseModel):
    id: int
    building_id: int
    unit_id: Optional[int]
    created_by_user_id: int
    title: str
    description: Optional[str]                             
    status: str
    vote_count: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True    

class MaintenanceOut(BaseModel):
    maintenance: MaintenanceRequestOut
    votes: int

class MaintenanceRequestUpdate(BaseModel):
    status: Status