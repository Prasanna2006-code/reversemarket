from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON
from datetime import datetime
from database import Base

class Offer(Base):
    __tablename__ = "offers"

    id = Column(Integer, primary_key=True, index=True)
    requirement_id = Column(Integer, nullable=False, index=True)
    requirement_title = Column(String, nullable=True)
    dealer_id = Column(Integer, nullable=True)
    dealer_name = Column(String, nullable=False)
    verified = Column(Boolean, default=True)
    rating = Column(Float, default=4.8)
    reviews = Column(Integer, default=100)

    # Product linkage — dealer selects from their catalog
    product_id = Column(Integer, nullable=True)
    product_title = Column(String, nullable=True)
    product_brand = Column(String, nullable=True)
    product_category = Column(String, nullable=True)
    product_description = Column(String, nullable=True)
    product_specifications = Column(JSON, nullable=True, default=dict)

    # Offer-specific details
    price = Column(Float, nullable=False)
    delivery_days = Column(Integer, nullable=False)
    warranty = Column(String, nullable=True)
    condition = Column(String, nullable=True, default="New")
    payment_terms = Column(String, nullable=True)
    message = Column(String, nullable=True)
    status = Column(String, default="pending")  # pending, selected, declined
    created_at = Column(DateTime, default=datetime.utcnow)
