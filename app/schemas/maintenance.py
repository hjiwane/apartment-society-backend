from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Literal


Status = Literal["open", "in_progress", "resolved"]

class MaintenanceRequestCreate(BaseModel):
    unit_id: int
    title: str
    description: str

class MaintenanceRequestOut(BaseModel):
    id: int
    unit_id: int
    created_by_user_id: int
    title: str
    description: str                            
    status: str
    vote_count: Optional[int] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

    # class Config:
    #     from_attributes = True    

class MaintenanceOut(BaseModel):
    maintenance: MaintenanceRequestOut
    votes: int

class MaintenanceRequestUpdate(BaseModel):
    status: Status