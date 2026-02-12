from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, text
from app.db.base import Base

class Unit(Base):
    __tablename__ = "units"
    id = Column(Integer, primary_key=True, index=True)
    unit_number = Column(String, nullable=False)
    floor = Column(Integer, nullable=True)
    building_id = Column(Integer, ForeignKey("buildings.id", ondelete = "CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone = True), server_default = text("now()"), nullable = False)