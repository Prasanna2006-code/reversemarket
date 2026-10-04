"""
ReverseMarket — FastAPI Backend
Connects Users, Requirements, Products, Offers, Orders, and AI.
Compatible with SQLite (local) and PostgreSQL (cloud).
"""

import os
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer

from database import engine, Base, get_db
from models.user import User
from models.product import Product
from models.requirement import Requirement
from models.offer import Offer
from models.order import Order
from models.training_data import TrainingData
from ai.features import create_features

# ---------------------------------------------------------------------------
# APP SETUP
# ---------------------------------------------------------------------------

Base.metadata.create_all(bind=engine)

app = FastAPI(title="ReverseMarket API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

# ---------------------------------------------------------------------------
# AUTH CONFIG (Cloud-ready environment variables)
# ---------------------------------------------------------------------------

SECRET_KEY = os.getenv("SECRET_KEY", "reversemarket-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 1440 * 7  # 7 days

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def hash_password(password: str) -> str:
    # Plain-text storage — store as-is, no hashing
    return password


def verify_password(plain: str, stored: str) -> bool:
    # Plain comparison — check email/username already in DB then match password directly
    return plain == stored


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Returns the authenticated user or None if no/invalid token."""
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            return None
        user = db.query(User).filter(User.id == user_id).first()
        return user
    except JWTError:
        return None


def require_auth(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Raises 401 if not authenticated."""
    user = get_current_user(token, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please log in.",
        )
    return user


# ---------------------------------------------------------------------------
# PYDANTIC SCHEMAS
# ---------------------------------------------------------------------------

# --- Auth ---
class RegisterRequest(BaseModel):
    name: str
    email: str
    phone: str = ""
    password: str = Field(..., min_length=6, max_length=72)
    account_type: str = "client"


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    token: str
    user_id: int
    name: str
    email: str
    account_type: str


# --- Product (Dealer Catalog) ---
class ProductCreate(BaseModel):
    title: str
    category: str
    brand: Optional[str] = None
    price: float
    stock: int = 0
    condition: Optional[str] = "New"
    warranty: Optional[str] = None
    description: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None  # Category-specific details


class ProductUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    condition: Optional[str] = None
    warranty: Optional[str] = None
    description: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None


class ProductOut(BaseModel):
    id: int
    dealer_id: Optional[int] = None
    dealer_name: Optional[str] = None
    title: str
    category: str
    brand: Optional[str] = None
    price: float
    stock: int
    condition: Optional[str] = None
    warranty: Optional[str] = None
    description: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# --- Requirement (Client) ---
# Requirement 1 & 5: Not all fields are compulsory!
class RequirementCreate(BaseModel):
    # Required
    title: str
    category: str
    quantity: str = "1"
    description: str
    city: str

    # Optional (Gracefully handled if left blank)
    budget: Optional[float] = None
    deadline: Optional[str] = None
    fulfillment: Optional[str] = "delivery"
    state: Optional[str] = "Tamil Nadu"
    pincode: Optional[str] = None
    address: Optional[str] = None
    brand: Optional[str] = None
    condition: Optional[str] = None
    allow_contact: Optional[bool] = True
    specifications: Optional[Dict[str, Any]] = None  # Category-specific details (Processor, RAM, etc.)


class RequirementOut(BaseModel):
    id: int
    client_id: Optional[int] = None
    client_name: Optional[str] = None
    title: str
    category: str
    quantity: str
    description: str
    budget: Optional[float] = None
    deadline: Optional[str] = None
    fulfillment: Optional[str] = None
    city: str
    state: Optional[str] = None
    pincode: Optional[str] = None
    address: Optional[str] = None
    brand: Optional[str] = None
    condition: Optional[str] = None
    allow_contact: Optional[bool] = None
    specifications: Optional[Dict[str, Any]] = None
    status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# --- Offer (Dealer) ---
# Requirement 1 & 4: Select existing product OR enter basic details
class OfferCreate(BaseModel):
    requirement_id: int
    product_id: Optional[int] = None         # Select from dealer's catalog
    price: float                             # Quoted offer price
    delivery_days: int                       # Delivery timeline
    warranty: Optional[str] = None           # Optional
    condition: Optional[str] = "New"         # Optional
    payment_terms: Optional[str] = None      # Optional
    message: Optional[str] = None            # Optional


class OfferOut(BaseModel):
    id: int
    requirement_id: int
    requirement_title: Optional[str] = None
    dealer_id: Optional[int] = None
    dealer_name: str
    verified: bool
    rating: float
    reviews: int
    product_id: Optional[int] = None
    product_title: Optional[str] = None
    product_brand: Optional[str] = None
    product_category: Optional[str] = None
    product_description: Optional[str] = None
    product_specifications: Optional[Dict[str, Any]] = None
    price: float
    delivery_days: int
    warranty: Optional[str] = None
    condition: Optional[str] = None
    payment_terms: Optional[str] = None
    message: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# --- Order ---
# Requirement 11: Order preserves product details & specifications snapshot
class OrderCreate(BaseModel):
    offer_id: int
    delivery_address: str
    city: str
    state: Optional[str] = "Tamil Nadu"
    pincode: Optional[str] = None
    payment_method: Optional[str] = "UPI"
    quantity: Optional[int] = 1


class OrderOut(BaseModel):
    id: str
    requirement_id: Optional[int] = None
    requirement_title: Optional[str] = None
    offer_id: Optional[int] = None
    client_id: Optional[int] = None
    client_name: Optional[str] = None
    dealer_id: Optional[int] = None
    dealer_name: str
    product_id: Optional[int] = None
    product_title: Optional[str] = None
    quantity: int
    specifications: Optional[Dict[str, Any]] = None
    delivery_days: int
    delivery_address: str
    city: str
    state: str
    pincode: Optional[str] = None
    payment_method: str
    amount: float
    status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# AUTH ROUTES
# ---------------------------------------------------------------------------

@app.post("/api/auth/register", response_model=AuthResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == req.email.strip().lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email is already registered")

    user = User(
        name=req.name.strip(),
        email=req.email.strip().lower(),
        phone=req.phone.strip(),
        hashed_password=hash_password(req.password),
        account_type=req.account_type.strip().lower(),
        verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"user_id": user.id, "account_type": user.account_type})
    return AuthResponse(
        token=token,
        user_id=user.id,
        name=user.name,
        email=user.email,
        account_type=user.account_type,
    )


@app.post("/api/auth/login", response_model=AuthResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email.strip().lower()).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"user_id": user.id, "account_type": user.account_type})
    return AuthResponse(
        token=token,
        user_id=user.id,
        name=user.name,
        email=user.email,
        account_type=user.account_type,
    )


