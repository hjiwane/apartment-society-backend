from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from ..core import config

SQLALCHEMY_DATABASE_URL = f'postgresql://{config.settings.database_username}:{config.settings.database_password}@{config.settings.database_hostname}:{config.settings.database_port}/{config.settings.database_name}'
engine = create_engine(SQLALCHEMY_DATABASE_URL)
 
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()   



