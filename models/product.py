from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from datetime import datetime
from database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    dealer_id = Column(Integer, nullable=True)
    dealer_name = Column(String, nullable=True)
    title = Column(String, nullable=False)
    category = Column(String, nullable=False)
    brand = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    condition = Column(String, default="New")
    warranty = Column(String, nullable=True)
    description = Column(String, nullable=True)
    specifications = Column(JSON, nullable=True, default=dict)  # Category-specific details
    created_at = Column(DateTime, default=datetime.utcnow)
