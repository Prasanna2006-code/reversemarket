# ai/recommender.py
"""
AI Recommender & Ranking Engine for ReverseMarket.
Ranks ALL valid dealer offers for a client's requirement using the
trained neural network, highlighting the Top 3 best matches.
"""

import os
import joblib
import numpy as np

from ai.features import create_features


MODEL_PATH = "ai/match_model.pkl"
SCALER_PATH = "ai/scaler.pkl"


def load_model():
    """Loads the model and scaler, training automatically if not found."""
    if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
        from ai.train import train_model
        return train_model()

    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    return model, scaler


def recommend_offer(requirement, offer, product=None):
    """
    Calculate the neural-network match score (0 to 100)
    between a requirement and a dealer offer.
    """
    try:
        model, scaler = load_model()
        features = create_features(requirement, offer, product=product)

        X = np.array([features], dtype=float)
        X_scaled = scaler.transform(X)

        prediction = model.predict(X_scaled)[0]

        # Convert prediction from 0-1 to 0-100 percentage
        score = float(prediction) * 100.0
        score = max(5.0, min(99.0, score))
        return round(score, 1)

    except Exception as e:
        # Fallback heuristic if ML prediction fails for any reason
        base = 75.0
        if getattr(requirement, "budget", None) and getattr(offer, "price", None):
            try:
                if float(offer.price) <= float(requirement.budget):
                    base += 10.0
                else:
                    base -= 15.0
            except Exception:
                pass
        return round(max(10.0, min(95.0, base)), 1)


def rank_offers(requirement, offers, products_by_id=None):
    """
    Score and rank ALL offers for a requirement.
    Requirement 9: AI ranks ALL offers, not just three.
    """
    products_by_id = products_by_id or {}
    ranked_offers = []

    for offer in offers:
        prod_id = getattr(offer, "product_id", None)
        product = products_by_id.get(prod_id) if prod_id else None

        score = recommend_offer(requirement, offer, product=product)

        ranked_offers.append({
            "offer": offer,
            "product": product,
            "match_score": score,
        })

    # Highest AI score first
    ranked_offers.sort(key=lambda item: item["match_score"], reverse=True)

    # Assign 1-indexed rank and top 3 flag
    for index, item in enumerate(ranked_offers, start=1):
        item["rank"] = index
        item["is_top_3"] = (index <= 3)

    return ranked_offers


def get_recommendations(requirement, offers, products_by_id=None):
    """
    Returns full ranking for all offers + designated top 3.
    """
    all_ranked = rank_offers(requirement, offers, products_by_id=products_by_id)
    return {
        "all_offers": all_ranked,
        "top_3": all_ranked[:3],
    }