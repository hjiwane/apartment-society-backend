from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.models.building import Building
from app.models.unit import Unit
from app.models.membership import Membership
from app.models.maintenance_request import MaintenanceRequest
from app.models.maintenance_vote import MaintenanceVote
from app.schemas.maintenance import MaintenanceRequestCreate, MaintenanceRequestOut, MaintenanceOut, MaintenanceRequestUpdate
from app.core.security import get_current_user
from typing import List

router = APIRouter(prefix="/maintenance-requests", tags=["Maintenance Requests"])

MANAGER_ROLES = {"manager", "owner"}

def _building_exists(db: Session, building_id: int) -> None:
    if not db.query(Building).filter(Building.id == building_id).first(): 
        raise HTTPException(status_code=404, detail="Building not found")


def _unit_in_building(db: Session, unit_id: int, building_id: int) -> Unit:
    unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if not unit: 
        raise HTTPException(status_code=404, detail="Unit not found")
    if unit.building_id != building_id: 
        raise HTTPException(status_code=400, detail="Unit does not belong to this building")
    return unit


def _user_belongs_to_building(db: Session, user_id: int, building_id: int) -> None:
    exists = db.query(Membership).join(Unit, Membership.unit_id == Unit.id).filter(Membership.user_id == user_id, Unit.building_id == building_id).first()
    if not exists: 
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not belong to this building")


def _user_is_manager_in_building(db: Session, user_id: int, building_id: int) -> bool:
    return db.query(Membership).join(Unit, Membership.unit_id == Unit.id).filter(Membership.user_id == user_id, Unit.building_id == building_id, func.lower(Membership.role).in_(MANAGER_ROLES)).first() is not None


def _user_is_member_of_unit(db: Session, user_id: int, unit_id: int) -> bool:
    return db.query(Membership).filter(Membership.user_id == user_id, Membership.unit_id == unit_id).first() is not None


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=MaintenanceRequestOut)
def create_request(payload: MaintenanceRequestCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    _building_exists(db, payload.building_id)
    _user_belongs_to_building(db, current_user.id, payload.building_id)

    # unit/common-area rules + authorization
    if payload.unit_id is not None:
        _unit_in_building(db, payload.unit_id, payload.building_id)
        # tenant must be member of unit OR manager/owner in building
        if not _user_is_member_of_unit(db, current_user.id, payload.unit_id):
            if not _user_is_manager_in_building(db, current_user.id, payload.building_id):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this unit/building")

    req = MaintenanceRequest(building_id=payload.building_id, unit_id=payload.unit_id, created_by_user_id=current_user.id, title=payload.title, description=payload.description, status="OPEN")
    db.add(req)
    db.commit()
    db.refresh(req)

    return req

@router.get("/", response_model=List[MaintenanceOut])
def get_requests(building_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    _building_exists(db, building_id)
    _user_belongs_to_building(db, current_user.id, building_id)

    is_manager = _user_is_manager_in_building(db, current_user.id, building_id)

    base = db.query(MaintenanceRequest, func.count(func.distinct(MaintenanceVote.user_id))).join(MaintenanceVote, MaintenanceVote.maintenance_request_id == MaintenanceRequest.id, isouter=True).group_by(MaintenanceRequest.id).filter(MaintenanceRequest.building_id == building_id)
    if is_manager:
        results = base.order_by(MaintenanceRequest.created_at.desc()).all()
    else:
        my_unit_ids_sq = db.query(Unit.id).join(Membership, Membership.unit_id == Unit.id).filter(Membership.user_id == current_user.id, Unit.building_id == building_id).subquery()

        results = base.filter((MaintenanceRequest.unit_id.is_(None)) | (MaintenanceRequest.unit_id.in_(my_unit_ids_sq))).order_by(MaintenanceRequest.created_at.desc()).all()

    return [{"maintenance": req, "votes": votes} for req, votes in results]

@router.get("/{id}", response_model=MaintenanceOut)
def get_request(id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    result = (
        db.query(MaintenanceRequest,func.count(func.distinct(MaintenanceVote.user_id)).label("vote_count")).outerjoin(MaintenanceVote, MaintenanceVote.maintenance_request_id == MaintenanceRequest.id).filter(MaintenanceRequest.id == id).group_by(MaintenanceRequest.id).first())

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"maintenance request with id={id} does not exist",)

    req, vote_count = result

    # must belong to building
    _user_belongs_to_building(db, current_user.id, req.building_id)

    # manager/owner can view all
    is_manager = _user_is_manager_in_building(db, current_user.id, req.building_id)

    # tenants: common-area OK; unit-specific only if unit member
    if not is_manager and req.unit_id is not None:
        if not _user_is_member_of_unit(db, current_user.id, req.unit_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return {"maintenance": req, "votes": vote_count}

from app.schemas.maintenance import MaintenanceRequestUpdate

@router.patch("/{id}", response_model=MaintenanceRequestOut)
def update_request(id: int, payload: MaintenanceRequestUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    req = db.query(MaintenanceRequest).filter(MaintenanceRequest.id == id).first()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"maintenance request with id={id} does not exist")

    _user_belongs_to_building(db, current_user.id, req.building_id)

    if not _user_is_manager_in_building(db, current_user.id, req.building_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager/Owner role required")

    req.status = payload.status
    db.commit()
    return req



