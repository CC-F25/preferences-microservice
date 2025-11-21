# users-microservice

# Program Description
Preferences Microservice

This microservice manages user housing preferences such as max budget, minimum size, preferred location/area, and number of rooms.

# Installation

- python 3.10+
- create a venv or conda environment
- `pip install requirements.txt`

# Program Execution

when using conda .env
`python .\main.py`

alternatively-
`uvicorn main:app --reload`

# Models and the CRUD Operations:

1) Preferences

PreferenceCreate
PreferenceRead
PreferenceUpdate

## **Listing Model Endpoints**
- GET / (retrievs ALL preferences)
- POST / (create or update user's preferences)
- GET /{userId} (retrieve a user's preferences)
- PATCH /{userId} (partially update a user's preferences}
- DELETE /{userId} (delete user's preferences)

