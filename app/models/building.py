from app.db.base import Base
from sqlalchemy import Column, Integer, String, DateTime, text

class Building(Base):
    __tablename__ = "buildings"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    created_at = Column(DateTime(timezone = True), server_default = text("now()"), nullable = False)
