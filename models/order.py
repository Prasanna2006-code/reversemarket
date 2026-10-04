from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from datetime import datetime
from database import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, index=True)  # e.g. "ORD-1728001234"
    requirement_id = Column(Integer, nullable=True)
    requirement_title = Column(String, nullable=True)
    offer_id = Column(Integer, nullable=True)
    client_id = Column(Integer, nullable=True)
    client_name = Column(String, nullable=True)
    dealer_id = Column(Integer, nullable=True)
    dealer_name = Column(String, nullable=False)

    # Product details preserved at order time
    product_id = Column(Integer, nullable=True)
    product_title = Column(String, nullable=True)
    quantity = Column(Integer, default=1)
    specifications = Column(JSON, nullable=True, default=dict)  # Snapshot of product specs at order time

    delivery_days = Column(Integer, default=5)
    delivery_address = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, default="Tamil Nadu")
    pincode = Column(String, nullable=True)
    payment_method = Column(String, default="UPI")
    amount = Column(Float, nullable=False)
    status = Column(String, default="Confirmed")  # Confirmed, In Transit, Delivered, Cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
