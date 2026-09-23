"""
GREEN-EYE Multi-Algorithm Model Comparison
============================================
Extracts deep features using a pretrained MobileNetV2 backbone, then trains
and compares 9 classical ML classifiers (SVM, Random Forest, KNN, Decision Tree,
Logistic Regression, Naive Bayes, AdaBoost, Gradient Boosting, XGBoost).

Based on Kaggle notebook: tarunmanjeti/notebook25f3ea3356

Usage:
    python -m backend.train_ml_models

Outputs:
    models/ml_comparison_results.json   -- Accuracy & F1 for all 9 models
    models/best_ml_model.pkl            -- Pickled best sklearn model
    models/training_results.json        -- Updated with ML comparison data
"""

import json
import os
import sys
import time
import pickle
from pathlib import Path
from typing import List, Tuple, Dict, Any

import numpy as np
from PIL import Image

# -- PyTorch for feature extraction --
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms

# -- Scikit-learn classifiers --
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.ensemble import (
    RandomForestClassifier,
    AdaBoostClassifier,
    GradientBoostingClassifier,
)
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import accuracy_score, f1_score, classification_report
from sklearn.model_selection import train_test_split

# -- XGBoost (optional — large package, may fail to install) --
XGBOOST_AVAILABLE = False
try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    print("  [INFO] XGBoost not installed. Skipping XGBoost classifier.")
    print("         Install with: uv pip install xgboost")

# -- Pandas for tabular display --
import pandas as pd

# -- Project imports --
from backend.config import BASE_DIR, CLASSES, MODELS_DIR


# =========================================================================
# Dataset
# =========================================================================
class SugarcaneFeatureDataset(Dataset):
    """Loads images for feature extraction."""

    VALID_EXTS = {".jpeg", ".jpg", ".png", ".webp"}

    def __init__(self, root_dir: Path, transform=None):
        self.transform = transform
        self.samples: List[Tuple[Path, int]] = []

        for class_idx, class_name in enumerate(CLASSES):
            class_folder = root_dir / class_name
            if not class_folder.exists():
                continue
            for img_path in sorted(class_folder.iterdir()):
                if img_path.is_file() and img_path.suffix.lower() in self.VALID_EXTS:
                    self.samples.append((img_path, class_idx))

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        img_path, label = self.samples[idx]
        image = Image.open(img_path).convert("RGB")
        if self.transform:
            image = self.transform(image)
        return image, label


# =========================================================================
# Feature Extraction with Pretrained MobileNetV2
# =========================================================================
def build_feature_extractor(device: torch.device):
    """Load MobileNetV2 pretrained on ImageNet as a feature extractor.
    
    Removes the classification head and uses global average pooling,
    producing a 1280-dimensional feature vector per image.
    """
    print("  Loading MobileNetV2 (ImageNet pretrained) as feature extractor...")
    backbone = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.IMAGENET1K_V1)
    # Remove classifier, keep features + adaptive avg pool
    feature_extractor = nn.Sequential(
        backbone.features,
        nn.AdaptiveAvgPool2d((1, 1)),
        nn.Flatten(),
    )
    feature_extractor.to(device)
    feature_extractor.eval()
    print(f"  [OK] Feature extractor ready (output: 1280-dim vectors)")
    return feature_extractor


def extract_features(
    feature_extractor: nn.Module,
    dataset: Dataset,
    indices: List[int],
    device: torch.device,
    batch_size: int = 32,
    desc: str = "data",
) -> Tuple[np.ndarray, np.ndarray]:
    """Extract feature vectors for a subset of the dataset."""
    subset = torch.utils.data.Subset(dataset, indices)
    loader = DataLoader(subset, batch_size=batch_size, shuffle=False, num_workers=0)

    all_features = []
    all_labels = []

    with torch.no_grad():
        for batch_idx, (images, labels) in enumerate(loader):
            images = images.to(device)
            features = feature_extractor(images)
            all_features.append(features.cpu().numpy())
            all_labels.append(labels.numpy())

            # Progress indicator
            done = min((batch_idx + 1) * batch_size, len(subset))
            print(f"\r    Extracting {desc}: {done}/{len(subset)}", end="", flush=True)

    print()  # newline after progress
    X = np.concatenate(all_features, axis=0)
    y = np.concatenate(all_labels, axis=0)
    return X, y


