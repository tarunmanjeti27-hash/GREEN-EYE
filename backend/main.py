import base64
import os
from pathlib import Path
from typing import Optional, List, Dict
import random

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel, Field

from backend.config import BASE_DIR, CLASSES, DISEASE_KNOWLEDGE
from backend.model import inference_engine

app = FastAPI(
    title="GREEN-EYE Vision Suite & Foliar Agronomy API",
    version="3.8.0",
    description="Deep learning and botanical pathology backend for sugarcane leaf disease diagnosis"
)

# Enable CORS for local and web frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# Request & Response Schemas
# ---------------------------------------------------------
class Base64DiagnoseRequest(BaseModel):
    image_base64: str = Field(..., description="Base64-encoded image string with or without data:image prefix")
    file_name: Optional[str] = "leaf_scan.jpeg"


class DosageRequest(BaseModel):
    disease: str = Field("RedRot", description="Disease class: Healthy, Mosaic, RedRot, Rust, Yellow")
    area: float = Field(1.0, ge=0.01, description="Field land area")
    unit: str = Field("acres", description="'acres' or 'hectares'")
    severity: float = Field(50.0, ge=0.0, le=100.0, description="Severity percentage (0-100)")
    growth_stage: str = Field("tillering", description="Tillering, Grand Growth, or Ripening")


# ---------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------
@app.get("/api/health")
async def health_check():
    """Health check endpoint with model status."""
    return {
        "status": "healthy",
        "service": "GREEN-EYE Pathology Engine",
        "version": "3.8.0",
        "device": str(inference_engine.device),
        "custom_weights_loaded": inference_engine.is_custom_weights_loaded,
        "classes": CLASSES
    }


@app.get("/api/dataset-stats")
async def dataset_stats():
    """Returns real-time image counts and distribution across dataset folders."""
    counts = {}
    total_images = 0
    valid_exts = {".jpeg", ".jpg", ".png", ".webp"}
    
    for cls_name in CLASSES:
        folder = BASE_DIR / cls_name
        if folder.exists() and folder.is_dir():
            file_count = sum(1 for f in folder.iterdir() if f.is_file() and f.suffix.lower() in valid_exts)
            counts[cls_name] = file_count
            total_images += file_count
        else:
            counts[cls_name] = 0

    return {
        "total_images": total_images,
        "classes": CLASSES,
        "class_breakdown": counts,
        "status": "Ready for high-throughput inference"
    }


@app.get("/api/samples")
async def get_sample_images(count_per_class: int = 4):
    """Returns curated representative image URLs for quick interactive testing."""
    samples = {}
    valid_exts = {".jpeg", ".jpg", ".png", ".webp"}
    
    for cls_name in CLASSES:
        folder = BASE_DIR / cls_name
        if folder.exists() and folder.is_dir():
            files = [f.name for f in folder.iterdir() if f.is_file() and f.suffix.lower() in valid_exts]
            # Select evenly spaced or sorted samples
            selected = sorted(files)[:count_per_class] if files else []
            samples[cls_name] = [f"/{cls_name}/{fname}" for fname in selected]
        else:
            samples[cls_name] = []
            
    return samples


@app.post("/api/diagnose")
async def diagnose_leaf_image(
    file: Optional[UploadFile] = File(None),
    base64_data: Optional[str] = Form(None)
):
    """
    Diagnoses a sugarcane leaf image uploaded via multipart/form-data.
    Supports either direct file upload or base64 form data.
    """
    image_bytes = None
    
    if file and file.filename:
        image_bytes = await file.read()
    elif base64_data:
        try:
            # Strip data:image/...;base64, prefix if present
            if "," in base64_data:
                base64_data = base64_data.split(",", 1)[1]
            image_bytes = base64.b64decode(base64_data)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 encoding: {str(e)}")
            
    if not image_bytes:
        raise HTTPException(status_code=400, detail="No image provided. Please upload an image file or provide base64 data.")

    try:
        diagnosis = inference_engine.predict(image_bytes)
        return JSONResponse(content=diagnosis)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diagnostic pipeline error: {str(e)}")


@app.post("/api/diagnose-json")
async def diagnose_leaf_json(payload: Base64DiagnoseRequest):
    """Diagnoses a leaf image from a JSON payload containing base64 image data."""
    try:
        raw_b64 = payload.image_base64
        if "," in raw_b64:
            raw_b64 = raw_b64.split(",", 1)[1]
        image_bytes = base64.b64decode(raw_b64)
        diagnosis = inference_engine.predict(image_bytes)
        return JSONResponse(content=diagnosis)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Diagnosis failed: {str(e)}")


