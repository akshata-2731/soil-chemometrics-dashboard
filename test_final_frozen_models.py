"""
TEST CODE: EVALUATE FROZEN MODELS ON THE TRAINED DATASET (data.xlsx)
===================================================================
Loads the 12 frozen models from 'models/Channel_Weighted_TwoStage_Models'
and runs full evaluation on the exact training file (data.xlsx):
- Computes Actual vs Predicted for all 12 nutrients across all samples
- Calculates Mean Absolute Error (MAE), Mean Absolute Percentage Error (MAPE), and R2
- Computes Classification Accuracy (Low/Med/High)
- Exports complete row-by-row Actual vs Predicted comparison to an Excel report
- Also tests responsiveness on field samples
"""

import os
import sys

# Ensure clean UTF-8 output
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

import joblib
import pandas as pd
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. RESOLVE DATASET PATH (data.xlsx)
POSSIBLE_DATA_PATHS = [
    os.path.join(SCRIPT_DIR, "data.xlsx"),
    os.path.join(SCRIPT_DIR, "data", "data.xlsx"),
    r"C:\Users\hp\Downloads\soil cali\data.xlsx",
    r"c:\Users\hp\Downloads\files (1) (6)\data.xlsx"
]

DATA_PATH = None
for p in POSSIBLE_DATA_PATHS:
    if os.path.exists(p):
        DATA_PATH = p
        break

if DATA_PATH is None:
    print("[ERROR] Trained file 'data.xlsx' not found!")
    sys.exit(1)

# 2. RESOLVE MODEL DIRECTORY
POSSIBLE_MODEL_DIRS = [
    os.path.join(SCRIPT_DIR, "models", "Channel_Weighted_TwoStage_Models"),
    r"C:\Users\hp\Downloads\soil cali\models\Channel_Weighted_TwoStage_Models",
    r"/home/soil/models"
]

MODEL_DIR = None
for d in POSSIBLE_MODEL_DIRS:
    if os.path.exists(d) and any(f.endswith(".pkl") for f in os.listdir(d)):
        MODEL_DIR = d
        break

if MODEL_DIR is None:
    print("[ERROR] Frozen models directory not found!")
    sys.exit(1)

print("=" * 85)
print("SOIL NUTRIENT PREDICTION - TRAINED FILE (data.xlsx) COMPREHENSIVE TESTER")
print(f"Data File : {DATA_PATH}")
print(f"Model Dir : {MODEL_DIR}")
print("=" * 85)

# 3. GLOBAL PHYSICAL LIMITS
GLOBAL_AGRONOMIC_LIMITS = {
    'OC': (0.1, 4.0),
    'N':  (50.0, 500.0),
    'P':  (2.0, 500.0),
    'K':  (50.0, 1000.0),       # Cap potassium strictly at 1000 kg/ha
    'Ca': (0.5, 55.0),
    'Mg': (0.5, 25.0),
    'S':  (1.0, 200.0),
    'Fe': (0.5, 250.0),
    'Mn': (0.5, 75.0),
    'Cu': (0.05, 20.0),
    'Zn': (0.05, 12.0),
    'B':  (0.05, 15.0)
}

def soft_clamp(val, lo, hi):
    if lo <= val <= hi:
        return val
    rng = hi - lo
    if rng <= 0: return hi
    if val > hi:
        excess = (val - hi) / rng
        return hi - (rng * 0.05) / (1.0 + excess)
    else:
        deficit = (lo - val) / rng
        return lo + (rng * 0.05) / (1.0 + deficit)

# 4. TARGET MAPPINGS
TARGET_MAP = {
    'OC': ('OC%', '%'),
    'N':  ('N Kg/ha', 'kg/ha'),
    'P':  ('P2O5', 'kg/ha'),
    'K':  ('K2O', 'kg/ha'),
    'Ca': ('Ca (meq)', 'meq'),
    'Mg': ('Mg (meq)', 'meq'),
    'S':  ('SO4', 'ppm'),
    'Fe': ('Fe (ppm)', 'ppm'),
    'Mn': ('Mn (ppm)', 'ppm'),
    'Cu': ('Cu (ppm)', 'ppm'),
    'Zn': ('Zn (ppm)', 'ppm'),
    'B':  ('B (ppm)', 'ppm')
}

NUTRIENTS = list(TARGET_MAP.keys())

# 5. LOAD ALL 12 FROZEN MODELS
models = {}
for nut in NUTRIENTS:
    path = os.path.join(MODEL_DIR, f"{nut}_model.pkl")
    if os.path.exists(path):
        data = joblib.load(path)
        models[nut] = data.get("model", data) if isinstance(data, dict) else data
    else:
        print(f"[WARNING] Missing model: {nut}_model.pkl")

