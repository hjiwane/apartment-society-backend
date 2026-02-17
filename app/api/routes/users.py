from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.membership import Membership
from app.models.unit import Unit
from app.schemas.user import UserCreate, UserOut
from app.db.session import get_db
from app.core import security
from sqlalchemy import func
from app.core.security import get_current_user


router = APIRouter(prefix = "/users", tags = ["Users"])

@router.post("/", status_code = status.HTTP_201_CREATED, response_model = UserOut)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code = status.HTTP_409_CONFLICT, detail = f'{user.email} already exists')
    hashed_password = security.hash(user.password)
    user.password = hashed_password
    new_user = User(**user.model_dump())
    db.add(new_user)
    db.commit()
    return new_user

@router.get("/{id}")
def get_user(id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    user = db.query(User).filter(User.id == id).first()
    if not user: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"user with id={id} does not exist")

    authorized = db.query(Membership).join(Unit, Membership.unit_id == Unit.id).filter(Membership.user_id == current_user.id, func.lower(Membership.role).in_(["manager","owner"])).first()
    if not authorized: raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager or owner role required")

    memberships = db.query(Membership).filter(Membership.user_id == user.id).all()
    return {"id": user.id, "email": user.email, "unit_ids": [m.unit_id for m in memberships]}
    