from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.maintenance_request import MaintenanceRequest
from app.models.maintenance_vote import MaintenanceVote
from app.models.membership import Membership
from app.models.unit import Unit
from app.schemas.maintenance_vote import Vote

router = APIRouter(prefix="/votes", tags=["Votes"])


from sqlalchemy import func
from fastapi import HTTPException, status

@router.post("/", status_code=status.HTTP_201_CREATED)
def vote(payload: Vote, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    req = db.query(MaintenanceRequest).filter(MaintenanceRequest.id == payload.maintenance_request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Maintenance request does not exist")

    unit = db.query(Unit).filter(Unit.id == req.unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")

    # Block COMMON for everyone (including manager)
    if unit.unit_number == "COMMON":
        raise HTTPException(status_code=403, detail="Voting not allowed for COMMON unit")

    building_id = unit.building_id

    # User must belong to this building (any membership in any unit in this building)
    building_membership = (
        db.query(Membership)
        .join(Unit, Unit.id == Membership.unit_id)
        .filter(Membership.user_id == current_user.id, Unit.building_id == building_id)
        .order_by(Membership.id.asc())
        .first()
    )
    if not building_membership:
        raise HTTPException(status_code=403, detail="Access denied")

    role = (building_membership.role or "").lower()

    # Explicitly block owners from voting
    if role == "owner":
        raise HTTPException(status_code=403, detail="Owners cannot vote")

    # Tenants must be members of the specific unit to vote
    if role != "manager":
        unit_membership = (
            db.query(Membership)
            .filter(Membership.user_id == current_user.id, Membership.unit_id == req.unit_id)
            .first()
        )
        if not unit_membership:
            raise HTTPException(status_code=403, detail="Access denied")

    vote_query = db.query(MaintenanceVote).filter(
        MaintenanceVote.maintenance_request_id == payload.maintenance_request_id,
        MaintenanceVote.user_id == current_user.id
    )
    found_vote = vote_query.first()

    if payload.dir == 1:
        if found_vote:
            raise HTTPException(status_code=409, detail="Already voted")
        db.add(MaintenanceVote(
            maintenance_request_id=payload.maintenance_request_id,
            user_id=current_user.id
        ))
        db.commit()
        return {"message": "Successfully added vote"}

    # payload.dir == 0
    if not found_vote:
        raise HTTPException(status_code=404, detail="Vote does not exist")
    vote_query.delete(synchronize_session=False)
    db.commit()
    return {"message": "Successfully removed vote"}


    