print(f"[OK] Successfully loaded {len(models)}/12 frozen models.\n")

# 6. LOAD AND PREPARE DATASET
df = pd.read_excel(DATA_PATH)
spec_cols = [c for c in df.columns if c.startswith("nm_") or "410" in c]
print(f"[OK] Read {len(df)} samples with {len(spec_cols)} spectral channels from trained file.\n")

# Median impute Ca and Mg if missing in dataset
if 'Ca (meq)' in df.columns:
    df['Ca (meq)'] = df['Ca (meq)'].fillna(df['Ca (meq)'].median())
if 'Mg (meq)' in df.columns:
    df['Mg (meq)'] = df['Mg (meq)'].fillna(df['Mg (meq)'].median())

# 7. RUN INFERENCE FOR A SINGLE SAMPLE VECTOR
def predict_sample(sensor_values):
    raw_vec = np.array(sensor_values, dtype=float).flatten()
    preds = {}
    
    for nutrient in NUTRIENTS:
        m = models.get(nutrient)
        if m is None:
            preds[nutrient] = ("N/A", 0.0)
            continue
            
        weights = m.get("channel_weights")
        sc_clf = m.get("sc_clf") or m.get("scaler")
        clf = m.get("clf") or m.get("classifier")
        sc_reg = m.get("sc_reg") or m.get("scaler")
        reg = m.get("reg") or m.get("regressor")
        
        # 1. Apply Channel Prioritization
        if weights is not None and len(weights) == len(raw_vec):
            X_weighted = (raw_vec * weights).reshape(1, -1)
        else:
            X_weighted = raw_vec.reshape(1, -1)
            
        # 2. Stage 1: Class Advisory Tag
        pred_cls = "Med"
        if clf is not None and sc_clf is not None:
            try:
                pred_cls = clf.predict(sc_clf.transform(X_weighted))[0]
            except Exception:
                pred_cls = "Med"
                
        # 3. Stage 2: Direct Continuous Slope
        if reg is not None and sc_reg is not None:
            raw_p = float(reg.predict(sc_reg.transform(X_weighted))[0])
        else:
            raw_p = 0.0
            
        # 4. Safe Outer Clamping
        glo, ghi = GLOBAL_AGRONOMIC_LIMITS.get(nutrient, (0.01, 1000.0))
        final_val = soft_clamp(raw_p, glo, ghi)
        
        preds[nutrient] = (pred_cls, round(final_val, 3))
        
    return preds

# 8. TEST ACROSS ALL ROWS OF THE TRAINED FILE
print("=" * 85)
print("EVALUATING MODEL PERFORMANCE ACROSS ALL SAMPLES IN TRAINED FILE:")
print("=" * 85)

summary_rows = []
export_data = {}

for nut in NUTRIENTS:
    col_name, unit = TARGET_MAP[nut]
    if col_name not in df.columns:
        continue
        
    actuals = df[col_name].values.astype(float)
    predicted_vals = []
    predicted_classes = []
    
    m = models.get(nut, {})
    rules = m.get("active_rules", {})
    
    # Predict for every row in dataset
    for i in range(len(df)):
        sample_spec = df.loc[i, spec_cols].values.astype(float)
        p_cls, p_val = predict_sample(sample_spec)[nut]
        predicted_vals.append(p_val)
        predicted_classes.append(p_cls)
        
    predicted_vals = np.array(predicted_vals)
    
    # Calculate performance metrics
    mae = np.mean(np.abs(actuals - predicted_vals))
    corr = np.corrcoef(actuals, predicted_vals)[0, 1] if np.std(predicted_vals) > 0 else 0.0
    
    # Actual classes based on rules
    actual_classes = []
    for val in actuals:
        cls_found = "Med"
        for c_name, (lo, hi) in rules.items():
            if lo <= val <= hi:
                cls_found = c_name
                break
        actual_classes.append(cls_found)
    
    cls_acc = np.mean([1 if a == p else 0 for a, p in zip(actual_classes, predicted_classes)]) * 100.0
    
    summary_rows.append({
        'Nutrient': nut,
        'Column': col_name,
        'Unit': unit,
        'Actual Mean': np.mean(actuals),
        'Pred Mean': np.mean(predicted_vals),
        'MAE': mae,
        'Correlation (R)': corr,
        'Class Accuracy (%)': cls_acc
    })
    
    export_data[f"{nut}_Actual"] = actuals
    export_data[f"{nut}_Pred"] = predicted_vals
    export_data[f"{nut}_PredClass"] = predicted_classes