@app.get("/api/auth/me")
def get_me(user: User = Depends(require_auth)):
    return {
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
        "account_type": user.account_type,
    }


# ---------------------------------------------------------------------------
# PRODUCT ROUTES (Dealer Catalog)
# ---------------------------------------------------------------------------

@app.post("/api/products", response_model=ProductOut)
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """
    Dealer creates a catalog product once, including category-specific specifications.
    """
    product = Product(
        dealer_id=user.id,
        dealer_name=user.name,
        title=data.title.strip(),
        category=data.category.strip().lower(),
        brand=data.brand.strip() if data.brand else None,
        price=data.price,
        stock=data.stock,
        condition=data.condition or "New",
        warranty=data.warranty.strip() if data.warranty else None,
        description=data.description.strip() if data.description else None,
        specifications=data.specifications or {},
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@app.get("/api/products", response_model=List[ProductOut])
def list_my_products(
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """List products belonging to the authenticated dealer."""
    return db.query(Product).filter(Product.dealer_id == user.id).order_by(Product.created_at.desc()).all()


@app.get("/api/products/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.put("/api/products/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    product = db.query(Product).filter(Product.id == product_id, Product.dealer_id == user.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or not owned by you")

    for field, value in data.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


@app.delete("/api/products/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    product = db.query(Product).filter(Product.id == product_id, Product.dealer_id == user.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or not owned by you")

    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}


# ---------------------------------------------------------------------------
# REQUIREMENT ROUTES
# ---------------------------------------------------------------------------

@app.post("/api/requirements", response_model=RequirementOut)
def create_requirement(
    data: RequirementCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """
    Client posts a requirement. Supports optional budget, brand, deadline,
    and category-specific specifications.
    """
    req = Requirement(
        client_id=user.id,
        client_name=user.name,
        title=data.title.strip(),
        category=data.category.strip().lower(),
        quantity=data.quantity.strip() if data.quantity else "1",
        description=data.description.strip(),
        budget=data.budget,                 # Optional
        deadline=data.deadline,             # Optional
        fulfillment=data.fulfillment or "delivery",
        city=data.city.strip(),
        state=data.state.strip() if data.state else "Tamil Nadu",
        pincode=data.pincode.strip() if data.pincode else None,
        address=data.address.strip() if data.address else None,
        brand=data.brand.strip() if data.brand else None,
        condition=data.condition.strip() if data.condition else None,
        allow_contact=data.allow_contact if data.allow_contact is not None else True,
        specifications=data.specifications or {},
        status="open",
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


@app.get("/api/requirements", response_model=List[RequirementOut])
def list_all_requirements(db: Session = Depends(get_db)):
    """List all open requirements for dealers to browse."""
    return db.query(Requirement).filter(Requirement.status == "open").order_by(Requirement.created_at.desc()).all()


@app.get("/api/requirements/my", response_model=List[RequirementOut])
def list_my_requirements(
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """List requirements posted by the authenticated client."""
    return db.query(Requirement).filter(Requirement.client_id == user.id).order_by(Requirement.created_at.desc()).all()


@app.get("/api/requirements/{req_id}", response_model=RequirementOut)
def get_requirement(req_id: int, db: Session = Depends(get_db)):
    req = db.query(Requirement).filter(Requirement.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return req


# ---------------------------------------------------------------------------
# OFFER ROUTES
# ---------------------------------------------------------------------------

@app.post("/api/offers", response_model=OfferOut)
def create_offer(
    data: OfferCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """
    Dealer submits an offer for a requirement. If product_id is selected from their
    catalog, the product details and category specs are automatically populated.
    """
    req = db.query(Requirement).filter(Requirement.id == data.requirement_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")

    product_title = None
    product_brand = None
    product_category = None
    product_description = None
    product_specifications = {}

    if data.product_id:
        product = db.query(Product).filter(
            Product.id == data.product_id,
            Product.dealer_id == user.id
        ).first()
        if not product:
            raise HTTPException(status_code=404, detail="Selected product not found in your catalog")

        product_title = product.title
        product_brand = product.brand
        product_category = product.category
        product_description = product.description
        product_specifications = product.specifications or {}

    offer = Offer(
        requirement_id=data.requirement_id,
        requirement_title=req.title,
        dealer_id=user.id,
        dealer_name=user.name,
        verified=True,
        rating=4.8,
        reviews=120,
        product_id=data.product_id,
        product_title=product_title,
        product_brand=product_brand,
        product_category=product_category,
        product_description=product_description,
        product_specifications=product_specifications,
        price=data.price,
        delivery_days=data.delivery_days,
        warranty=data.warranty.strip() if data.warranty else None,
        condition=data.condition or "New",
        payment_terms=data.payment_terms.strip() if data.payment_terms else None,
        message=data.message.strip() if data.message else None,
        status="pending",
    )
    db.add(offer)
    db.commit()
    db.refresh(offer)
    return offer


@app.get("/api/offers", response_model=List[OfferOut])
def list_offers(
    requirement_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """List offers, optionally filtered by requirement_id."""
    query = db.query(Offer)
    if requirement_id:
        query = query.filter(Offer.requirement_id == requirement_id)
    return query.order_by(Offer.created_at.desc()).all()


@app.get("/api/dealers/my-offers", response_model=List[OfferOut])
def list_dealer_offers(
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """List offers submitted by the authenticated dealer."""
    return db.query(Offer).filter(Offer.dealer_id == user.id).order_by(Offer.created_at.desc()).all()


@app.get("/api/offers/{offer_id}", response_model=OfferOut)
def get_offer(offer_id: int, db: Session = Depends(get_db)):
    offer = db.query(Offer).filter(Offer.id == offer_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    return offer


# ---------------------------------------------------------------------------
# AI RANKING & COMPARISON ROUTE
# ---------------------------------------------------------------------------

@app.get("/api/ai/rank-offers/{requirement_id}")
def rank_offers_for_requirement(requirement_id: int, db: Session = Depends(get_db)):
    """
    Ranks ALL offers for a requirement using the neural network.
    Requirement 9: AI ranks ALL offers, not just three.
    Requirement 10: Returns top 3 comparison package.
    """
    req = db.query(Requirement).filter(Requirement.id == requirement_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")

    offers = db.query(Offer).filter(Offer.requirement_id == requirement_id).all()
    if not offers:
        return {"all_offers": [], "top_3": []}

    # Fetch associated products for richer matching
    product_ids = [o.product_id for o in offers if o.product_id]
    products = db.query(Product).filter(Product.id.in_(product_ids)).all() if product_ids else []
    products_by_id = {p.id: p for p in products}

    from ai.recommender import get_recommendations
    ranked_result = get_recommendations(req, offers, products_by_id=products_by_id)

    serialized_all = []
    for item in ranked_result["all_offers"]:
        offer_data = OfferOut.model_validate(item["offer"]).model_dump()
        product_data = ProductOut.model_validate(item["product"]).model_dump() if item["product"] else None
        serialized_all.append({
            "rank": item["rank"],
            "is_top_3": item["is_top_3"],
            "match_score": item["match_score"],
            "offer": offer_data,
            "product": product_data,
        })

    serialized_top_3 = serialized_all[:3]

    return {
        "all_offers": serialized_all,
        "top_3": serialized_top_3,
    }


@app.post("/api/ai/retrain")
def retrain_ai_model(db: Session = Depends(get_db)):
    """
    Retrain the AI MLP model combining synthetic seed data
    and real marketplace outcomes from the database.
    """
    from ai.train import train_model
    model, scaler = train_model(db_session=db)
    return {"message": "AI neural network model retrained successfully"}


# ---------------------------------------------------------------------------
# ORDER ROUTES
# ---------------------------------------------------------------------------

@app.post("/api/orders", response_model=OrderOut)
def create_order(
    data: OrderCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """
    Client selects an offer and confirms order.
    Requirement 11: Order preserves product details & specifications snapshot.
    Requirement 13: Store marketplace outcomes for future AI retraining!
    """
    offer = db.query(Offer).filter(Offer.id == data.offer_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    # Mark selected offer
    offer.status = "selected"

    # Mark other competing offers for this requirement as not_selected
    competing_offers = db.query(Offer).filter(
        Offer.requirement_id == offer.requirement_id,
        Offer.id != offer.id
    ).all()
    for o in competing_offers:
        o.status = "declined"

    # Close/complete the requirement
    req = db.query(Requirement).filter(Requirement.id == offer.requirement_id).first()
    if req:
        req.status = "completed"

    # Fetch product to preserve snapshot of specifications
    product = None
    if offer.product_id:
        product = db.query(Product).filter(Product.id == offer.product_id).first()

    specs_snapshot = {}
    if product and product.specifications:
        specs_snapshot = product.specifications
    elif offer.product_specifications:
        specs_snapshot = offer.product_specifications

    order_id = f"ORD-{int(time.time())}"
    order = Order(
        id=order_id,
        requirement_id=offer.requirement_id,
        requirement_title=req.title if req else offer.requirement_title,
        offer_id=offer.id,
        client_id=user.id,
        client_name=user.name,
        dealer_id=offer.dealer_id,
        dealer_name=offer.dealer_name,
        product_id=offer.product_id,
        product_title=offer.product_title or (product.title if product else offer.requirement_title),
        quantity=data.quantity or 1,
        specifications=specs_snapshot,  # Preserved snapshot
        delivery_days=offer.delivery_days,
        delivery_address=data.delivery_address,
        city=data.city,
        state=data.state or "Tamil Nadu",
        pincode=data.pincode,
        payment_method=data.payment_method or "UPI",
        amount=offer.price,
        status="Confirmed",
    )
    db.add(order)

    # --- REQUIREMENT 13: LOG REAL MARKETPLACE OUTCOME FOR MODEL RETRAINING ---
    try:
        # 1. Positive outcome for selected dealer
        pos_features = create_features(req, offer, product=product)
        pos_log = TrainingData(
            requirement_id=offer.requirement_id,
            offer_id=offer.id,
            features=pos_features,
            target_score=0.96,
            is_selected=True,
        )
        db.add(pos_log)

        # 2. Negative/non-selected outcome for competing offers
        for comp in competing_offers:
            comp_prod = db.query(Product).filter(Product.id == comp.product_id).first() if comp.product_id else None
            comp_features = create_features(req, comp, product=comp_prod)
            neg_log = TrainingData(
                requirement_id=offer.requirement_id,
                offer_id=comp.id,
                features=comp_features,
                target_score=0.35,
                is_selected=False,
            )
            db.add(neg_log)
    except Exception as e:
        print(f"Non-fatal error logging training data: {e}")

    db.commit()
    db.refresh(order)
    return order


@app.get("/api/orders", response_model=List[OrderOut])
def list_my_orders(
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """List orders for the authenticated client."""
    return db.query(Order).filter(Order.client_id == user.id).order_by(Order.created_at.desc()).all()


@app.get("/api/dealers/my-orders", response_model=List[OrderOut])
def list_dealer_orders(
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """List orders received by the authenticated dealer."""
    return db.query(Order).filter(Order.dealer_id == user.id).order_by(Order.created_at.desc()).all()


@app.get("/api/orders/{order_id}", response_model=OrderOut)
def get_order(order_id: str, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


# ---------------------------------------------------------------------------
# ROOT / HEALTH
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {
        "status": "online",
        "app": "ReverseMarket API",
        "version": "1.1.0",
        "docs": "/docs",
        "frontend": "/frontend/index.html",
    }


# ---------------------------------------------------------------------------
# RUN
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
