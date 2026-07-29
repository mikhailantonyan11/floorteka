"""
Предсказание отмены заказа (бинарная классификация).

Признаки: delivery_time, order_price, customer_type, distance, restaurant_rating.
Модель: ансамбль (усреднение вероятностей) логистической регрессии,
неглубокого XGBoost и CatBoost.

Метрика: ROC-AUC. CV OOF ROC-AUC ~0.585.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import xgboost as xgb

FEATURES = ["delivery_time", "order_price", "distance", "restaurant_rating"]


def make_features(df: pd.DataFrame) -> pd.DataFrame:
    X = df[FEATURES].copy()
    X["is_regular"] = (df["customer_type"] == "regular").astype(int)
    return X


def build_models() -> dict:
    logreg = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=2000, class_weight="balanced")),
        ]
    )
    xgb_shallow = xgb.XGBClassifier(
        n_estimators=400,
        max_depth=2,
        learning_rate=0.01,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric="auc",
        random_state=42,
        n_jobs=-1,
    )
    cat = CatBoostClassifier(
        iterations=400,
        depth=3,
        learning_rate=0.02,
        random_state=42,
        verbose=0,
    )
    return {"logreg": logreg, "xgb": xgb_shallow, "catboost": cat}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", default="data2/train.csv")
    parser.add_argument("--test", default="data2/test.csv")
    parser.add_argument("--out", default="data2/submission.csv")
    parser.add_argument("--cv", action="store_true", help="Run 5-fold CV before predict")
    args = parser.parse_args()

    train = pd.read_csv(args.train)
    test = pd.read_csv(args.test)

    X = make_features(train)
    y = train["is_cancelled"]
    X_test = make_features(test)

    models = build_models()

    if args.cv:
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        oof_preds = []
        for name, model in models.items():
            oof = cross_val_predict(model, X, y, cv=cv, method="predict_proba", n_jobs=1)[:, 1]
            auc = roc_auc_score(y, oof)
            print(f"{name}: OOF ROC-AUC = {auc:.5f}")
            oof_preds.append(oof)
        blend = np.mean(oof_preds, axis=0)
        blend_auc = roc_auc_score(y, blend)
        print(f"Ensemble (mean): OOF ROC-AUC = {blend_auc:.5f}")
        print(f"Estimated points: {max(0.0, blend_auc - 0.55) / 0.45:.4f}")

    test_preds = []
    for model in models.values():
        model.fit(X, y)
        test_preds.append(model.predict_proba(X_test)[:, 1])
    final_proba = np.mean(test_preds, axis=0)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    submission = pd.DataFrame({"id": test["id"], "is_cancelled": final_proba})
    submission.to_csv(out, index=False)
    print(f"Saved: {out}")
    print(submission["is_cancelled"].describe())


if __name__ == "__main__":
    main()
