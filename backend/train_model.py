"""
GREEN-EYE Model Training Pipeline
===================================
Fine-tunes MobileNetV3-Small (ImageNet pretrained) on the Sugarcane Leaf Disease
Dataset with 5 classes: Healthy, Mosaic, RedRot, Rust, Yellow.

Usage:
    python -m backend.train_model [--epochs 10] [--batch-size 16] [--lr 0.001]

Outputs:
    models/green_eye_model.pth      — Best checkpoint (state_dict)
    models/training_results.json    — Accuracy report with per-class metrics
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Tuple, Dict

import numpy as np
from PIL import Image

# ── PyTorch imports ───────────────────────────────────────────────────────────
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset, random_split
from torchvision import transforms

# ── Project imports ───────────────────────────────────────────────────────────
from backend.config import BASE_DIR, CLASSES, MODELS_DIR, MODEL_WEIGHTS_PATH
from backend.model import GreenEyeClassifier


# ═════════════════════════════════════════════════════════════════════════════
# Dataset
# ═════════════════════════════════════════════════════════════════════════════
class SugarcaneDataset(Dataset):
    """Custom dataset loader for 5 sugarcane leaf disease class folders."""

    VALID_EXTS = {".jpeg", ".jpg", ".png", ".webp"}

    def __init__(self, root_dir: Path, transform=None):
        self.root_dir = root_dir
        self.transform = transform
        self.samples: List[Tuple[Path, int]] = []

        for class_idx, class_name in enumerate(CLASSES):
            class_folder = root_dir / class_name
            if not class_folder.exists():
                print(f"  [!] Class folder not found: {class_folder}")
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


# ═════════════════════════════════════════════════════════════════════════════
# Training Loop
# ═════════════════════════════════════════════════════════════════════════════
def train_model(epochs: int = 10, batch_size: int = 16, lr: float = 0.001):
    """Train MobileNetV3-Small with transfer learning on the sugarcane dataset."""

    print("=" * 70)
    print("  GREEN-EYE Vision Suite - Model Training Pipeline")
    print("=" * 70)
    print(f"  Classes       : {CLASSES}")
    print(f"  Epochs        : {epochs}")
    print(f"  Batch Size    : {batch_size}")
    print(f"  Learning Rate : {lr}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"  Device        : {device}")
    print(f"  Dataset Root  : {BASE_DIR}")
    print("=" * 70)

    # ── Data Augmentation ─────────────────────────────────────────────────
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.1),
        transforms.RandomRotation(degrees=15),
        transforms.ColorJitter(brightness=0.25, contrast=0.25, saturation=0.2, hue=0.05),
        transforms.RandomAffine(degrees=0, translate=(0.05, 0.05)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    # ── Load Dataset ──────────────────────────────────────────────────────
    full_dataset = SugarcaneDataset(BASE_DIR, transform=None)  # transform applied later
    total_samples = len(full_dataset)
    print(f"\n  Total images found: {total_samples}")

    if total_samples == 0:
        print("  [X] ERROR: No images found in dataset folders!")
        return

    # Print per-class breakdown
    class_counts = [0] * len(CLASSES)
    for _, label in full_dataset.samples:
        class_counts[label] += 1
    for cls_name, count in zip(CLASSES, class_counts):
        print(f"    {cls_name:12s}: {count:4d} images")

    # ── Train/Val Split ───────────────────────────────────────────────────
    val_size = int(0.2 * total_samples)
    train_size = total_samples - val_size

    generator = torch.Generator().manual_seed(42)
    train_indices, val_indices = random_split(
        range(total_samples), [train_size, val_size], generator=generator
    )

    # Create separate datasets with appropriate transforms
    train_dataset = SugarcaneDataset(BASE_DIR, transform=train_transform)
    val_dataset = SugarcaneDataset(BASE_DIR, transform=val_transform)

    train_subset = torch.utils.data.Subset(train_dataset, train_indices.indices)
    val_subset = torch.utils.data.Subset(val_dataset, val_indices.indices)

    train_loader = DataLoader(train_subset, batch_size=batch_size, shuffle=True, num_workers=0, pin_memory=True)
    val_loader = DataLoader(val_subset, batch_size=batch_size, shuffle=False, num_workers=0, pin_memory=True)

    print(f"\n  Training set  : {train_size} images")
    print(f"  Validation set: {val_size} images")

    # ── Model ─────────────────────────────────────────────────────────────
    print("\n  Initializing MobileNetV3-Small with ImageNet pretrained weights...")
    model = GreenEyeClassifier(num_classes=len(CLASSES), pretrained=True)
    model.to(device)
    print(f"  [OK] Model loaded on {device}")

    # ── Optimizer & Scheduler ─────────────────────────────────────────────
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    # ── Training History ──────────────────────────────────────────────────
    history = {
        "train_loss": [],
        "train_acc": [],
        "val_acc": [],
        "epoch_time_sec": [],
    }
    best_val_acc = 0.0
    best_epoch = 0

    print("\n" + "─" * 70)
    print(f"  {'Epoch':>6s}  {'Time':>7s}  {'Train Loss':>11s}  {'Train Acc':>10s}  {'Val Acc':>10s}")
    print("─" * 70)

    for epoch in range(1, epochs + 1):
        t0 = time.time()

        # ── Train Phase ───────────────────────────────────────────────────
        model.train()
        running_loss = 0.0
        correct_train = 0
        total_train = 0

        for images, labels in train_loader:
            images = images.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * images.size(0)
            _, preds = torch.max(outputs, 1)
            correct_train += (preds == labels).sum().item()
            total_train += labels.size(0)

        scheduler.step()

        epoch_loss = running_loss / total_train
        epoch_acc = (correct_train / total_train) * 100.0

        # ── Validation Phase ──────────────────────────────────────────────
        model.eval()
        val_correct = 0
        val_total = 0
        with torch.no_grad():
            for images, labels in val_loader:
                images = images.to(device)
                labels = labels.to(device)
                outputs = model(images)
                _, preds = torch.max(outputs, 1)
                val_correct += (preds == labels).sum().item()
                val_total += labels.size(0)

        val_acc = (val_correct / val_total) * 100.0 if val_total > 0 else 0.0
        elapsed = time.time() - t0

        # Log
        history["train_loss"].append(round(epoch_loss, 4))
        history["train_acc"].append(round(epoch_acc, 2))
        history["val_acc"].append(round(val_acc, 2))
        history["epoch_time_sec"].append(round(elapsed, 1))

        marker = " *BEST*" if val_acc > best_val_acc else ""
        print(f"  {epoch:3d}/{epochs:<3d}  {elapsed:6.1f}s  {epoch_loss:11.4f}  {epoch_acc:9.1f}%  {val_acc:9.1f}%{marker}")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_epoch = epoch
            MODELS_DIR.mkdir(exist_ok=True)
            torch.save(model.state_dict(), MODEL_WEIGHTS_PATH)

    print("─" * 70)

    # ═════════════════════════════════════════════════════════════════════
    # Final Evaluation — Per-Class Accuracy
    # ═════════════════════════════════════════════════════════════════════
    print("\n  Loading best checkpoint for final evaluation...")
    model.load_state_dict(torch.load(MODEL_WEIGHTS_PATH, map_location=device))
    model.eval()

    # Compute per-class metrics on the full validation set
    all_preds = []
    all_labels = []
    with torch.no_grad():
        for images, labels in val_loader:
            images = images.to(device)
            labels = labels.to(device)
            outputs = model(images)
            _, preds = torch.max(outputs, 1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    all_preds = np.array(all_preds)
    all_labels = np.array(all_labels)

    overall_acc = (all_preds == all_labels).sum() / len(all_labels) * 100.0

    per_class_metrics: Dict[str, Dict] = {}
    for idx, cls_name in enumerate(CLASSES):
        cls_mask = all_labels == idx
        cls_pred_mask = all_preds == idx

        tp = int(((all_preds == idx) & (all_labels == idx)).sum())
        fp = int(((all_preds == idx) & (all_labels != idx)).sum())
        fn = int(((all_preds != idx) & (all_labels == idx)).sum())
        support = int(cls_mask.sum())

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        accuracy = tp / support * 100.0 if support > 0 else 0.0

        per_class_metrics[cls_name] = {
            "accuracy": round(accuracy, 2),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "support": support,
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
        }

    # ── Confusion Matrix ──────────────────────────────────────────────────
    num_classes = len(CLASSES)
    confusion = np.zeros((num_classes, num_classes), dtype=int)
    for true_label, pred_label in zip(all_labels, all_preds):
        confusion[true_label][pred_label] += 1

    # ── Print Results ─────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  FINAL MODEL ACCURACY REPORT")
    print("=" * 70)
    print(f"\n  Overall Validation Accuracy: {overall_acc:.2f}%")
    print(f"  Best Epoch: {best_epoch}/{epochs}")
    print(f"  Checkpoint: {MODEL_WEIGHTS_PATH}\n")

    print(f"  {'Class':>12s}  {'Accuracy':>9s}  {'Precision':>10s}  {'Recall':>8s}  {'F1-Score':>9s}  {'Support':>8s}")
    print("  " + "─" * 62)
    for cls_name, m in per_class_metrics.items():
        print(
            f"  {cls_name:>12s}  {m['accuracy']:8.1f}%  {m['precision']:10.4f}  "
            f"{m['recall']:8.4f}  {m['f1_score']:9.4f}  {m['support']:8d}"
        )

    # ── Confusion Matrix Display ──────────────────────────────────────────
    print(f"\n  Confusion Matrix:")
    header = "  " + " " * 12 + "".join(f"{c[:7]:>8s}" for c in CLASSES)
    print(header)
    for i, cls_name in enumerate(CLASSES):
        row = "".join(f"{confusion[i][j]:8d}" for j in range(num_classes))
        print(f"  {cls_name:>12s}{row}")

    # ── Save Results JSON ─────────────────────────────────────────────────
    results = {
        "model": "MobileNetV3-Small (ImageNet Transfer Learning)",
        "total_images": total_samples,
        "train_size": train_size,
        "val_size": val_size,
        "epochs_trained": epochs,
        "best_epoch": best_epoch,
        "overall_accuracy": round(overall_acc, 2),
        "per_class_metrics": per_class_metrics,
        "confusion_matrix": {
            "labels": CLASSES,
            "matrix": confusion.tolist(),
        },
        "training_history": history,
        "device": str(device),
        "checkpoint_path": str(MODEL_WEIGHTS_PATH),
    }

    results_path = MODELS_DIR / "training_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  [OK] Training results saved to: {results_path}")

    print("\n" + "=" * 70)
    print(f"  [OK] Training Complete! Overall Accuracy: {overall_acc:.2f}%")
    print("=" * 70 + "\n")

    return results


# ═════════════════════════════════════════════════════════════════════════════
# CLI Entry Point
# ═════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GREEN-EYE Model Trainer")
    parser.add_argument("--epochs", type=int, default=10, help="Number of training epochs (default: 10)")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size (default: 16)")
    parser.add_argument("--lr", type=float, default=0.001, help="Learning rate (default: 0.001)")
    args = parser.parse_args()

    train_model(epochs=args.epochs, batch_size=args.batch_size, lr=args.lr)
