from sqlalchemy import Column, Integer, Float, Boolean, DateTime, JSON
from datetime import datetime
from database import Base

class TrainingData(Base):
    __tablename__ = "marketplace_training_data"

    id = Column(Integer, primary_key=True, index=True)
    requirement_id = Column(Integer, nullable=False, index=True)
    offer_id = Column(Integer, nullable=False, index=True)
    features = Column(JSON, nullable=False)          # Numerical feature vector
    target_score = Column(Float, nullable=False)     # Historical/interaction target score (0.0 to 1.0)
    is_selected = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
