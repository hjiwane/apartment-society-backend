from app.db.base import Base
from sqlalchemy import Column, Integer, String, DateTime, text

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key = True, nullable = False, index = True)
    email = Column(String, nullable = False, unique = True)
    password = Column(String, nullable = False)
    created_at = Column(DateTime(timezone=True), server_default = text('now()'), nullable = False)

