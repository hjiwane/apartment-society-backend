from fastapi import FastAPI
from .api import health 
from .api.routes import users, buildings, units, memberships, maintenance_request, auth, maintenance_vote

app = FastAPI()

app.include_router(health.router)
app.include_router(users.router)
app.include_router(buildings.router)
app.include_router(units.router)
app.include_router(memberships.router)
app.include_router(maintenance_request.router)
app.include_router(auth.router)
app.include_router(maintenance_vote.router)