# =========================================================================
# Multi-Algorithm Training & Comparison
# =========================================================================
def train_and_compare(
    Xtr: np.ndarray,
    ytr: np.ndarray,
    Xte: np.ndarray,
    yte: np.ndarray,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Train 9 ML classifiers and compare accuracy & F1 scores."""

    model_configs = {
        "SVM": make_pipeline(StandardScaler(), SVC()),
        "Random Forest": RandomForestClassifier(n_estimators=200, random_state=42),
        "KNN": make_pipeline(StandardScaler(), KNeighborsClassifier()),
        "Decision Tree": DecisionTreeClassifier(random_state=42),
        "Logistic Regression": make_pipeline(
            StandardScaler(), LogisticRegression(max_iter=2000)
        ),
        "Naive Bayes": GaussianNB(),
        "AdaBoost": AdaBoostClassifier(random_state=42),
        "Gradient Boosting": GradientBoostingClassifier(random_state=42),
    }

    if XGBOOST_AVAILABLE:
        model_configs["XGBoost"] = XGBClassifier(eval_metric="mlogloss", random_state=42)

    rows = []
    trained_models = {}

    print("\n  Training 9 ML classifiers on extracted features...")
    print("  " + "-" * 66)
    print(f"  {'Model':<22s}  {'Accuracy':>9s}  {'Macro F1':>9s}  {'Time (s)':>9s}")
    print("  " + "-" * 66)

    for name, model in model_configs.items():
        t0 = time.time()
        model.fit(Xtr, ytr)
        preds = model.predict(Xte)
        elapsed = time.time() - t0

        acc = accuracy_score(yte, preds)
        f1 = f1_score(yte, preds, average="macro")

        rows.append([name, acc, f1, elapsed])
        trained_models[name] = model

        print(f"  {name:<22s}  {acc:9.4f}  {f1:9.4f}  {elapsed:9.2f}")

    print("  " + "-" * 66)

    results_df = pd.DataFrame(
        rows, columns=["Model", "Accuracy", "Macro F1", "Time (s)"]
    )
    results_df = results_df.sort_values("Accuracy", ascending=False).reset_index(
        drop=True
    )

    return results_df, trained_models


# =========================================================================
# Main Pipeline
# =========================================================================
def run_ml_comparison():
    """Full pipeline: split data -> extract features -> train & compare models."""

    print("=" * 70)
    print("  GREEN-EYE Multi-Algorithm Model Comparison")
    print("  (MobileNetV2 Feature Extraction + 9 ML Classifiers)")
    print("=" * 70)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"  Device: {device}")
    print(f"  Dataset: {BASE_DIR}")
    print(f"  Classes: {CLASSES}")

    # -- Image transforms (same as MobileNetV2 expects) --
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    # -- Load full dataset --
    full_dataset = SugarcaneFeatureDataset(BASE_DIR, transform=transform)
    total = len(full_dataset)
    print(f"\n  Total images: {total}")

    if total == 0:
        print("  [X] ERROR: No images found!")
        return

    # Per-class counts
    labels_all = [label for _, label in full_dataset.samples]
    for idx, cls_name in enumerate(CLASSES):
        count = labels_all.count(idx)
        print(f"    {cls_name:12s}: {count:4d} images")

    # -- Train / Val / Test Split (60/20/20) --
    all_indices = list(range(total))
    labels_arr = np.array(labels_all)

    train_idx, temp_idx = train_test_split(
        all_indices, test_size=0.4, random_state=42, stratify=labels_arr
    )
    temp_labels = labels_arr[temp_idx]
    val_idx, test_idx = train_test_split(
        temp_idx, test_size=0.5, random_state=42, stratify=temp_labels
    )

    print(f"\n  Split: Train={len(train_idx)} | Val={len(val_idx)} | Test={len(test_idx)}")

    # -- Extract Features --
    feature_extractor = build_feature_extractor(device)

    print("\n  Extracting deep features (MobileNetV2 -> 1280-dim)...")
    Xtr, ytr = extract_features(feature_extractor, full_dataset, train_idx, device, desc="train")
    Xva, yva = extract_features(feature_extractor, full_dataset, val_idx, device, desc="val  ")
    Xte, yte = extract_features(feature_extractor, full_dataset, test_idx, device, desc="test ")

    print(f"\n  Feature shapes: Train={Xtr.shape}, Val={Xva.shape}, Test={Xte.shape}")

    # Combine train + val for final training (test kept separate for evaluation)
    Xtr_full = np.concatenate([Xtr, Xva], axis=0)
    ytr_full = np.concatenate([ytr, yva], axis=0)
    print(f"  Combined train+val for fitting: {Xtr_full.shape}")

    # -- Train & Compare --
    results_df, trained_models = train_and_compare(Xtr_full, ytr_full, Xte, yte)

    # -- Display Final Results --
    print("\n" + "=" * 70)
    print("  FINAL MODEL ACCURACY COMPARISON")
    print("=" * 70)
    print()
    print(results_df.round(4).to_string(index=False))

    # -- Best Model Details --
    best_name = results_df.iloc[0]["Model"]
    best_acc = results_df.iloc[0]["Accuracy"]
    best_f1 = results_df.iloc[0]["Macro F1"]
    best_model = trained_models[best_name]

    print(f"\n  >> Best Model: {best_name}")
    print(f"  >> Accuracy:   {best_acc:.4f} ({best_acc*100:.2f}%)")
    print(f"  >> Macro F1:   {best_f1:.4f}")

    # Per-class classification report for the best model
    best_preds = best_model.predict(Xte)
    print(f"\n  Per-Class Report ({best_name}):")
    print("  " + "-" * 60)
    report = classification_report(yte, best_preds, target_names=CLASSES, digits=4)
    for line in report.split("\n"):
        print(f"  {line}")

    # -- Save Best Model --
    MODELS_DIR.mkdir(exist_ok=True)
    best_model_path = MODELS_DIR / "best_ml_model.pkl"
    with open(best_model_path, "wb") as f:
        pickle.dump(best_model, f)
    print(f"\n  [OK] Best model saved: {best_model_path}")

    # -- Save Results JSON --
    results_dict = {
        "pipeline": "MobileNetV2 Feature Extraction + ML Classifiers",
        "feature_extractor": "MobileNetV2 (ImageNet, 1280-dim)",
        "total_images": total,
        "split": {
            "train": len(train_idx),
            "val": len(val_idx),
            "test": len(test_idx),
        },
        "model_comparison": [],
        "best_model": {
            "name": best_name,
            "accuracy": round(float(best_acc), 4),
            "accuracy_pct": round(float(best_acc * 100), 2),
            "macro_f1": round(float(best_f1), 4),
        },
        "per_class_report": {},
        "classes": CLASSES,
        "device": str(device),
    }

    # All model results
    for _, row in results_df.iterrows():
        results_dict["model_comparison"].append({
            "model": row["Model"],
            "accuracy": round(float(row["Accuracy"]), 4),
            "accuracy_pct": round(float(row["Accuracy"] * 100), 2),
            "macro_f1": round(float(row["Macro F1"]), 4),
            "time_seconds": round(float(row["Time (s)"]), 3),
        })

    # Per-class metrics for best model
    from sklearn.metrics import precision_recall_fscore_support
    prec, rec, f1s, sup = precision_recall_fscore_support(yte, best_preds, labels=range(len(CLASSES)))
    for idx, cls_name in enumerate(CLASSES):
        results_dict["per_class_report"][cls_name] = {
            "precision": round(float(prec[idx]), 4),
            "recall": round(float(rec[idx]), 4),
            "f1_score": round(float(f1s[idx]), 4),
            "support": int(sup[idx]),
        }

    results_path = MODELS_DIR / "ml_comparison_results.json"
    with open(results_path, "w") as f:
        json.dump(results_dict, f, indent=2)
    print(f"  [OK] Comparison results saved: {results_path}")

    # Also update training_results.json if it exists
    training_results_path = MODELS_DIR / "training_results.json"
    try:
        if training_results_path.exists():
            with open(training_results_path, "r") as f:
                existing = json.load(f)
            existing["ml_comparison"] = results_dict
            with open(training_results_path, "w") as f:
                json.dump(existing, f, indent=2)
            print(f"  [OK] Updated training_results.json with ML comparison data")
    except Exception:
        pass

    print("\n" + "=" * 70)
    print(f"  [OK] Complete! Best: {best_name} = {best_acc*100:.2f}% accuracy")
    print("=" * 70 + "\n")

    return results_dict


# =========================================================================
# CLI Entry Point
# =========================================================================
if __name__ == "__main__":
    run_ml_comparison()
