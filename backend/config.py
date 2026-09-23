from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)
MODEL_WEIGHTS_PATH = MODELS_DIR / "green_eye_model.pth"

# 5 Core Disease Classes in Dataset
CLASSES = ["Healthy", "Mosaic", "RedRot", "Rust", "Yellow"]

# Disease Knowledge Base with Agronomic & Clinical Prescriptions
DISEASE_KNOWLEDGE = {
    "Healthy": {
        "title": "Healthy Sugarcane Foliage",
        "pathogen": "Saccharum officinarum L. (Normal Vigorous Tissue)",
        "severity": "Normal (Optimal Health)",
        "severity_score": 0,
        "icon": "fa-circle-check",
        "color_class": "verdict-healthy",
        "hex_color": "#10b981",
        "immediate": "No corrective agronomic intervention required. Leaf structure exhibits optimal photosynthetic vigor.",
        "chemical": "No chemical fungicides needed. Avoid excessive prophylactic spraying to preserve beneficial phyllosphere microflora.",
        "biological": "Continue regular soil organic matter enrichment and beneficial mycorrhizal inoculation.",
        "followup": "Maintain scheduled canopy monitoring every 21–30 days. Inspect underside of leaves for early vector aphid presence."
    },
    "RedRot": {
        "title": "Sugarcane Red Rot Disease",
        "pathogen": "Colletotrichum falcatum Went (Glomerella tucumanensis)",
        "severity": "Severe (Critical Foliar / Midrib Infection)",
        "severity_score": 85,
        "icon": "fa-triangle-exclamation",
        "color_class": "verdict-redrot",
        "hex_color": "#ef4444",
        "immediate": "Immediately rogue out and safely incinerate heavily infected clumps. Eliminate standing water from field furrows.",
        "chemical": "Apply foliar spray of Carbendazim 50% WP @ 2.0g/L or Thiophanate Methyl 70% WP @ 1.5g/L water directly over canopy.",
        "biological": "Inoculate soil with Trichoderma harzianum @ 10g/L or fermented Pseudomonas fluorescens formulation.",
        "followup": "Resurvey field in 12–14 days. Avoid continuous ratoon in infected plots; treat seed sets at 52°C before next planting."
    },
    "Rust": {
        "title": "Sugarcane Leaf Rust",
        "pathogen": "Puccinia melanocephala / Puccinia kuehnii",
        "severity": "Moderate to High (Foliar Uredinia Spores)",
        "severity_score": 65,
        "icon": "fa-burst",
        "color_class": "verdict-rust",
        "hex_color": "#f97316",
        "immediate": "Detrash and destroy heavily rusted senescent lower leaves to enhance inter-row ventilation and lower micro-humidity.",
        "chemical": "Spray protective fungicide Mancozeb 75% WP @ 2.5g/L or systemic triazole Pyraclostrobin + Epoxiconazole @ 1.0ml/L.",
        "biological": "Apply foliar spray of Bacillus amyloliquefaciens biocontrol suspension during early morning dew drying.",
        "followup": "Re-inspect after 10 days if high humidity (>80%) persists. Balance N-P-K fertilization to avoid excess succulent nitrogen."
    },
    "Yellow": {
        "title": "Sugarcane Yellow Leaf Disease",
        "pathogen": "Sugarcane yellow leaf virus (SCYLV) / Polerovirus",
        "severity": "Systemic (Phloem Vessel Restriction)",
        "severity_score": 70,
        "icon": "fa-sun",
        "color_class": "verdict-yellow",
        "hex_color": "#eab308",
        "immediate": "Flag and isolate infected field blocks. Ensure optimal drip irrigation to mitigate moisture-induced symptom flare.",
        "chemical": "Target insect vector Melanaphis sacchari (Sugarcane aphid) with Thiamethoxam 25% WG @ 0.3g/L or Imidacloprid 17.8% SL @ 0.3ml/L.",
        "biological": "Release predatory ladybird beetles (Coccinella septempunctata) or apply Azadirachtin (Neem oil 10,000 ppm) @ 2.5ml/L.",
        "followup": "Audit next cycle seed-cane nursery using tissue-culture or serologically certified virus-indexed sets."
    },
    "Mosaic": {
        "title": "Sugarcane Mosaic Virus (SCMV)",
        "pathogen": "Sugarcane mosaic virus (SCMV) / Potyviridae",
        "severity": "Moderate (Chlorotic Foliar Mottling)",
        "severity_score": 55,
        "icon": "fa-virus",
        "color_class": "verdict-mosaic",
        "hex_color": "#06b6d4",
        "immediate": "Systematically rogue out symptomatic stunted clumps during early tillering (45–60 days after germination).",
        "chemical": "Control vector aphid colonies (Rhopalosiphum maidis) with Acetamiprid 20% SP @ 0.2g/L or Dimethoate 30% EC @ 1.5ml/L.",
        "biological": "Introduce Chrysoperla carnea (Green lacewing) larvae to feed on aphid colonies.",
        "followup": "Sterilize harvest machetes and cutter blades with 10% sodium hypochlorite to prevent mechanical transmission."
    }
}
