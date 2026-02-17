from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session

from app.models.unit import Unit
from app.models.building import Building
from app.models.membership import Membership
from app.schemas.unit import UnitCreate, UnitOut
from app.db.session import get_db
from app.core.security import get_current_user
from sqlalchemy import func

router = APIRouter(prefix = "/units", tags = ["Units"])

@router.post("/", status_code = status.HTTP_201_CREATED, response_model = UnitOut)
def create_unit(unit: UnitCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    building = db.query(Building).filter(Building.id == unit.building_id).first()
    if not building:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = "Building not found")
    
    owner = db.query(Membership).join(Unit, Membership.unit_id == Unit.id).filter(Membership.user_id == current_user.id, Unit.building_id == unit.building_id, func.lower(Membership.role) == "owner").first()
    if not owner: 
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner role required")
    
    existing = db.query(Unit).filter(Unit.building_id == unit.building_id, Unit.unit_number == unit.unit_number).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail = "Unit already exists in this building")

    new_unit = Unit(**unit.model_dump())
    db.add(new_unit)
    db.commit()
    return new_unit


@router.get("/", response_model=list[UnitOut])
def get_units_by_building(building_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    building = db.query(Building).filter(Building.id == building_id).first()
    if not building:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building does not exist")

    belongs = db.query(Membership.id).join(Unit, Unit.id == Membership.unit_id).filter(Membership.user_id == current_user.id, Unit.building_id == building_id).first()
    
    if not belongs:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Access denied")

    units = db.query(Unit).filter(Unit.building_id == building_id, Unit.unit_number != "COMMON").order_by(Unit.unit_number.asc()).all()

    return units
