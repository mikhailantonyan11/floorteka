"""
Предсказание отмены заказа (бинарная классификация).

Признаки: delivery_time, customer_type, distance, restaurant_rating
(order_price исключён — не несёт предсказательного сигнала, см. EDA в README).

Модель: ансамбль (усреднение вероятностей) трёх алгоритмов:
  - GAM-подобный подход: изотоническая регрессия по каждому признаку
    (учитывает монотонную, но нелинейную форму зависимости) + логистическая
    регрессия поверх преобразованных признаков;
  - XGBoost с монотонными ограничениями (соответствуют направлению
    зависимости каждого признака с целевой переменной);
  - CatBoost.

Метрика: ROC-AUC. CV OOF ROC-AUC ~0.586. Обширная проверка (повторная
кросс-валидация, полиномиальные/binned признаки, взаимодействия,
неограниченный Random Forest) показала, что дальнейшее усложнение модели
не даёт прироста — это близко к достижимому пределу для этих признаков.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
import xgboost as xgb

FEATURES = ["delivery_time", "distance", "restaurant_rating"]
# Направление монотонной зависимости с вероятностью отмены:
# delivery_time (+), distance (+), restaurant_rating (-), is_regular (-)
INCREASING = [True, True, False, False]
MONOTONE_CONSTRAINTS = (1, 1, -1, -1)


def make_features(df: pd.DataFrame) -> pd.DataFrame:
    X = df[FEATURES].copy()
    X["is_regular"] = (df["customer_type"] == "regular").astype(int)
    return X


class GAMClassifier(BaseEstimator, ClassifierMixin):
    """Изотоническая регрессия по каждому признаку + логистическая регрессия."""

    def fit(self, X: np.ndarray, y: np.ndarray) -> "GAMClassifier":
        self.classes_ = np.unique(y)
        self.isotonics_ = []
        transformed = np.zeros_like(X, dtype=float)
        for j in range(X.shape[1]):
            iso = IsotonicRegression(increasing=INCREASING[j], out_of_bounds="clip")
            transformed[:, j] = iso.fit_transform(X[:, j], y)
            self.isotonics_.append(iso)
        self.clf_ = LogisticRegression(max_iter=2000, class_weight="balanced")
        self.clf_.fit(transformed, y)
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        transformed = np.zeros_like(X, dtype=float)
        for j, iso in enumerate(self.isotonics_):
            transformed[:, j] = iso.predict(X[:, j])
        return self.clf_.predict_proba(transformed)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.classes_[np.argmax(self.predict_proba(X), axis=1)]


def build_models() -> dict:
    xgb_mono = xgb.XGBClassifier(
        n_estimators=400,
        max_depth=3,
        learning_rate=0.01,
        subsample=0.8,
        colsample_bytree=0.9,
        eval_metric="auc",
        random_state=42,
        n_jobs=-1,
        monotone_constraints=MONOTONE_CONSTRAINTS,
    )
    cat = CatBoostClassifier(iterations=400, depth=3, learning_rate=0.02, random_state=42, verbose=0)
    return {"gam": GAMClassifier(), "xgb_mono": xgb_mono, "catboost": cat}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", default="data2/train.csv")
    parser.add_argument("--test", default="data2/test.csv")
    parser.add_argument("--out", default="data2/submission.csv")
    parser.add_argument("--cv", action="store_true", help="Run 5-fold CV before predict")
    args = parser.parse_args()

    train = pd.read_csv(args.train)
    test = pd.read_csv(args.test)

    X = make_features(train).values
    y = train["is_cancelled"].values
    X_test = make_features(test).values

    if args.cv:
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        oof_preds = []
        for name, model in build_models().items():
            oof = cross_val_predict(model, X, y, cv=cv, method="predict_proba", n_jobs=1)[:, 1]
            auc = roc_auc_score(y, oof)
            print(f"{name}: OOF ROC-AUC = {auc:.5f}")
            oof_preds.append(oof)
        blend = np.mean(oof_preds, axis=0)
        blend_auc = roc_auc_score(y, blend)
        print(f"Ensemble (mean): OOF ROC-AUC = {blend_auc:.5f}")
        print(f"Estimated points: {max(0.0, blend_auc - 0.55) / 0.45:.4f}")

    test_preds = []
    for model in build_models().values():
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
