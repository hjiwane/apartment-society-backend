from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, text
from app.db.base import Base

class Membership(Base):
    __tablename__ = "memberships"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable = False)
    unit_id = Column(Integer, ForeignKey("units.id", ondelete="CASCADE"), nullable = False)
    role = Column(String, nullable = False)  # OWNER / TENANT / MANAGER
    created_at = Column(DateTime(timezone = True), server_default = text("now()"), nullable = False)
