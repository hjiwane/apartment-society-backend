from sqlalchemy.orm import declarative_base

Base = declarative_base()

from app.models.user import User
from app.models.building import Building
from app.models.unit import Unit
from app.models.membership import Membership
from app.models.maintenance_request import MaintenanceRequest
