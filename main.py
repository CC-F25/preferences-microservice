from __future__ import annotations

import os
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, Path, status


from .preferences import PreferenceCreate, PreferenceRead, PreferenceUpdate

# -----------------------------------------------------------------------------
# Fake In-Memory "Database"
# -----------------------------------------------------------------------------

preferences_db: Dict[UUID, PreferenceRead] = {} 

#port = int(os.environ.get("FASTAPIPORT", 8000))
port = int(os.environ.get("PORT",8080)) #cloudrun port

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
# Helper function
# -----------------------------------------------------------------------------

def make_preference_read(payload: PreferenceCreate, existing: Optional[PreferenceRead] = None) -> PreferenceRead:
    """
    Creates a new PreferenceRead object or updates an existing one.
    """
    now = datetime.utcnow()
    
    if existing:
        return PreferenceRead(
            id=existing.id,
            user_id=payload.user_id,
            max_budget=payload.max_budget,
            min_size=payload.min_size,
            location_area=payload.location_area,
            rooms=payload.rooms,
            created_at=existing.created_at,
            updated_at=now,
        )
    else:
        return PreferenceRead(
            id=uuid4(),
            user_id=payload.user_id,
            max_budget=payload.max_budget,
            min_size=payload.min_size,
            location_area=payload.location_area,
            rooms=payload.rooms,
            created_at=now,
            updated_at=now,
        )

# -----------------------------------------------------------------------------
# FastAPI Endpoints
# -----------------------------------------------------------------------------

## GET / - Get all preferences (admin/debug)
@app.get("/", response_model=List[PreferenceRead])
def get_all_preferences():
    """List of all user preferences."""
    return list(preferences_db.values())

## POST / - Create or update a user's preferences
@app.post("/", response_model=PreferenceRead, status_code=status.HTTP_200_OK)
def create_or_update_preferences(payload: PreferenceCreate):
    """
    If preferences already exist for the user, they are updated. 
    Otherwise, a new record is created.
    """
    user_id = payload.user_id
    existing_preference = next((p for p in preferences_db.values() if p.user_id == user_id), None)
    
    if existing_preference:
        new_preference = make_preference_read(payload, existing_preference)
        preferences_db[existing_preference.id] = new_preference
        return new_preference
    else:
        new_preference = make_preference_read(payload)
        preferences_db[new_preference.id] = new_preference
        return new_preference

## GET /{userId} - Get preferences for a specific user
@app.get("/{userId}", response_model=PreferenceRead)
def get_user_preferences(
    userId: UUID = Path(..., description="The unique ID of the user")
):
    """Get preferences for a specific user."""
    preference = next((p for p in preferences_db.values() if p.user_id == userId), None)
    
    if not preference:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Preferences not found for this user"
        )
    return preference

## DELETE /{userId} - Delete a user's preferences
@app.delete("/{userId}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_preferences(
    userId: UUID = Path(..., description="The unique ID of the user")
):
    """Delete a user's preferences."""
    preference_to_delete = next(((p_id, p) for p_id, p in preferences_db.items() if p.user_id == userId), None)

    if not preference_to_delete:
        return

    del preferences_db[preference_to_delete[0]]
    return

## PATCH /{userId} - Partially update a user's preferences
@app.patch("/{userId}", response_model=PreferenceRead)
def update_user_preferences(
    payload: PreferenceUpdate,
    userId: UUID = Path(..., description="The unique ID of the user")
):
    """Partially update preferences for a specific user."""
    
    preference_item = next(((p_id, p) for p_id, p in preferences_db.items() if p.user_id == userId), None)

    if not preference_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Preferences not found for this user"
        )
    
    existing_id, existing_preference = preference_item

    update_data = payload.model_dump(exclude_unset=True)
    updated_fields = existing_preference.model_copy(update=update_data)
    updated_fields.updated_at = datetime.utcnow()

    preferences_db[existing_id] = updated_fields
    
    return updated_fields

# -----------------------------------------------------------------------------
# Entrypoint
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
