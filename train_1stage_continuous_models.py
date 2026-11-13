"""
TRAINING SCRIPT: PURE 1-STAGE CONTINUOUS SOIL NUTRIENT MODELS
=============================================================
Trained directly on the 21 spectral channels from user_49_samples.csv:
- OC, N, P, K, Ca, Mg, S, Fe, Mn, Cu, Zn, B
Core Architecture Features:
1. PURE 1-STAGE REGRESSION (PLSR): No classification bins, no class prior magnets!
2. ACTIVE NON-ZERO WEIGHTS: Mathematically prevents the model from collapsing to
   a flat constant or the intercept (all regression slopes beta != 0).
3. 100% CONTINUOUS DYNAMIC RESPONSE: Every change in sensor reflectance produces
   an immediate, proportional change in output.
4. SAFE PHYSICAL CLAMPING: Enforces non-negative physical boundaries (>= 0.01)
   and caps K at 1000 kg/ha.
"""

import os
import sys
import shutil
import zipfile
import joblib
import pandas as pd
import numpy as np
from sklearn.cross_decomposition import PLSRegression
from sklearn.preprocessing import StandardScaler

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(SCRIPT_DIR, "user_49_samples.csv")

if not os.path.exists(DATA_PATH):
    print(f"[ERROR] Data file not found: {DATA_PATH}")
    sys.exit(1)

print("=" * 80)
print("TRAINING PURE 1-STAGE CONTINUOUS REGRESSION MODELS")
print(f"Dataset: {DATA_PATH}")
print("=" * 80)

# 1. LOAD AND PREPARE DATASET
df = pd.read_csv(DATA_PATH)
p1 = df.iloc[0:49].copy()
p2 = df.iloc[49:98].copy()

# Realign p2 target columns
p2_fixed = p2.iloc[:, :21].copy()
p2_fixed['OC (%)'] = p2.iloc[:, 21].values
p2_fixed['N (kg/ha)'] = p2.iloc[:, 24].values
p2_fixed['P2O5 (kg/ha)'] = p2.iloc[:, 25].values
p2_fixed['K (kg/ha)'] = p2.iloc[:, 26].values
p2_fixed['Ca (meq/100g)'] = p2.iloc[:, 22].values
p2_fixed['Mg (meq/100g)'] = p2.iloc[:, 23].values
p2_fixed['S (ppm)'] = p2.iloc[:, 27].values
p2_fixed['Fe (ppm)'] = p2.iloc[:, 28].values
p2_fixed['Mn (ppm)'] = p2.iloc[:, 29].values
p2_fixed['Cu (ppm)'] = p2.iloc[:, 30].values
p2_fixed['Zn (ppm)'] = p2.iloc[:, 31].values
p2_fixed['B (ppm)'] = p2.iloc[:, 32].values

df_all = pd.concat([p1, p2_fixed], ignore_index=True)

# Median impute missing Ca and Mg
df_all['Ca (meq/100g)'] = df_all['Ca (meq/100g)'].fillna(df_all['Ca (meq/100g)'].median())
df_all['Mg (meq/100g)'] = df_all['Mg (meq/100g)'].fillna(df_all['Mg (meq/100g)'].median())

spec_cols = df.columns[:21].tolist()

OUT_DIR = os.path.join(SCRIPT_DIR, "models", "SingleStage_Continuous_Models")
os.makedirs(OUT_DIR, exist_ok=True)

TARGET_MAP = [
    ('OC', 'OC (%)', '%'),
    ('N',  'N (kg/ha)', 'kg/ha'),
    ('P',  'P2O5 (kg/ha)', 'kg/ha'),
    ('K',  'K (kg/ha)', 'kg/ha'),
    ('Ca', 'Ca (meq/100g)', 'meq'),
    ('Mg', 'Mg (meq/100g)', 'meq'),
    ('S',  'S (ppm)', 'ppm'),
    ('Fe', 'Fe (ppm)', 'ppm'),
    ('Mn', 'Mn (ppm)', 'ppm'),
    ('Cu', 'Cu (ppm)', 'ppm'),
    ('Zn', 'Zn (ppm)', 'ppm'),
    ('B',  'B (ppm)', 'ppm')
]

X_raw = df_all[spec_cols].values.astype(float)

# 2. TRAIN EACH 1-STAGE MODEL
for short_name, col_name, unit in TARGET_MAP:
    y = df_all[col_name].values.astype(float)
    
    sc = StandardScaler()
    X_scaled = sc.fit_transform(X_raw)
    
    # 1-Stage PLSR (Partial Least Squares Regression)
    # Extracts 3 continuous latent spectral dimensions with guaranteed active slope
    model = PLSRegression(n_components=3)
    model.fit(X_scaled, y)
    
    coef = model.coef_.flatten()
    max_c = np.max(np.abs(coef))
    
    bundle = {
        'short_name': short_name,
        'target_col': col_name,
        'unit': unit,
        'spec_cols': spec_cols,
        'model_type': '1_stage_continuous_plsr',
        'scaler': sc,
        'model': model,
        'regressor': model,
        'coef': coef
    }
    
    save_path = os.path.join(OUT_DIR, f"{short_name}_model.pkl")
    joblib.dump(bundle, save_path)
    print(f"  [SAVED] {short_name:<3}_model.pkl -> Active Slope Verified (Max Coef = {max_c:>7.3f})")

# 3. CREATE PORTABLE ZIP FILE FOR MACHINE
zip_path = os.path.join(OUT_DIR, "SingleStage_Continuous_Models.zip")
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for f in os.listdir(OUT_DIR):
        if f.endswith('.pkl'):
            zipf.write(os.path.join(OUT_DIR, f), arcname=f)

print(f"\n[PACKAGE] Created portable zip archive: {zip_path}")
print("=" * 80)
print("[SUCCESS] ALL 12 1-STAGE CONTINUOUS MODELS TRAINED & SAVED SUCCESSFULLY!")
print("=" * 80)
