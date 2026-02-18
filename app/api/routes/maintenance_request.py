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

@router.post("/", status_code=201, response_model=MaintenanceRequestOut)
def create_request(payload: MaintenanceRequestCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    unit = db.query(Unit).filter(Unit.id == payload.unit_id).first()
    if not unit:
        raise HTTPException(404, "Unit not found")

    # block COMMON so owners (who only have COMMON) can't create
    if unit.unit_number == "COMMON":
        raise HTTPException(403, "Owners cannot create maintenance requests")

    # must be member of that unit (tenant/manager/etc)
    is_member = db.query(Membership).filter(Membership.user_id == current_user.id, Membership.unit_id == payload.unit_id).first()
    if not is_member:
        raise HTTPException(403, "Not authorized for this unit")

    req = MaintenanceRequest(unit_id=payload.unit_id, created_by_user_id=current_user.id, title=payload.title, description=payload.description,status="open")
    db.add(req)
    db.commit()

    return req

@router.get("/", response_model=List[MaintenanceOut])
def get_requests(building_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    building = db.query(Building).filter(Building.id == building_id).first()
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")

    # user must belong to this building (any membership in any unit in building)
    belongs = (
        db.query(Membership.id)
        .join(Unit, Unit.id == Membership.unit_id)
        .filter(Membership.user_id == current_user.id, Unit.building_id == building_id)
        .first()
    )
    if not belongs:
        raise HTTPException(status_code=403, detail="Access denied")

    results = (
        db.query(
            MaintenanceRequest,
            func.count(func.distinct(MaintenanceVote.user_id)).label("votes")
        )
        .join(Unit, Unit.id == MaintenanceRequest.unit_id)
        .outerjoin(MaintenanceVote, MaintenanceVote.maintenance_request_id == MaintenanceRequest.id)
        .filter(Unit.building_id == building_id)
        .group_by(MaintenanceRequest.id)
        .order_by(MaintenanceRequest.created_at.desc())
        .all()
    )

    return [{"maintenance": req, "votes": votes} for req, votes in results]



@router.get("/{id}", response_model=MaintenanceOut)
def get_request(
    id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = (
        db.query(
            MaintenanceRequest,
            func.count(func.distinct(MaintenanceVote.user_id)).label("votes"),
        )
        .outerjoin(
            MaintenanceVote,
            MaintenanceVote.maintenance_request_id == MaintenanceRequest.id,
        )
        .filter(MaintenanceRequest.id == id)
        .group_by(MaintenanceRequest.id)
        .first()
    )

    if not result:
        raise HTTPException(status_code=404, detail="Maintenance request not found")

    req, votes = result

    unit = db.query(Unit).filter(Unit.id == req.unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")

    # user must belong to building (any membership in any unit in that building)
    belongs = (
        db.query(Membership.id)
        .join(Unit, Membership.unit_id == Unit.id)
        .filter(
            Membership.user_id == current_user.id,
            Unit.building_id == unit.building_id,
        )
        .first()
    )
    if not belongs:
        raise HTTPException(status_code=403, detail="Access denied")

    return {"maintenance": req, "votes": votes}

@router.patch("/{id}", response_model=MaintenanceRequestOut)
def update_request(id: int, payload: MaintenanceRequestUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    req = db.query(MaintenanceRequest).filter(MaintenanceRequest.id == id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Maintenance request not found")

    unit = db.query(Unit).filter(Unit.id == req.unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")

    # manager/owner in the SAME building can update any request in that building
    is_manager = (db.query(Membership.id).join(Unit, Unit.id == Membership.unit_id).filter(Membership.user_id == current_user.id,Unit.building_id == unit.building_id,func.lower(Membership.role).in_(("manager", "owner"))).first() is not None)

    if not is_manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager/Owner role required")

    # normalize to DB style (OPEN / IN_PROGRESS / RESOLVED)
    req.status = payload.status.lower()
    db.commit()
    return req




