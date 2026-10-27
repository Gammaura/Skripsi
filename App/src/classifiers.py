"""
Definisi kandidat model klasifikasi struktur dokumen (dipakai train.py & Active Learning).
"""

from typing import Dict

import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
from sklearn.utils.class_weight import compute_sample_weight

MODEL_LOGREG = "Logistic Regression (Balanced)"
MODEL_RF = "Random Forest (Balanced)"
MODEL_XGB = "XGBoost (Balanced)"


class BalancedXGBClassifier(ClassifierMixin, BaseEstimator):
    """XGBoost dengan label string & bobot kelas seimbang.

    XGBoost hanya menerima label 0..K-1 dan tidak punya class_weight, sehingga
    pembungkus ini meng-encode label dan memberi sample_weight 'balanced' agar
    setara dengan class_weight='balanced' pada model scikit-learn lain.
    """

    def __init__(self, n_estimators: int = 300, max_depth: int = 6, learning_rate: float = 0.1,
                 subsample: float = 0.9, colsample_bytree: float = 0.8, random_state: int = 42):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.subsample = subsample
        self.colsample_bytree = colsample_bytree
        self.random_state = random_state

    def fit(self, X, y):
        from xgboost import XGBClassifier  # impor lokal: xgboost hanya wajib bila model ini dipakai

        self.encoder_ = LabelEncoder().fit(y)
        self.classes_ = self.encoder_.classes_
        self.booster_ = XGBClassifier(
            n_estimators=self.n_estimators, max_depth=self.max_depth, learning_rate=self.learning_rate,
            subsample=self.subsample, colsample_bytree=self.colsample_bytree, random_state=self.random_state,
            tree_method="hist", eval_metric="mlogloss", n_jobs=-1,
        )
        self.booster_.fit(X, self.encoder_.transform(y), sample_weight=compute_sample_weight("balanced", y))
        return self

    def predict_proba(self, X) -> np.ndarray:
        return self.booster_.predict_proba(X)

    def predict(self, X) -> np.ndarray:
        return self.classes_[np.argmax(self.predict_proba(X), axis=1)]


def candidate_models(seed: int = 42) -> Dict[str, BaseEstimator]:
    """Tiga model pembanding dengan penanganan ketimpangan kelas yang setara."""
    return {
        MODEL_LOGREG: LogisticRegression(max_iter=1000, random_state=seed, C=1.0, class_weight="balanced"),
        MODEL_RF: RandomForestClassifier(n_estimators=100, random_state=seed, max_depth=14, class_weight="balanced"),
        MODEL_XGB: BalancedXGBClassifier(random_state=seed),
    }
