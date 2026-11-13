"""
SOIL NUTRIENT PREDICTION — EXACT TWO-STAGE MODEL TESTER
Strictly loads from: C:\\Users\\hp\\Downloads\\soil cali\\models\\B02_SVR_21D
Matches the Excel Report (High_Range_Expanded_Models_and_Predictions.xlsx) 100% exactly.
"""

import os
import sys
import joblib
import numpy as np

# 1. STRICTLY LOAD FROM THIS SPECIFIC FOLDER ONLY
MODEL_DIR = r"C:\Users\hp\Downloads\soil cali\models\B02_SVR_21D"

if not os.path.exists(MODEL_DIR):
    print(f"[ERROR] Model directory does not exist: {MODEL_DIR}")
    sys.exit(1)

print("=" * 70)
print("SOIL NUTRIENT INTERACTIVE PREDICTION TESTER")
print(f"Strict Model Folder: {MODEL_DIR}")
print("=" * 70)

# 2. NUTRIENT METADATA
NUTRIENTS = ["OC", "N", "P", "K", "Ca", "Mg", "S", "Fe", "Mn", "Cu", "Zn", "B"]

UNITS = {
    "OC": "%", "N": "kg/ha", "P": "kg/ha", "K": "kg/ha",
    "Ca": "meq", "Mg": "meq", "S": "ppm", "Fe": "ppm",
    "Mn": "ppm", "Cu": "ppm", "Zn": "ppm", "B": "ppm"
}

# 3. LOAD ALL MODELS INTO MEMORY
models = {}
for nut in NUTRIENTS:
    fn = os.path.join(MODEL_DIR, f"{nut}_model.pkl")
    if os.path.exists(fn):
        try:
            data = joblib.load(fn)
            models[nut] = data.get("model", data) if isinstance(data, dict) else data
        except Exception as e:
            print(f"[WARNING] Failed to load {nut}_model.pkl: {e}")
    else:
        print(f"[MISSING] {nut}_model.pkl not found in {MODEL_DIR}")

print(f"[OK] Successfully loaded {len(models)}/12 models into memory.\n")

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

# 4. HIERARCHICAL TWO-STAGE DYNAMIC PREDICTION ROUTINE
def predict_nutrient(m, X_raw):
    sc_clf = m.get("sc_clf") or m.get("scaler")
    clf = m.get("clf") or m.get("classifier")
    active_rules = m.get("active_rules") or m.get("rules", {})
    per_class = m.get("per_class_regressors", {})
    
    # Stage 1: Class Prediction
    X_clf_sc = sc_clf.transform(X_raw) if sc_clf is not None else X_raw
    pred_cls = clf.predict(X_clf_sc)[0] if clf is not None else "Med"
    
    # Stage 2: Per-Class Dynamic Regressor
    if pred_cls in per_class:
        sc_spec, r_spec = per_class[pred_cls]
        X_reg_sc = sc_spec.transform(X_raw) if sc_spec is not None else X_raw
        raw_p = float(r_spec.predict(X_reg_sc)[0])
    else:
        sc_reg = m.get("sc_reg") or m.get("scaler")
        reg = m.get("reg") or m.get("regressor")
        X_reg_sc = sc_reg.transform(X_raw) if sc_reg is not None else X_raw
        raw_p = float(reg.predict(X_reg_sc)[0])
        
    # Stage 3: Dynamic In-Class Locking
    if active_rules and pred_cls in active_rules:
        lo, hi = active_rules[pred_cls]
        final_p = soft_clamp(raw_p, lo, hi)
    else:
        final_p = max(0.001, raw_p)
        
    return pred_cls, round(final_p, 4)

def run_prediction(sensor_values):
    X = np.array(sensor_values, dtype=float).reshape(1, -1)
    
    print("\n" + "=" * 60)
    print(f"{'NUTRIENT':<10} | {'PREDICTED CLASS':<18} | {'PREDICTED VALUE':<16} | {'UNIT':<8}")
    print("-" * 60)
    
    results = {}
    for nut in NUTRIENTS:
        if nut not in models:
            print(f"{nut:<10} | {'MISSING':<18} | {'0.000':<16} | {'-':<8}")
            continue
            
        m = models[nut]
        pred_cls, final_val = predict_nutrient(m, X)
        results[nut] = (pred_cls, final_val)
        unit = UNITS.get(nut, "")
        
        print(f"{nut:<10} | {pred_cls:<18} | {final_val:<16.4f} | {unit:<8}")
        
    print("=" * 60 + "\n")
    return results

# 5. DEFAULT TEST SAMPLE (21 CHANNELS)
DEFAULT_21_CHANNELS = [
    542.1, 550.3, 560.8, 570.2, 582.4, 595.1, 610.5, 625.3, 640.1, 
    655.4, 670.2, 685.9, 700.1, 715.4, 730.8, 745.2, 760.5, 775.1,
    0.152, 0.185, 0.388
]

def get_input():
    print("Select an input mode:")
    print("  [1] Paste 21 channel values manually (comma or space separated)")
    print("  [2] Enter sample number from data.xlsx (Sample 1 to 49)")
    print("  [3] Run default sample sensor reading")
    print("  [q] Quit")
    
    choice = input("\nEnter choice (1, 2, 3, or q): ").strip()
    return choice

def main():
    while True:
        choice = get_input()
        if choice.lower() == 'q':
            print("Exiting tester. Goodbye!")
            break
            
        if choice == '1':
            print("\nEnter or paste 21 sensor numbers (separated by commas or spaces):")
            raw_in = input("> ").strip()
            raw_in = raw_in.replace(",", " ")
            parts = [p for p in raw_in.split() if p]
            if len(parts) != 21:
                print(f"[ERROR] Expected 21 numbers, but received {len(parts)}. Please try again.\n")
                continue
            try:
                values = [float(p) for p in parts]
                run_prediction(values)
            except ValueError as e:
                print(f"[ERROR] Error parsing numbers: {e}\n")
                
        elif choice == '2':
            excel_path = r"C:\Users\hp\Downloads\soil cali\data\data.xlsx"
            if not os.path.exists(excel_path):
                print(f"[ERROR] data.xlsx not found at: {excel_path}\n")
                continue
            import pandas as pd
            df = pd.read_excel(excel_path).fillna(0)
            spec_cols = [c for c in df.columns if c.startswith("nm_")]
            
            s_idx = input(f"Enter sample index (1 to {len(df)}): ").strip()
            try:
                idx = int(s_idx) - 1
                if 0 <= idx < len(df):
                    row_vals = df.loc[idx, spec_cols].values.tolist()
                    print(f"\nTesting Sample #{idx + 1} from data.xlsx:")
                    run_prediction(row_vals)
                else:
                    print("[ERROR] Sample index out of range.\n")
            except Exception as e:
                print(f"[ERROR] Error: {e}\n")
                
        elif choice == '3':
            print("\nRunning Default 21-Channel Sensor Reading:")
            run_prediction(DEFAULT_21_CHANNELS)
            
        else:
            print("Invalid choice. Please enter 1, 2, 3, or q.\n")

if __name__ == "__main__":
    main()