@app.post("/api/dosage-calculator")
async def calculate_field_dosage(req: DosageRequest):
    """
    Calculates precise agronomic chemical and bio-agent application recommendations
    tailored to acreage, growth stage, and pathogen severity.
    """
    # Normalize acreage: 1 hectare = 2.47105 acres
    area_in_acres = req.area if req.unit.lower() == "acres" else req.area * 2.47105
    
    # Growth stage multiplier for canopy surface area
    stage_multipliers = {
        "germination": 0.6,
        "tillering": 1.0,
        "grand_growth": 1.45,
        "maturity": 1.2
    }
    stage_key = req.growth_stage.lower().replace(" ", "_")
    stage_factor = stage_multipliers.get(stage_key, 1.0)
    
    # Base water requirement: 200 Liters per acre for mature sugarcane canopy
    water_liters = round(200.0 * area_in_acres * stage_factor, 1)
    
    disease = req.disease if req.disease in DISEASE_KNOWLEDGE else "RedRot"
    info = DISEASE_KNOWLEDGE[disease]
    severity_factor = max(0.2, req.severity / 100.0)
    
    if disease == "Healthy":
        return {
            "disease": "Healthy",
            "required": False,
            "summary": "Canopy is vigorous. Prophylactic chemical fungicides are contraindicated.",
            "water_volume_liters": 0,
            "recommended_treatment": "Routine organic fertilization and mycorrhizal drenching.",
            "bio_agent": "Trichoderma viride @ 5g/L during next irrigation",
            "spray_schedule": "Inspect canopy in 21 days."
        }
    elif disease == "RedRot":
        carbendazim_grams = round(2.0 * water_liters * severity_factor, 1)
        trichoderma_kg = round(1.0 * area_in_acres, 2)
        return {
            "disease": "RedRot",
            "required": True,
            "pathogen": info["pathogen"],
            "water_volume_liters": water_liters,
            "primary_chemical": f"Carbendazim 50% WP: {carbendazim_grams} grams ({round(carbendazim_grams/1000, 2)} kg)",
            "alternate_chemical": f"Thiophanate Methyl 70% WP: {round(1.5 * water_liters, 1)} grams",
            "bio_agent": f"Trichoderma harzianum soil inoculation: {trichoderma_kg} kg mixed with farmyard manure",
            "application_protocol": "Direct heavy foliar spray over infected canopy & furrow drenching",
            "repeat_interval_days": 12,
            "action_warning": "Rogue out and incinerate completely collapsed canes immediately."
        }
    elif disease == "Rust":
        mancozeb_grams = round(2.5 * water_liters, 1)
        pyraclostrobin_ml = round(1.0 * water_liters, 1)
        return {
            "disease": "Rust",
            "required": True,
            "pathogen": info["pathogen"],
            "water_volume_liters": water_liters,
            "primary_chemical": f"Mancozeb 75% WP: {mancozeb_grams} grams ({round(mancozeb_grams/1000, 2)} kg)",
            "alternate_chemical": f"Pyraclostrobin + Epoxiconazole: {pyraclostrobin_ml} ml",
            "bio_agent": f"Bacillus amyloliquefaciens: {round(2.0 * water_liters, 1)} ml in morning dew",
            "application_protocol": "Spray under-leaf surface where urediniospores concentrate",
            "repeat_interval_days": 10,
            "action_warning": "Detrash lower senescent infected foliage to reduce local micro-humidity."
        }
    elif disease == "Yellow":
        thiamethoxam_grams = round(0.3 * water_liters, 1)
        neem_oil_liters = round((2.5 * water_liters) / 1000.0, 2)
        return {
            "disease": "Yellow",
            "required": True,
            "pathogen": info["pathogen"],
            "water_volume_liters": water_liters,
            "primary_chemical": f"Thiamethoxam 25% WG (Aphid vector control): {thiamethoxam_grams} grams",
            "alternate_chemical": f"Imidacloprid 17.8% SL: {round(0.3 * water_liters, 1)} ml",
            "bio_agent": f"Azadirachtin (Neem oil 10,000 ppm): {neem_oil_liters} Liters",
            "application_protocol": "Target underside of leaf whorls where vector aphid colonies reside",
            "repeat_interval_days": 14,
            "action_warning": "Yellow leaf virus is phloem-bound; maintain soil moisture via drip irrigation."
        }
    elif disease == "Mosaic":
        acetamiprid_grams = round(0.2 * water_liters, 1)
        return {
            "disease": "Mosaic",
            "required": True,
            "pathogen": info["pathogen"],
            "water_volume_liters": water_liters,
            "primary_chemical": f"Acetamiprid 20% SP (Vector aphid suppression): {acetamiprid_grams} grams",
            "alternate_chemical": f"Dimethoate 30% EC: {round(1.5 * water_liters, 1)} ml",
            "bio_agent": f"Release Chrysoperla carnea (Green lacewing) larvae @ 500/acre",
            "application_protocol": "Foliar mist covering leaf blades and terminal shoots",
            "repeat_interval_days": 14,
            "action_warning": "Sterilize cane cutting implements in 10% sodium hypochlorite bleach."
        }


# ---------------------------------------------------------
# Static File Mounts for Single-Command Full-Stack App
# ---------------------------------------------------------
# Mount dataset folders so images can be directly displayed
for cls_folder in CLASSES:
    folder_path = BASE_DIR / cls_folder
    if folder_path.exists():
        app.mount(f"/{cls_folder}", StaticFiles(directory=str(folder_path)), name=cls_folder)

# Serve login.html for authentication
@app.get("/login")
async def serve_login():
    login_file = BASE_DIR / "login.html"
    if login_file.exists():
        return FileResponse(str(login_file))
    return RedirectResponse(url="/")

@app.get("/login.html")
async def serve_login_html():
    login_file = BASE_DIR / "login.html"
    if login_file.exists():
        return FileResponse(str(login_file))
    return RedirectResponse(url="/")

# Serve index.html at root
@app.get("/")
async def serve_index():
    index_file = BASE_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "GREEN-EYE Backend Online. index.html not found in root."}

# Mount static files for CSS, JS, etc.
app.mount("/", StaticFiles(directory=str(BASE_DIR)), name="static_root")
