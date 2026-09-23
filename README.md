# 🌾 GREEN-EYE: Precision Sugarcane Leaf Pathology & Vision Suite

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688.svg)](https://fastapi.tiangolo.com/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.x-EE4C2C.svg)](https://pytorch.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**GREEN-EYE** is an AI-powered foliar agronomy and computer vision platform engineered for real-time diagnostic pathology of sugarcane crops. It benchmarks on **2,521 high-resolution sugarcane leaf images** across 5 distinct clinical categories, providing spectral lesion analysis, instant classification, and agronomic chemical/biological remedy prescriptions.

---

## 🔬 Detected Disease Categories

| Category | Pathogen / Scientific Classification | Severity Index |
| :--- | :--- | :--- |
| **Healthy** | *Saccharum officinarum L.* (Normal Vigorous Tissue) | Normal (Optimal Health) |
| **Red Rot** | *Colletotrichum falcatum Went* (*Glomerella tucumanensis*) | Severe (Critical Foliar & Midrib Necrosis) |
| **Rust** | *Puccinia melanocephala* / *Puccinia kuehnii* | Moderate to High (Uredinial Pustules) |
| **Yellow Leaf** | Sugarcane Yellow Leaf Virus (SCYLV) / *Polerovirus* | Systemic (Phloem Vessel Restriction) |
| **Mosaic** | Sugarcane Mosaic Virus (SCMV) / *Potyviridae* | Moderate (Chlorotic Mottling) |

---

## ⚡ Architecture & Features

- **Deep Learning Vision Engine**: MobileNetV3 / ResNet deep neural network fine-tuned for botanical lesion analysis.
- **Spectral Pigment Extraction**: Computes Green Chlorophyll Vigor, Red Necrosis Ratio, Yellow Chlorosis Index, and Spatial Texture Disruption.
- **FastAPI Asynchronous REST API**:
  - `POST /api/diagnose`: Real-time leaf diagnosis via file upload or base64 data.
  - `GET /api/samples`: Curated high-resolution dataset samples for one-click testing.
  - `GET /api/dataset-stats`: Dynamic dataset metrics across the 2,521 images.
  - `POST /api/dosage-calculator`: Precise acreage-based fungicide and bio-agent dilution calculations.
  - `GET /api/health`: Engine health and PyTorch device telemetry.
- **Interactive Agronomic Web UI**: Glassmorphic dashboard with live lesion heatmap overlays, audio announcements, and dosage calculators.

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) (recommended for blazingly fast dependency management)

### 2. Setup Virtual Environment & Install Dependencies
```bash
# Using uv (instant setup)
uv venv .venv
.venv\Scripts\activate
uv pip install -r requirements.txt

# Or using standard pip
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Start the Unified Server
```bash
# Option A: One-click batch launcher
start_backend.bat

# Option B: PowerShell
.\start_backend.ps1

# Option C: Direct CLI
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🌐 Unified Master Preview Gateway

All components of GREEN-EYE are integrated into a single unified web server:

| Subsystem | Master Route | Description |
| :--- | :--- | :--- |
| 🌿 **Full-Stack Studio** | [http://localhost:8000](http://localhost:8000) | Complete Diagnostic Studio, 2,521 Dataset Explorer, Disease Guide, Treatment Calculator & Multilingual Voice Guide. |
| 🔐 **Login & Auth Portal** | [http://localhost:8000/login](http://localhost:8000/login) | Multilingual sign-in (Telugu, English, Hindi), Google OAuth & 1-Click Demo Login. |
| ⚡ **FastAPI Swagger Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive Swagger UI API testing and telemetry. |
| 📖 **ReDoc Specification** | [http://localhost:8000/redoc](http://localhost:8000/redoc) | Technical REST API specification. |

---

## 🎯 Model Training

Train the PyTorch classifier directly on your 2,521 local dataset images:
```bash
uv run python train.py 5
```
*(Where `5` is the number of training epochs. Best model weights are automatically saved to `models/green_eye_model.pth`)*.

---

## 📂 Project Directory Structure

```
├── Healthy/                  # 522 Healthy sugarcane leaf images
├── Mosaic/                   # 462 Mosaic virus images
├── RedRot/                   # 518 Red rot fungal lesion images
├── Rust/                     # 514 Leaf rust pustule images
├── Yellow/                   # 505 Yellow leaf syndrome images
├── backend/
│   ├── __init__.py
│   ├── config.py             # Disease knowledge base & agronomic prescriptions
│   ├── model.py              # PyTorch model architecture & inference pipeline
│   └── main.py               # FastAPI application & REST endpoints
├── train.py                  # PyTorch model training script
├── index.html                # GREEN-EYE web interface
├── app.js                    # Web application logic & API client
├── style.css                 # Modern responsive styling
├── start_backend.bat         # One-click Windows batch launcher
├── start_backend.ps1         # PowerShell launcher
├── requirements.txt          # Python dependencies
└── pyproject.toml            # Project packaging specification
```

---

## 🛡️ License
MIT License. Built for precision agronomy and crop disease resilience.
