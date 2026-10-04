# ai/features.py
"""
AI Feature Extraction Engine for ReverseMarket.
Extracts 12 robust, normalized features for matching client requirements
with dealer products and offers. Handles missing values gracefully.
"""

import re
from datetime import datetime


def condition_to_score(condition):
    c = str(condition or "New").strip().lower()
    if c == "new":
        return 1.0
    elif c in ["refurbished", "renewed"]:
        return 0.7
    elif c in ["used", "second hand", "surplus"]:
        return 0.4
    return 0.5


def warranty_to_months(warranty):
    """Missing or empty warranty safely yields 0.0 months."""
    if not warranty:
        return 0.0

    w = str(warranty).lower()
    numbers = re.findall(r"\d+", w)
    if not numbers:
        return 0.0

    val = float(numbers[0])
    if "year" in w or "yr" in w:
        return val * 12.0
    return val


def payment_to_score(payment_terms):
    if not payment_terms:
        return 0.7  # Default neutral score for missing payment terms

    p = str(payment_terms).lower()
    if "cod" in p or "cash" in p or "delivery" in p or "inspection" in p:
        return 1.0
    if "upi" in p or "escrow" in p:
        return 0.95
    if "net 30" in p or "50%" in p or "30%" in p:
        return 0.8
    if "net 60" in p:
        return 0.6
    if "100% advance" in p:
        return 0.4
    return 0.7


def quantity_to_number(quantity):
    if quantity is None:
        return 1.0
    try:
        return float(quantity)
    except (ValueError, TypeError):
        nums = re.findall(r"\d+", str(quantity))
        return float(nums[0]) if nums else 1.0


def category_match_score(req_cat, offer_cat):
    if not req_cat or not offer_cat:
        return 0.8
    r = str(req_cat).strip().lower()
    o = str(offer_cat).strip().lower()
    if r == o:
        return 1.0
    # Overlapping or related categories
    electronics = {"electronics", "computers", "mobile", "software"}
    furniture = {"home", "furniture", "office"}
    if (r in electronics and o in electronics) or (r in furniture and o in furniture):
        return 0.85
    return 0.2


def brand_match_score(req_brand, offer_brand, offer_title=""):
    # If client didn't specify brand, DO NOT penalize
    if not req_brand or str(req_brand).strip().lower() in ["", "none", "any", "all"]:
        return 1.0

    target = str(req_brand).strip().lower()
    off_b = str(offer_brand or "").strip().lower()
    off_t = str(offer_title or "").strip().lower()

    if target in off_b or off_b in target:
        return 1.0
    if target in off_t:
        return 0.95
    return 0.2


def specification_match_score(req_specs, offer_specs, offer_text=""):
    """
    Evaluates category-specific technical details.
    If client specified no specs, returns 1.0 (no penalty for missing specs).
    """
    if not isinstance(req_specs, dict) or not req_specs:
        return 1.0

    # Filter out empty preferences
    valid_req = {k.lower(): str(v).strip().lower() for k, v in req_specs.items() if v and str(v).strip()}
    if not valid_req:
        return 1.0

    offer_dict = {}
    if isinstance(offer_specs, dict):
        offer_dict = {k.lower(): str(v).strip().lower() for k, v in offer_specs.items() if v}

    text_corpus = (offer_text or "").lower()

    matched = 0
    for key, req_val in valid_req.items():
        if key in offer_dict:
            off_val = offer_dict[key]
            if req_val in off_val or off_val in req_val:
                matched += 1
                continue
        if req_val in text_corpus:
            matched += 1

    return float(matched / len(valid_req))


def condition_match_score(req_cond, offer_cond):
    r = str(req_cond or "").strip().lower()
    o = str(offer_cond or "New").strip().lower()

    if not r or r in ["any", "all", "none"]:
        return 1.0
    if r == o:
        return 1.0
    if r == "new" and o != "new":
        return 0.3
    if r in ["used", "refurbished"] and o == "new":
        return 1.0
    return 0.5


def stock_available_score(stock, req_quantity):
    qty = quantity_to_number(req_quantity)
    if stock is None:
        return 1.0
    try:
        s = float(stock)
        if s >= qty:
            return 1.0
        if s > 0:
            return max(0.1, s / max(qty, 1.0))
        return 0.1
    except (ValueError, TypeError):
        return 1.0


