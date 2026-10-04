# ai/train.py
"""
ReverseMarket AI Model Training Pipeline
Generates a comprehensive seed dataset (400+ samples) reflecting realistic
buyer preferences, incorporates real marketplace outcomes from the database,
and trains a Scikit-Learn MLPRegressor neural network.
"""

import os
import random
import numpy as np
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from ai.model import create_model

MODEL_PATH = "ai/match_model.pkl"
SCALER_PATH = "ai/scaler.pkl"


def compute_target_score(features):
    """
    Computes a realistic ground-truth preference score (0.0 to 1.0)
    based on the 12 normalized feature dimensions:
    0: cat_match (weight 0.20)
    1: brand_match (weight 0.12)
    2: spec_match (weight 0.15)
    3: cond_match (weight 0.08)
    4: stock_avail (weight 0.06)
    5: budget_fit (weight 0.14)
    6: price_ratio (penalty if > 1.0)
    7: deliv_fit (weight 0.08)
    8: warranty_norm (weight 0.05)
    9: dealer_rating (weight 0.07)
    10: dealer_reviews (weight 0.02)
    11: payment_score (weight 0.03)
    """
    (
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
    ) = features

    # Hard rejection penalty if completely wrong category
    if cat_match < 0.3:
        return 0.15

    base_score = (
        0.20 * cat_match +
        0.12 * brand_match +
        0.15 * spec_match +
        0.08 * cond_match +
        0.06 * stock_avail +
        0.14 * budget_fit +
        0.08 * deliv_fit +
        0.05 * warranty_norm +
        0.07 * dealer_rating +
        0.02 * dealer_reviews +
        0.03 * payment_score
    )

    # Extra penalty for extreme price overshoots
    if price_ratio > 1.25:
        base_score -= 0.15 * (price_ratio - 1.25)

    # Noise for real-world variation (+/- 2%)
    noise = (random.random() - 0.5) * 0.04
    final_score = max(0.10, min(0.99, base_score + noise))
    return round(float(final_score), 4)


def generate_seed_data(num_samples=450):
    """
    Generates a diverse synthetic seed dataset across categories,
    matching and non-matching specs, price variations, and missing fields.
    """
    random.seed(42)
    np.random.seed(42)

    X_list = []
    y_list = []

    for _ in range(num_samples):
        # 1. Category match: mostly matched, occasionally related or mismatched
        cat_rand = random.random()
        cat_match = 1.0 if cat_rand > 0.15 else (0.85 if cat_rand > 0.05 else 0.2)

        # 2. Brand match: 1.0 (exact or not specified), 0.95 (in title), 0.2 (mismatch)
        brand_rand = random.random()
        brand_match = 1.0 if brand_rand > 0.25 else (0.95 if brand_rand > 0.15 else 0.2)

        # 3. Spec match: 0.2 to 1.0
        spec_match = random.choice([1.0, 1.0, 0.85, 0.75, 0.60, 0.40, 1.0])

        # 4. Condition match
        cond_match = random.choice([1.0, 1.0, 1.0, 0.7, 0.5, 0.3])

        # 5. Stock availability
        stock_avail = random.choice([1.0, 1.0, 1.0, 0.8, 0.5, 0.2])

        # 6 & 7. Budget fit & price ratio
        price_ratio = round(random.uniform(0.65, 1.45), 2)
        if price_ratio <= 1.0:
            budget_fit = round(1.0 - 0.15 * max(0.0, price_ratio - 0.8), 2)
        else:
            budget_fit = max(0.1, round(1.0 - (price_ratio - 1.0), 2))

        # 8. Delivery fit
        deliv_fit = random.choice([1.0, 0.85, 0.65, 0.4])

        # 9. Warranty norm (0 to 1)
        warranty_norm = random.choice([0.0, 0.33, 0.66, 1.0])

        # 10. Dealer rating (3.5 to 5.0 -> 0.7 to 1.0)
        dealer_rating = round(random.uniform(0.70, 1.0), 2)

        # 11. Dealer reviews (0 to 1)
        dealer_reviews = round(random.uniform(0.05, 1.0), 2)

        # 12. Payment terms
        payment_score = random.choice([1.0, 0.95, 0.8, 0.6, 0.7])

        feat = [
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

        target = compute_target_score(feat)
        X_list.append(feat)
        y_list.append(target)

    return np.array(X_list, dtype=float), np.array(y_list, dtype=float)


def load_real_marketplace_data(db_session=None):
    """
    Loads historical user selections from the database if available.
    """
    if db_session is None:
        try:
            from database import SessionLocal
            from models.training_data import TrainingData
            db = SessionLocal()
            records = db.query(TrainingData).all()
            db.close()
        except Exception:
            return None, None
    else:
        from models.training_data import TrainingData
        records = db_session.query(TrainingData).all()

    if not records:
        return None, None

    real_X = []
    real_y = []
    for r in records:
        if isinstance(r.features, list) and len(r.features) == 12:
            real_X.append(r.features)
            real_y.append(r.target_score)

    if not real_X:
        return None, None

    return np.array(real_X, dtype=float), np.array(real_y, dtype=float)


def train_model(db_session=None):
    print("Preparing training dataset...")
    X_seed, y_seed = generate_seed_data(num_samples=500)

    # Check for real marketplace outcomes
    X_real, y_real = load_real_marketplace_data(db_session)
    if X_real is not None and len(X_real) > 0:
        print(f"Incorporating {len(X_real)} real marketplace outcomes into training set...")
        X = np.vstack([X_seed, X_real])
        y = np.concatenate([y_seed, y_real])
    else:
        X, y = X_seed, y_seed

    print(f"Total training dataset size: {len(X)} samples.")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.15, random_state=42
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    print("Building neural network architecture...")
    model = create_model(X_train_scaled.shape[1])

    print("Training MLPRegressor model...")
    model.fit(X_train_scaled, y_train)

    train_score = model.score(X_train_scaled, y_train)
    test_score = model.score(X_test_scaled, y_test)
    print(f"Model R² Train: {train_score:.4f}, Test: {test_score:.4f}")

    os.makedirs("ai", exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)

    print(f"Model successfully saved to: {MODEL_PATH}")
    print(f"Scaler successfully saved to: {SCALER_PATH}")
    return model, scaler


if __name__ == "__main__":
    train_model()