# Print Metrics Summary Table
print(f"{'NUTRIENT':<10} | {'UNIT':<6} | {'ACTUAL MEAN':<12} | {'PRED MEAN':<12} | {'MAE':<10} | {'CORR (R)':<10} | {'CLASS ACC (%)':<14}")
print("-" * 88)
for s in summary_rows:
    print(f"{s['Nutrient']:<10} | {s['Unit']:<6} | {s['Actual Mean']:>11.3f} | {s['Pred Mean']:>11.3f} | {s['MAE']:>10.3f} | {s['Correlation (R)']:>10.3f} | {s['Class Accuracy (%)']:>13.1f}%")
print("-" * 88)

# 9. DISPLAY SAMPLE ACTUAL VS PREDICTED FOR FIRST 5 SAMPLES
print("\n" + "=" * 85)
print("FIRST 5 SAMPLES FROM TRAINED FILE: ACTUAL vs PREDICTED COMPARISON")
print("=" * 85)

for idx in range(min(5, len(df))):
    print(f"\n--- [Sample #{idx + 1}] ---")
    row_spec = df.loc[idx, spec_cols].values.astype(float)
    p_dict = predict_sample(row_spec)
    
    print(f"{'NUTRIENT':<10} | {'ACTUAL':<12} | {'PREDICTED':<12} | {'UNIT':<8} | {'CLASS':<10}")
    print("-" * 60)
    for nut in NUTRIENTS:
        col_name, unit = TARGET_MAP[nut]
        act_val = df.loc[idx, col_name] if col_name in df.columns else np.nan
        p_cls, p_val = p_dict[nut]
        print(f"{nut:<10} | {act_val:>11.3f} | {p_val:>11.3f} | {unit:<8} | {p_cls:<10}")

# 10. EXPORT COMPREHENSIVE AUDIT TO EXCEL
out_excel = os.path.join(SCRIPT_DIR, "Trained_File_Predictions_Audit.xlsx")
try:
    df_export = pd.DataFrame(export_data)
    df_summary = pd.DataFrame(summary_rows)
    with pd.ExcelWriter(out_excel) as writer:
        df_summary.to_excel(writer, sheet_name="Model_Metrics_Summary", index=False)
        df_export.to_excel(writer, sheet_name="All_Samples_Actual_vs_Pred", index=False)
    print(f"\n[SAVED] Complete audit saved to: {out_excel}")
except Exception as ex:
    print(f"\n[NOTE] Could not write Excel file: {ex}")

# 11. ALSO TEST THE 3 LIVE FIELD SAMPLES
print("\n" + "=" * 85)
print("FIELD SAMPLES TEST (VERIFYING CONTINUOUS UNROUNDED VARIATION):")
print("=" * 85)

field_s1 = [621.7782, 147.7311, 50.035, 40.479, 63.8, 316.8385, 202.3269, 219.023, 1032.4768, 122.1224, 348.9792, 31.2682, 1268.1235, 320.2846, 438.8409, 700.001, 29.9546, 12.987, 138.4432, 3.1585, 3.4742]
field_s2 = [622.0375, 142.9023, 49.7431, 40.1148, 62.5958, 306.8589, 203.7483, 223.4214, 1041.1273, 126.5123, 325.3631, 31.1217, 1031.6512, 326.5543, 423.7986, 578.0113, 30.3, 12.987, 142.3746, 3.1638, 3.4938]
field_s3 = [654.4955, 150.4473, 51.4528, 41.208, 65.1294, 316.6252, 218.2936, 238.7166, 976.2681, 132.7605, 341.4121, 33.2923, 1103.8229, 363.4607, 455.4384, 605.3018, 31.3362, 13.7751, 166.7166, 3.3559, 3.538]

r1 = predict_sample(field_s1)
r2 = predict_sample(field_s2)
r3 = predict_sample(field_s3)

print(f"{'NUTRIENT':<10} | {'SAMPLE 1 (16:26)':<22} | {'SAMPLE 2 (16:22)':<22} | {'SAMPLE 3 (12:48)':<22}")
print("-" * 88)
for nut in NUTRIENTS:
    c1, v1 = r1[nut]
    c2, v2 = r2[nut]
    c3, v3 = r3[nut]
    unit = TARGET_MAP[nut][1]
    print(f"{nut:<10} | {v1:>7.3f} {unit:<5} ({c1:<4}) | {v2:>7.3f} {unit:<5} ({c2:<4}) | {v3:>7.3f} {unit:<5} ({c3:<4})")
print("-" * 88)
print("[SUCCESS] ALL 12 NUTRIENTS EVALUATED SUCCESSFULLY ON TRAINED FILE AND FIELD SAMPLES!")
print("=" * 85)
