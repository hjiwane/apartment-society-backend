from pydantic import BaseModel
from typing import Literal

class Vote(BaseModel):
    maintenance_request_id: int
    dir: Literal[0,1]