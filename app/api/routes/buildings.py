from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.building import Building
from app.models.unit import Unit
from app.models.membership import Membership
from app.schemas.building import BuildingCreate, BuildingOut
from app.models.user import User
from app.schemas.user import UserOut
from typing import List
from app.db.session import get_db
from app.core.security import get_current_user

router = APIRouter(prefix = "/buildings", tags = ["Buildings"])

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=BuildingOut)
def create_building(building: BuildingCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    existing = db.query(Building).filter(Building.name == building.name, Building.address == building.address).first()
    if existing: raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Building already exists")

    new_building = Building(**building.model_dump())
    db.add(new_building)
    db.commit()
    db.refresh(new_building)

    # create a default/common unit so we can attach an OWNER membership
    default_unit = Unit(building_id=new_building.id, unit_number="COMMON") 
    db.add(default_unit) 
    db.commit()
    db.refresh(default_unit)

    owner_membership = Membership(user_id=current_user.id, unit_id=default_unit.id, role="owner")
    db.add(owner_membership) 
    db.commit()
    db.refresh(owner_membership)

    return new_building


@router.get("/{id}", response_model=BuildingOut)
def get_building(id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    building = db.query(Building).join(Unit, Unit.building_id == Building.id).join(Membership, Membership.unit_id == Unit.id).filter(Building.id == id, Membership.user_id == current_user.id).first()
    if not building: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"building with id={id} does not exist or access denied")
    return building

@router.get("/", response_model=List[BuildingOut])
def get_buildings(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    buildings = db.query(Building).join(Unit, Unit.building_id == Building.id).join(Membership, Membership.unit_id == Unit.id).filter(Membership.user_id == current_user.id).distinct(Building.id).order_by(Building.id.asc()).all()
    return buildings

@router.get("/{building_id}/users", response_model=List[UserOut])
def list_building_users(
    building_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # 1) must belong to building (any membership in any unit in building)
    belongs = (
        db.query(Membership.id)
        .join(Unit, Unit.id == Membership.unit_id)
        .filter(
            Membership.user_id == current_user.id,
            Unit.building_id == building_id,
        )
        .first()
    )
    if not belongs:
        raise HTTPException(status_code=403, detail="Access denied")

    # 2) must be manager/owner in this building
    is_admin = (
        db.query(Membership.id)
        .join(Unit, Unit.id == Membership.unit_id)
        .filter(
            Membership.user_id == current_user.id,
            Unit.building_id == building_id,
            func.lower(Membership.role).in_(("manager", "owner")),
        )
        .first()
        is not None
    )
    if not is_admin:
        raise HTTPException(status_code=403, detail="Manager/Owner role required")

    # 3) list users in this building (unique)
    users = (
        db.query(User)
        .join(Membership, Membership.user_id == User.id)
        .join(Unit, Unit.id == Membership.unit_id)
        .filter(Unit.building_id == building_id)
        .distinct(User.id)
        .order_by(User.id.asc())
        .all()
    )

    return users