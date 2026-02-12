from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, text
from app.db.base import Base

class MaintenanceRequest(Base):
    __tablename__ = "maintenance_requests"

    id = Column(Integer, primary_key=True, index=True)
    unit_id = Column(Integer, ForeignKey("units.id", ondelete="CASCADE"), nullable=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assigned_to_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    priority = Column(String, nullable=False, server_default=text("'MEDIUM'"))  # LOW/MEDIUM/HIGH
    status = Column(String, nullable=False, server_default=text("'OPEN'"))      # OPEN/IN_PROGRESS/RESOLVED/CLOSED
    created_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
