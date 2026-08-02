"""Train and persist category recommendation model."""

import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier

from src.phase1.features import FEATURE_NAMES, FeatureBuilder
from src.phase1.purchase_history.analyzer import (
    CATEGORY_AFFINITY,
    PurchaseHistoryAnalyzer,
)
from src.shared.models.domain import Category, PurchaseHistory, PurchaseRecord

MODEL_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "models"


class CategoryModelTrainer:
    """Phase 1: Train ML model on synthetic + historical purchase data."""

    CATEGORIES = list(Category)

    def __init__(self) -> None:
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        self.model_path = MODEL_DIR / "category_classifier.joblib"
        self.meta_path = MODEL_DIR / "category_classifier.meta.json"
        self._model: GradientBoostingClassifier | None = None
        self._label_to_idx: dict[str, int] = {}
        self._idx_to_label: dict[int, str] = {}
        self._feature_builder = FeatureBuilder(PurchaseHistoryAnalyzer())
        self._load_if_exists()

    def _load_if_exists(self) -> None:
        if self.model_path.exists() and self.meta_path.exists():
            self._model = joblib.load(self.model_path)
            meta = json.loads(self.meta_path.read_text(encoding="utf-8"))
            self._label_to_idx = meta["label_to_idx"]
            self._idx_to_label = {int(k): v for k, v in meta["idx_to_label"].items()}

    def _synthetic_training_data(self) -> tuple[np.ndarray, list[str]]:
        """Generate training pairs from category affinity patterns."""
        X: list[np.ndarray] = []
        y: list[str] = []
        patterns = [
            ([1, 1, 0.3, 1, 1], Category.HEALTH_WELLNESS.value),
            ([2, 1, 0.2, 1, 1], Category.PET_SUPPLIES.value),
            ([1, 0, 0.4, 1, 1], Category.HOUSEHOLD.value),
            ([0, 1, 0.5, 1, 1], Category.PERSONAL_CARE.value),
            ([2, 0, 0.3, 1, 1], Category.SNACKS.value),
            ([1, 1, 0.25, 1, 1], Category.HEALTH_WELLNESS.value),
            ([0, 0, 0.2, 1, 1], Category.FROZEN.value),
        ]
        rng = np.random.default_rng(42)
        for features, label in patterns:
            for _ in range(25):
                noise = rng.normal(0, 0.05, len(features))
                X.append(np.array(features, dtype=float) + noise)
                y.append(label)
        return np.array(X), y

    def _records_to_training_data(
        self, records: list[PurchaseRecord]
    ) -> tuple[np.ndarray, list[str]]:
        """Derive labeled examples from real purchase histories."""
        X: list[np.ndarray] = []
        y: list[str] = []
        by_user: dict[str, list[PurchaseRecord]] = {}
        for record in records:
            by_user.setdefault(record.user_id, []).append(record)

        for user_id, user_records in by_user.items():
            history = PurchaseHistory(user_id=user_id, records=user_records)
            missing = self._feature_builder.analyzer.get_missing_categories(history)
            for candidate in missing:
                features = self._feature_builder.build(history, candidate)
                X.append(features)
                y.append(candidate.value)

            for purchased_cat, related in CATEGORY_AFFINITY.items():
                if purchased_cat not in history.categories_purchased:
                    continue
                for target in related:
                    if target in history.categories_purchased:
                        continue
                    features = self._feature_builder.build(history, target)
                    X.append(features)
                    y.append(target.value)

        if not X:
            return np.empty((0, len(FEATURE_NAMES))), []
        return np.array(X), y

    def train(self, records: list[PurchaseRecord] | None = None) -> dict:
        X_syn, y_syn = self._synthetic_training_data()
        X_parts, y_parts = [X_syn], [y_syn]

        if records:
            X_rec, y_rec = self._records_to_training_data(records)
            if len(X_rec):
                X_parts.append(X_rec)
                y_parts.append(y_rec)

        X = np.vstack(X_parts)
        y_labels = [label for part in y_parts for label in part]

        unique_labels = sorted(set(y_labels))
        self._label_to_idx = {label: i for i, label in enumerate(unique_labels)}
        self._idx_to_label = {i: label for label, i in self._label_to_idx.items()}
        y = np.array([self._label_to_idx[label] for label in y_labels])

        self._model = GradientBoostingClassifier(
            n_estimators=50, max_depth=3, random_state=42
        )
        self._model.fit(X, y)

        joblib.dump(self._model, self.model_path)
        metadata = {
            "labels": unique_labels,
            "label_to_idx": self._label_to_idx,
            "idx_to_label": self._idx_to_label,
            "n_samples": len(X),
            "n_real_records": len(records or []),
            "feature_names": FEATURE_NAMES,
        }
        self.meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        return metadata

    def predict_proba(self, features: np.ndarray) -> dict[str, float]:
        if self._model is None:
            self.train()
        assert self._model is not None

        probs = self._model.predict_proba(features.reshape(1, -1))[0]
        return {
            self._idx_to_label[i]: float(prob)
            for i, prob in enumerate(probs)
        }

    def category_probability(
        self, features: np.ndarray, category: Category
    ) -> float:
        probs = self.predict_proba(features)
        return probs.get(category.value, 0.0)

    @property
    def is_trained(self) -> bool:
        return self._model is not None

    def model_info(self) -> dict:
        if not self.meta_path.exists():
            return {"trained": False, "path": str(self.model_path)}
        meta = json.loads(self.meta_path.read_text(encoding="utf-8"))
        return {
            "trained": self.is_trained,
            "path": str(self.model_path),
            **meta,
        }
