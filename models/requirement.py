from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON
from datetime import datetime
from database import Base

class Requirement(Base):
    __tablename__ = "requirements"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, nullable=True)
    client_name = Column(String, nullable=True)
    title = Column(String, nullable=False)
    category = Column(String, nullable=False)
    quantity = Column(String, nullable=False)
    description = Column(String, nullable=False)
    budget = Column(Float, nullable=True)
    deadline = Column(String, nullable=True)
    fulfillment = Column(String, default="delivery") # delivery, pickup, service
    city = Column(String, nullable=False)
    state = Column(String, default="Tamil Nadu", nullable=True)
    pincode = Column(String, nullable=True)
    address = Column(String, nullable=True)
    brand = Column(String, nullable=True)
    condition = Column(String, nullable=True)
    allow_contact = Column(Boolean, default=True)
    specifications = Column(JSON, nullable=True, default=dict)  # Dynamic category specifications
    status = Column(String, default="open") # open, closed, completed
    created_at = Column(DateTime, default=datetime.utcnow)
