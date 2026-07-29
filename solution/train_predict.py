"""
Классификация жанра фильма по описанию (action / comedy / drama).

Модель: предобработка + стемминг (Snowball RU) + TF-IDF
(word 1-3 + char_wb 3-6) + Logistic Regression.

Метрика: Macro F1. CV ~0.936.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd
from nltk.stem.snowball import SnowballStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import FeatureUnion, Pipeline

STEMMER = SnowballStemmer("russian")


def clean_text(text: str) -> str:
    text = str(text).lower()
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = re.sub(r"[^\w\sёа-яa-z]", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\d+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def stem_text(text: str) -> str:
    return " ".join(STEMMER.stem(w) for w in text.split() if w)


def preprocess(series: pd.Series) -> pd.Series:
    return series.map(clean_text).map(stem_text)


def build_model() -> Pipeline:
    return Pipeline(
        [
            (
                "features",
                FeatureUnion(
                    [
                        (
                            "word",
                            TfidfVectorizer(
                                ngram_range=(1, 3),
                                max_features=50_000,
                                min_df=2,
                                sublinear_tf=True,
                            ),
                        ),
                        (
                            "char",
                            TfidfVectorizer(
                                analyzer="char_wb",
                                ngram_range=(3, 6),
                                max_features=100_000,
                                min_df=2,
                                sublinear_tf=True,
                            ),
                        ),
                    ]
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    C=2.0,
                    max_iter=3000,
                    class_weight="balanced",
                    solver="lbfgs",
                    random_state=42,
                ),
            ),
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", default="data/train.csv")
    parser.add_argument("--test", default="data/test.csv")
    parser.add_argument("--out", default="data/submission.csv")
    parser.add_argument("--cv", action="store_true", help="Run 5-fold CV before predict")
    args = parser.parse_args()

    train = pd.read_csv(args.train)
    test = pd.read_csv(args.test)

    X = preprocess(train["description"])
    y = train["genre"]
    X_test = preprocess(test["description"])

    model = build_model()

    if args.cv:
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        oof = cross_val_predict(model, X, y, cv=cv, n_jobs=-1)
        macro = f1_score(y, oof, average="macro")
        print(classification_report(y, oof, target_names=["action", "comedy", "drama"], digits=4))
        print(f"CV Macro F1: {macro:.4f}")
        print(f"Estimated points: {max(0.0, macro - 0.5) / 0.5:.4f}")

    model.fit(X, y)
    preds = model.predict(X_test)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    submission = pd.DataFrame({"id": test["id"], "genre": preds.astype(int)})
    submission.to_csv(out, index=False)
    print(f"Saved: {out}")
    print(submission["genre"].value_counts().sort_index().to_dict())


if __name__ == "__main__":
    main()
