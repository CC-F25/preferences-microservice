from sqlalchemy import Column, String, DateTime
from database import Base
import uuid
from datetime import datetime

class PreferencesDB(Base):
    __tablename__ = "preferences"

    # columns match the Pydantic model fields
    user_id = Column(CHAR(36), nullable=False, index=True)
    max_budget = Column(Integer, nullable=True)
    min_size = Column(Integer, nullable=True)
    location_area = Column(VARCHAR(255), nullable=True)
    rooms = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
