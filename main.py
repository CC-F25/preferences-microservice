from __future__ import annotations

import os
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4
from models.health import Health

from fastapi import FastAPI, HTTPException, Path, status, Depends
from sqlalchemy.orm import Session

from models.preferences import PreferenceCreate, PreferenceRead, PreferenceUpdate
from database import Base, engine, get_db
from models.preferences_sql import PreferencesDB

# -----------------------------------------------------------------------------
# Databse setup
# -----------------------------------------------------------------------------

port = int(os.environ.get("FASTAPIPORT", 8080))

# This creates the table automatically if it doesn't exist
Base.metadata.create_all(bind=engine)

# -----------------------------------------------------------------------------
# FastAPI app
# -----------------------------------------------------------------------------

app = FastAPI(
    title="Preferences Service API",
    description="API for managing user housing preferences (budget, rooms, size, and neighborhood)",
    version="1.0.0",
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5000",                     # Firebase local emulator
        "https://cloud-computing-ui.web.app",        # deployed Firebase site
        "https://cloud-computing-ui.firebaseapp.com" # alt Firebase domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# FastAPI Endpoints
# -----------------------------------------------------------------------------

## GET / - Get all preferences (admin/debug)
@app.get("/", response_model=List[PreferenceRead])
def get_all_preferences(db: Session = Depends(get_db)):
    """List of all user preferences."""
    prefs = db.query(PreferencesDB).all()
    # Ignore location_area and just return None for it
    return [
        PreferenceRead(
            id=p.id,
            user_id=p.user_id,
            max_budget=p.max_budget,
            min_size=p.min_size,
            location_area=None,
            rooms=p.rooms,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        for p in prefs
    ]

## POST / - Create or update a user's preferences
@app.post("/", response_model=PreferenceRead, status_code=status.HTTP_200_OK)
def create_or_update_preferences(payload: PreferenceCreate, db: Session = Depends(get_db)):
    """
    If preferences already exist for the user, they are updated. 
    Otherwise, a new record is created.
    """
    user_id_str = str(payload.user_id)

    existing = (
        db.query(PreferencesDB)
        .filter(PreferencesDB.user_id == user_id_str)
        .first()
    )

    now = datetime.utcnow()

    if existing:
        existing.max_budget = payload.max_budget
        existing.min_size = payload.min_size
        # ignore location_area: set to None or leave as-is; here we just ignore it
        existing.rooms = payload.rooms
        existing.updated_at = now

        db.commit()
        db.refresh(existing)

        return PreferenceRead(
            id=existing.id,
            user_id=existing.user_id,
            max_budget=existing.max_budget,
            min_size=existing.min_size,
            location_area=None,
            rooms=existing.rooms,
            created_at=existing.created_at,
            updated_at=existing.updated_at,
        )
    else:
        new_pref = PreferencesDB(
            user_id=user_id_str,
            max_budget=payload.max_budget,
            min_size=payload.min_size,
            # ignore location_area entirely in DB
            rooms=payload.rooms,
        )
        db.add(new_pref)
        db.commit()
        db.refresh(new_pref)

        return PreferenceRead(
            id=new_pref.id,
            user_id=new_pref.user_id,
            max_budget=new_pref.max_budget,
            min_size=new_pref.min_size,
            location_area=None,
            rooms=new_pref.rooms,
            created_at=new_pref.created_at,
            updated_at=new_pref.updated_at,
        )

## GET /{userId} - Get preferences for a specific user
@app.get("/{userId}", response_model=PreferenceRead)
def get_user_preferences(
    userId: UUID = Path(..., description="The unique ID of the user"),
    db: Session = Depends(get_db)
):
    """Get preferences for a specific user."""
    user_id_str = str(userId)

    pref = (
        db.query(PreferencesDB)
        .filter(PreferencesDB.user_id == user_id_str)
        .first()
    )

    if not pref:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Preferences not found for this user"
        )

    return PreferenceRead(
        id=pref.id,
        user_id=pref.user_id,
        max_budget=pref.max_budget,
        min_size=pref.min_size,
        location_area=None,
        rooms=pref.rooms,
        created_at=pref.created_at,
        updated_at=pref.updated_at,
    )

## DELETE /{userId} - Delete a user's preferences
@app.delete("/{userId}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_preferences(
    userId: UUID = Path(..., description="The unique ID of the user"),
    db: Session = Depends(get_db)
):
    """Delete a user's preferences."""
    user_id_str = str(userId)

    pref = (
        db.query(PreferencesDB)
        .filter(PreferencesDB.user_id == user_id_str)
        .first()
    )

    if not pref:
        # 204 even if nothing deleted is fine
        return

    db.delete(pref)
    db.commit()
    return

## PATCH /{userId} - Partially update a user's preferences
@app.patch("/{userId}", response_model=PreferenceRead)
def update_user_preferences(
    payload: PreferenceUpdate,
    userId: UUID = Path(..., description="The unique ID of the user"),
    db: Session = Depends(get_db)
):
    """Partially update preferences for a specific user."""
    
    user_id_str = str(userId)

    pref = (
        db.query(PreferencesDB)
        .filter(PreferencesDB.user_id == user_id_str)
        .first()
    )

    if not pref:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Preferences not found for this user"
        )

    update_data = payload.model_dump(exclude_unset=True)

    if "max_budget" in update_data:
        pref.max_budget = update_data["max_budget"]
    if "min_size" in update_data:
        pref.min_size = update_data["min_size"]
    # ignore location_area on purpose
    if "rooms" in update_data:
        pref.rooms = update_data["rooms"]

    pref.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(pref)

    return PreferenceRead(
        id=pref.id,
        user_id=pref.user_id,
        max_budget=pref.max_budget,
        min_size=pref.min_size,
        location_area=None,
        rooms=pref.rooms,
        created_at=pref.created_at,
        updated_at=pref.updated_at,
    )

# -----------------------------------------------------------------------------
# Health endpoints
# -----------------------------------------------------------------------------

def make_health(echo: Optional[str], path_echo: Optional[str]=None) -> Health:
    return Health(
        status=200,
        status_message="OK",
        timestamp=datetime.utcnow().isoformat() + "Z",
        ip_address=socket.gethostbyname(socket.gethostname()),
        echo=echo,
        path_echo=path_echo
    )

@app.get("/health", response_model=Health)
def get_health_no_path(echo: str | None = Query(None, description="Optional echo string")):
    # Works because path_echo is optional in the model
    return make_health(echo=echo, path_echo=None)

@app.get("/health/{path_echo}", response_model=Health)
def get_health_with_path(
    path_echo: str = Path(..., description="Required echo in the URL path"),
    echo: str | None = Query(None, description="Optional echo string"),
):
    return make_health(echo=echo, path_echo=path_echo)

# -----------------------------------------------------------------------------
# Entrypoint
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
