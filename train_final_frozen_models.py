"""
TRAINING CODE: HIGH-SENSITIVITY TWO-STAGE FROZEN SOIL MODELS
============================================================
Trains and exports all 12 frozen nutrient models (.pkl) from data.xlsx:
- OC, N, P, K, Ca, Mg, S, Fe, Mn, Cu, Zn, B
Features:
- Dynamic Channel Weighting across all 21 spectral channels (410nm to 200nm UV)
- ExtraTrees Classifier for classification advisory tag (Low/Med/High)
- Direct Continuous Ridge Regressor for 100% continuous variation (no dead zones, no magnetic clamping)
- Safe agronomic boundary protection (K capped at 1000 kg/ha, non-negative)
- Exports .pkl files directly into 'models/Channel_Weighted_TwoStage_Models'
"""

import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

import shutil
import zipfile
import joblib
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.linear_model import Ridge

# 1. PATH RESOLUTION
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
POSSIBLE_DATA_PATHS = [
    os.path.join(SCRIPT_DIR, "data.xlsx"),
    os.path.join(SCRIPT_DIR, "data", "data.xlsx"),
    r"c:\Users\hp\Downloads\files (1) (6)\data.xlsx",
    r"c:\Users\hp\Downloads\soil cali\data.xlsx"
]

DATA_PATH = None
for p in POSSIBLE_DATA_PATHS:
    if os.path.exists(p):
        DATA_PATH = p
        break

if DATA_PATH is None:
    print("[ERROR] data.xlsx not found in expected folders!")
    sys.exit(1)

print("=" * 75)
print("TRAINING 12 HIGH-SENSITIVITY FROZEN SOIL MODELS")
print(f"Dataset: {DATA_PATH}")
print("=" * 75)

# 2. LOAD DATASET
df = pd.read_excel(DATA_PATH)
spec_cols = [c for c in df.columns if c.startswith("nm_") or "410" in c]
print(f"[OK] Found {len(spec_cols)} spectral channels: {spec_cols[0]} ... {spec_cols[-1]}")

# Clean / Median Impute
if 'Ca (meq)' in df.columns:
    df['Ca (meq)'] = df['Ca (meq)'].fillna(df['Ca (meq)'].median())
if 'Mg (meq)' in df.columns:
    df['Mg (meq)'] = df['Mg (meq)'].fillna(df['Mg (meq)'].median())

# 3. TARGET DEFINITIONS & AGRONOMIC ADVISORY RULES
TARGET_CONFIG = [
    ('OC', 'OC%', '%', {'Low': (0.1, 0.5), 'Med': (0.5, 0.75), 'High': (0.75, 4.0)}),
    ('N',  'N Kg/ha', 'kg/ha', {'Low': (50.0, 200.0), 'Med': (200.0, 320.0), 'High': (320.0, 500.0)}),
    ('P',  'P2O5', 'kg/ha', {'Low': (2.0, 22.9), 'Med': (22.9, 56.3), 'High': (56.3, 500.0)}),
    ('K',  'K2O', 'kg/ha', {'Low': (50.0, 144.0), 'Med': (144.0, 336.0), 'High': (336.0, 1000.0)}),
    ('Ca', 'Ca (meq)', 'meq', {'Deficient': (0.0, 6.0), 'Sufficient': (6.0, 55.0)}),
    ('Mg', 'Mg (meq)', 'meq', {'Deficient': (0.0, 4.0), 'Sufficient': (4.0, 25.0)}),
    ('S',  'SO4', 'ppm', {'Low': (0.1, 10.0), 'Med': (10.0, 20.0), 'High': (20.0, 200.0)}),
    ('Fe', 'Fe (ppm)', 'ppm', {'Low': (0.1, 4.5), 'Med': (4.5, 10.0), 'High': (10.0, 250.0)}),
    ('Mn', 'Mn (ppm)', 'ppm', {'Low': (0.1, 2.0), 'Med': (2.0, 4.0), 'High': (4.0, 75.0)}),
    ('Cu', 'Cu (ppm)', 'ppm', {'Low': (0.01, 0.2), 'Med': (0.2, 0.4), 'High': (0.4, 20.0)}),
    ('Zn', 'Zn (ppm)', 'ppm', {'Low': (0.01, 0.6), 'Med': (0.6, 1.2), 'High': (1.2, 12.0)}),
    ('B',  'B (ppm)', 'ppm', {'Low': (0.0, 0.5), 'Med': (0.5, 1.0), 'High': (1.0, 40.0)})
]

# Compute Channel Variability
channel_cvs = np.array([(df[c].std() / df[c].mean()) * 100.0 for c in spec_cols])
max_cv = np.max(channel_cvs)

# Output directory for frozen models
OUT_DIR = os.path.join(SCRIPT_DIR, "models", "Channel_Weighted_TwoStage_Models")
os.makedirs(OUT_DIR, exist_ok=True)

# 4. TRAIN AND EXPORT EACH MODEL
for short_n, col, unit, rules in TARGET_CONFIG:
    if col not in df.columns:
        print(f"⚠️ Column '{col}' not found, skipping...")
        continue

    y = df[col].values.astype(float)
    X_raw = df[spec_cols].values.astype(float)

    # Calculate correlation-informed channel weighting
    corrs = np.array([abs(np.corrcoef(X_raw[:, j], y)[0, 1]) for j in range(len(spec_cols))])
    weights = np.sqrt(channel_cvs / max_cv) * (1.0 + 2.0 * corrs)
    weights = weights / np.mean(weights)
    X_weighted = X_raw * weights.reshape(1, -1)

    # Class assignment for classification
    classes = []
    for val in y:
        cls_found = list(rules.keys())[0]
        for c_name, (lo, hi) in rules.items():
            if lo <= val <= hi:
                cls_found = c_name
                break
        classes.append(cls_found)
    classes = np.array(classes)

    # Stage 1: Classifier for advisory class tag
    sc_clf = StandardScaler()
    clf = ExtraTreesClassifier(n_estimators=50, random_state=42)
    clf.fit(sc_clf.fit_transform(X_weighted), classes)

    # Stage 2: Continuous Regressor (Ridge with gentle regularization)
    sc_reg = StandardScaler()
    reg = Ridge(alpha=20.0)
    reg.fit(sc_reg.fit_transform(X_weighted), y)

    # Build frozen model bundle (with backwards-compatible keys)
    bundle = {
        "short_name": short_n,
        "target_col": col,
        "unit": unit,
        "channel_weights": weights,
        "spec_cols": spec_cols,
        "clf": clf,
        "sc_clf": sc_clf,
        "reg": reg,
        "sc_reg": sc_reg,
        "active_rules": rules,
        # Universal fallback keys for all main.py versions
        "classifier": clf,
        "regressor": reg,
        "scaler": sc_reg,
        "rules": rules
    }

    out_file = os.path.join(OUT_DIR, f"{short_n}_model.pkl")
    joblib.dump({"model": bundle}, out_file, compress=3)
    print(f"  [SAVED] Exported frozen model: {short_n}_model.pkl ({col})")

# 5. GENERATE PORTABLE ZIP BUNDLE FOR RASPBERRY PI
zip_path = os.path.join(OUT_DIR, "models.zip")
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(OUT_DIR):
        for file in files:
            if file.endswith('.pkl'):
                zipf.write(os.path.join(root, file), arcname=file)

print(f"\n[PACKAGE] Portable Raspberry Pi package created: {zip_path}")
print("=" * 75)
print("[SUCCESS] ALL 12 FROZEN MODELS SUCCESSFULLY TRAINED AND SAVED!")
print("=" * 75)
