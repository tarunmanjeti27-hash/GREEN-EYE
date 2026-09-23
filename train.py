"""
GREEN-EYE Model Trainer
Fine-tunes MobileNetV3-Small on the 2,521 Sugarcane Leaf Disease images across 5 classes:
Healthy, Mosaic, RedRot, Rust, Yellow.
"""

import os
import sys
import time
from pathlib import Path
from typing import Tuple, List

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset, random_split
from torchvision import transforms
from PIL import Image

from backend.config import BASE_DIR, CLASSES, MODELS_DIR, MODEL_WEIGHTS_PATH
from backend.model import GreenEyeClassifier


class SugarcaneDataset(Dataset):
    """Custom dataset loader for the 5 sugarcane leaf disease directories."""
    def __init__(self, root_dir: Path, transform=None):
        self.root_dir = root_dir
        self.transform = transform
        self.samples: List[Tuple[Path, int]] = []
        valid_exts = {".jpeg", ".jpg", ".png", ".webp"}
        
        for class_idx, class_name in enumerate(CLASSES):
            class_folder = root_dir / class_name
            if not class_folder.exists():
                continue
            for img_path in class_folder.iterdir():
                if img_path.is_file() and img_path.suffix.lower() in valid_exts:
                    self.samples.append((img_path, class_idx))

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        img_path, label = self.samples[idx]
        image = Image.open(img_path).convert("RGB")
        if self.transform:
            image = self.transform(image)
        return image, label


def train_model(epochs: int = 5, batch_size: int = 16, lr: float = 0.001):
    print("=" * 65)
    print("🌾 GREEN-EYE Vision Suite — Model Training Pipeline")
    print(f"Target Classes: {CLASSES}")
    print("=" * 65)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    # Data augmentations
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(degrees=15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    full_dataset = SugarcaneDataset(BASE_DIR, transform=train_transform)
    total_samples = len(full_dataset)
    print(f"Total dataset samples detected: {total_samples}")

    if total_samples == 0:
        print("Error: No images found in dataset folders!")
        return

    val_size = int(0.2 * total_samples)
    train_size = total_samples - val_size
    train_set, val_set = random_split(full_dataset, [train_size, val_size])

    train_loader = DataLoader(train_set, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_set, batch_size=batch_size, shuffle=False, num_workers=0)

    print(f"Training set: {train_size} | Validation set: {val_size}")

    # Initialize model
    model = GreenEyeClassifier(num_classes=len(CLASSES), pretrained=False)
    model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    best_val_acc = 0.0

    for epoch in range(1, epochs + 1):
        t0 = time.time()
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
            correct_train += torch.sum(preds == labels.data).item()
            total_train += labels.size(0)

        scheduler.step()
        epoch_loss = running_loss / total_train
        epoch_acc = (correct_train / total_train) * 100.0

        # Validation
        model.eval()
        val_correct = 0
        val_total = 0
        with torch.no_grad():
            for images, labels in val_loader:
                images = images.to(device)
                labels = labels.to(device)
                outputs = model(images)
                _, preds = torch.max(outputs, 1)
                val_correct += torch.sum(preds == labels.data).item()
                val_total += labels.size(0)

        val_acc = (val_correct / val_total) * 100.0 if val_total > 0 else 0.0
        elapsed = time.time() - t0

        print(f"Epoch [{epoch:02d}/{epochs:02d}] ({elapsed:.1f}s) - "
              f"Train Loss: {epoch_loss:.4f} | Train Acc: {epoch_acc:.1f}% | "
              f"Val Acc: {val_acc:.1f}%")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            MODELS_DIR.mkdir(exist_ok=True)
            torch.save(model.state_dict(), MODEL_WEIGHTS_PATH)
            print(f"  ★ New best model checkpoint saved to: {MODEL_WEIGHTS_PATH} ({val_acc:.1f}%)")

    print("\n" + "=" * 65)
    print(f"✓ Training Complete! Peak Validation Accuracy: {best_val_acc:.1f}%")
    print(f"✓ Checkpoint ready at: {MODEL_WEIGHTS_PATH}")
    print("=" * 65)


if __name__ == "__main__":
    epochs = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    train_model(epochs=epochs)
