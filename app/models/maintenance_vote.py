from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, text
from app.db.base import Base

class MaintenanceVote(Base):
    __tablename__ = "maintenance_votes"
    maintenance_request_id = Column(Integer, ForeignKey("maintenance_requests.id", ondelete="CASCADE"), primary_key = True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key = True)