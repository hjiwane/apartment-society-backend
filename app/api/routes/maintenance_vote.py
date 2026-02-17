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

@router.post("/", status_code=status.HTTP_201_CREATED)
def vote(payload: Vote, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    req = db.query(MaintenanceRequest).filter(MaintenanceRequest.id == payload.maintenance_request_id).first()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance request does not exist")
    
    if req.unit_id is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Voting is allowed only for common-area maintenance requests")

    belongs = db.query(Membership).join(Unit, Membership.unit_id == Unit.id).filter(Membership.user_id == current_user.id, Unit.building_id == req.building_id).first()
    if not belongs:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    vote_query = db.query(MaintenanceVote).filter(MaintenanceVote.maintenance_request_id == payload.maintenance_request_id, MaintenanceVote.user_id == current_user.id)
    found_vote = vote_query.first()

    if payload.dir == 1:
        if found_vote:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"{current_user.id} has already voted on maintenance request {payload.maintenance_request_id}")
        new_vote = MaintenanceVote(maintenance_request_id=payload.maintenance_request_id, user_id=current_user.id)
        db.add(new_vote)
        db.commit()
        return {"message": "Successfully added vote"}

    else:
        if not found_vote:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vote does not exist")
        vote_query.delete(synchronize_session=False)
        db.commit()
        return {"message": "Successfully removed vote"}
    
    