def budget_fit_and_ratio(budget, offer_price):
    """
    Returns (budget_fit, price_ratio).
    If client didn't specify budget, returns (1.0, 1.0) without penalizing.
    """
    try:
        b = float(budget or 0)
        p = float(offer_price or 0)
        if b <= 0:
            return 1.0, 1.0
        ratio = p / b
        if p <= b:
            fit = 1.0 - 0.15 * max(0.0, ratio - 0.8)
        else:
            fit = max(0.0, 1.0 - (p - b) / b)
        return round(fit, 4), round(ratio, 4)
    except (ValueError, TypeError):
        return 1.0, 1.0


def delivery_fit_score(delivery_days, deadline_str=None):
    d_days = float(delivery_days or 5)
    if deadline_str:
        try:
            deadline = datetime.strptime(str(deadline_str).split("T")[0], "%Y-%m-%d")
            days_allowed = (deadline - datetime.utcnow()).days
            if days_allowed > 0:
                return 1.0 if d_days <= days_allowed else max(0.1, 1.0 - (d_days - days_allowed) / 10.0)
        except Exception:
            pass

    if d_days <= 3:
        return 1.0
    elif d_days <= 7:
        return 0.85
    elif d_days <= 14:
        return 0.65
    return 0.4


def create_features(requirement, offer, product=None):
    """
    Extract 12 normalized numerical features from requirement and offer/product.
    All missing attributes fall back safely to non-penalizing defaults.
    """
    # 1. Category match
    req_cat = getattr(requirement, "category", None)
    off_cat = getattr(offer, "product_category", None) or (getattr(product, "category", None) if product else req_cat)
    cat_match = category_match_score(req_cat, off_cat)

    # 2. Brand match
    req_brand = getattr(requirement, "brand", None)
    off_brand = getattr(offer, "product_brand", None) or (getattr(product, "brand", None) if product else None)
    off_title = getattr(offer, "product_title", "") or getattr(offer, "requirement_title", "")
    brand_match = brand_match_score(req_brand, off_brand, off_title)

    # 3. Specification match
    req_specs = getattr(requirement, "specifications", None) or {}
    off_specs = getattr(offer, "product_specifications", None) or (getattr(product, "specifications", None) if product else {})
    combined_desc = f"{off_title} {getattr(offer, 'message', '')} {getattr(offer, 'product_description', '')}"
    spec_match = specification_match_score(req_specs, off_specs, combined_desc)

    # 4. Condition match
    req_cond = getattr(requirement, "condition", None)
    off_cond = getattr(offer, "condition", None)
    cond_match = condition_match_score(req_cond, off_cond)

    # 5. Stock available
    stock_val = getattr(product, "stock", None) if product else None
    stock_avail = stock_available_score(stock_val, getattr(requirement, "quantity", 1))

    # 6 & 7. Budget fit & Price ratio
    budget_fit, price_ratio = budget_fit_and_ratio(getattr(requirement, "budget", None), getattr(offer, "price", 0))

    # 8. Delivery fit
    deliv_fit = delivery_fit_score(getattr(offer, "delivery_days", 5), getattr(requirement, "deadline", None))

    # 9. Warranty (normalized by 36 months)
    warranty_months = warranty_to_months(getattr(offer, "warranty", None))
    warranty_norm = min(warranty_months / 36.0, 1.0)

    # 10. Dealer rating (normalized by 5.0)
    rating = float(getattr(offer, "rating", 4.5) or 4.5)
    dealer_rating = min(max(rating / 5.0, 0.0), 1.0)

    # 11. Dealer reviews (normalized by 200)
    reviews = float(getattr(offer, "reviews", 50) or 50)
    dealer_reviews = min(reviews / 200.0, 1.0)

    # 12. Payment terms
    payment_score = payment_to_score(getattr(offer, "payment_terms", None))

    return [
        cat_match,
        brand_match,
        spec_match,
        cond_match,
        stock_avail,
        budget_fit,
        price_ratio,
        deliv_fit,
        warranty_norm,
        dealer_rating,
        dealer_reviews,
        payment_score,
    ]