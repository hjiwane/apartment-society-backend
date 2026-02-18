from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session

from app.models.membership import Membership
from app.models.user import User
from app.models.unit import Unit
from app.core.security import get_current_user
from app.schemas.membership import MembershipCreate, MembershipOut, MembershipUpdate
from app.db.session import get_db
from sqlalchemy import func

router = APIRouter(prefix = "/memberships", tags = ["Memberships"])

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=MembershipOut)
def create_membership(membership: MembershipCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    user = db.query(User).filter(User.id == membership.user_id).first()
    if not user: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    unit = db.query(Unit).filter(Unit.id == membership.unit_id).first()
    if not unit: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")

    owner = db.query(Membership).join(Unit, Membership.unit_id == Unit.id).filter(Membership.user_id == current_user.id, Unit.building_id == unit.building_id, func.lower(Membership.role) == "owner").first()
    if not owner: 
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner role required")

    existing = db.query(Membership).filter(Membership.user_id == membership.user_id, Membership.unit_id == membership.unit_id).first()
    if existing: 
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Membership already exists")
    
    if unit.unit_number == "COMMON": 
        raise HTTPException(400, "Cannot assign membership to COMMON unit")

    new_membership = Membership(**membership.model_dump())
    db.add(new_membership)
    db.commit()
    return new_membership


@router.get("/", response_model=list[MembershipOut])
def get_my_membership_in_building(building_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    memberships = db.query(Membership).join(Unit, Membership.unit_id == Unit.id).filter(Membership.user_id == current_user.id, Unit.building_id == building_id).all()
    if not memberships: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No membership found for this building")
    return memberships

@router.patch("/{id}", response_model=MembershipOut)
def update_membership_by_owner(id: int, membership: MembershipUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    target = db.query(Membership).filter(Membership.id == id).first()
    if not target: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"membership with id={id} does not exist")

    unit = db.query(Unit).filter(Unit.id == target.unit_id).first()
    if not unit: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")

    owner = db.query(Membership).join(Unit, Membership.unit_id == Unit.id).filter(Membership.user_id == current_user.id, Unit.building_id == unit.building_id, func.lower(Membership.role) == "owner").first()
    if not owner: 
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner role required")

    target.role = membership.role
    db.commit()
    db.refresh(target)
    return target

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_membership_by_owner(id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    target = db.query(Membership).filter(Membership.id == id).first()
    if not target: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"membership with id={id} does not exist")

    unit = db.query(Unit).filter(Unit.id == target.unit_id).first()
    if not unit: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")

    owner = db.query(Membership).join(Unit, Membership.unit_id == Unit.id).filter(Membership.user_id == current_user.id, Unit.building_id == unit.building_id, func.lower(Membership.role) == "owner").first()
    if not owner: 
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner role required")
    
    if (target.role).lower() == "owner":
        owners = db.query(Membership).join(Unit, Membership.unit_id == Unit.id).filter(Unit.building_id == unit.building_id, func.lower(Membership.role) == "owner").count()
        if owners <= 1: 
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot remove the only owner from this building")

    db.delete(target)
    db.commit()
    return




