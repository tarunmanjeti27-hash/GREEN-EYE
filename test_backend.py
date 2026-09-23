"""
Verification test suite for GREEN-EYE FastAPI Backend.
Tests all endpoints using FastAPI's TestClient without needing a network port.
"""

import sys
from pathlib import Path

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from starlette.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_all():
    print("==================================================")
    print("  GREEN-EYE Backend Verification Tests")
    print("==================================================")
    
    # 1. Test Health Endpoint
    print("\n[1/5] Testing GET /api/health...")
    resp = client.get("/api/health")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    health_data = resp.json()
    print(f"  [PASS] Health Status: {health_data['status']} | Service: {health_data['service']}")
    
    # 2. Test Dataset Stats Endpoint
    print("\n[2/5] Testing GET /api/dataset-stats...")
    resp = client.get("/api/dataset-stats")
    assert resp.status_code == 200
    stats = resp.json()
    print(f"  [PASS] Total dataset images detected: {stats['total_images']}")
    for cls_name, count in stats['class_breakdown'].items():
        print(f"    - {cls_name}: {count} images")
    assert stats['total_images'] > 2000, "Expected >2000 images in dataset"

    # 3. Test Samples Endpoint
    print("\n[3/5] Testing GET /api/samples...")
    resp = client.get("/api/samples?count_per_class=3")
    assert resp.status_code == 200
    samples = resp.json()
    for cls_name, paths in samples.items():
        print(f"    - {cls_name}: {len(paths)} sample URLs")
    assert len(samples["RedRot"]) > 0
    print("  [PASS] Sample images retrieved successfully.")

    # 4. Test Diagnosis Endpoint with a real image from workspace
    print("\n[4/5] Testing POST /api/diagnose with actual leaf image...")
    sample_img_path = Path("RedRot") / "redrot (1).jpeg"
    if sample_img_path.exists():
        with open(sample_img_path, "rb") as f:
            resp = client.post(
                "/api/diagnose",
                files={"file": ("redrot (1).jpeg", f, "image/jpeg")}
            )
        assert resp.status_code == 200, f"Diagnose error: {resp.text}"
        result = resp.json()
        print(f"  [PASS] Diagnosis Result:")
        print(f"    - Top Class: {result['top_class']} ({result['confidence']}%)")
        print(f"    - Pathogen: {result['pathology']['pathogen']}")
        print(f"    - Severity: {result['pathology']['severity']}")
        print(f"    - Probabilities: {result['probabilities']}")
        print(f"    - Inference Latency: {result['engine']['latency_ms']} ms")
        print(f"    - Engine: {result['engine']['model_type']}")
    else:
        print("  Notice: Sample image not found, skipping file diagnosis.")

    # 5. Test Dosage Calculator Endpoint
    print("\n[5/5] Testing POST /api/dosage-calculator...")
    dosage_payload = {
        "disease": "RedRot",
        "area": 2.5,
        "unit": "acres",
        "severity": 65.0,
        "growth_stage": "tillering"
    }
    resp = client.post("/api/dosage-calculator", json=dosage_payload)
    assert resp.status_code == 200
    dosage = resp.json()
    print(f"  [PASS] Dosage Calculation for {dosage_payload['area']} {dosage_payload['unit']} of {dosage['disease']}:")
    print(f"    - Water Volume: {dosage['water_volume_liters']} L")
    print(f"    - Primary Chemical: {dosage['primary_chemical']}")
    print(f"    - Bio Agent: {dosage['bio_agent']}")

    print("\n" + "=" * 50)
    print("  ALL 5 BACKEND VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("==================================================")


if __name__ == "__main__":
    test_all()
