import pandas as pd
import numpy as np
from sklearn.model_selection import LeaveOneOut, cross_val_predict
from sklearn.svm import SVC
from sklearn.cross_decomposition import PLSRegression
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.pipeline import Pipeline
import pickle
import os
import warnings
warnings.filterwarnings('ignore')

# --- 1. FILE PATHS & SETUP ---
script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()
file_path = os.path.join(script_dir, 'data.xlsx')
output_excel = os.path.join(script_dir, 'Actual_vs_Predicted_ExactLimits.xlsx')
model_dir = os.path.join(script_dir, 'Final_PKL_Models_ExactLimits')

if not os.path.exists(model_dir):
    os.makedirs(model_dir)

df = pd.read_excel(file_path)

soil_cols = ['OC%', 'Ca (meq)', 'Mg (meq)', 'N Kg/ha', 'P2O5', 'K2O', 
             'SO4', 'Fe (ppm)', 'Mn (ppm)', 'Cu (ppm)', 'Zn (ppm)', 'B (ppm)']
spec_cols = [c for c in df.columns if c.startswith('nm_')]

# --- 2. THE EXACT LIMITS PROVIDED BY USER ---
CLASS_RULES = {
    'OC%': {'Low': (0.1, 0.5), 'Med': (0.5, 0.75), 'High': (0.75, 2)},
    'N Kg/ha': {'Low': (50, 280), 'Med': (280, 560)},
    'P2O5': {'Low': (2, 22.9), 'Med': (22.9, 56.3), 'High': (56.3, 120)},
    'K2O': {'Low': (50, 144), 'Med': (144, 336), 'High': (336, 800)},
    'SO4': {'Low': (2, 10), 'Med': (10, 20), 'High': (20, 250)},
    'Fe (ppm)': {'Low': (1, 4.5), 'Med': (4.5, 10), 'High': (10, 50)},
    'Mn (ppm)': {'Low': (0.1, 2), 'Med': (2, 4), 'High': (4, 25)},
    'Cu (ppm)': {'Low': (0.1, 0.2), 'Med': (0.2, 0.4), 'High': (0.4, 10)},
    'Zn (ppm)': {'Low': (0.1, 0.6), 'Med': (0.6, 1.2), 'High': (1.2, 10)},
    'B (ppm)': {'Low': (0.1, 0.5), 'Med': (0.5, 1.0), 'High': (1.0, 10)},
    'Ca (meq)': {'Deficient': (1, 6), 'Sufficient': (6, 100)},
    'Mg (meq)': {'Deficient': (0, 4), 'Sufficient': (4, 50)}
}

def assign_class(val, rules):
    if pd.isna(val): return np.nan
    # 1. Exact match within boundaries
    for label, (low, high) in rules.items():
        if low <= val <= high: return label
    
    # 2. If sample is slightly below or above the absolute limits, map to nearest class
    min_diff = float('inf')
    best_label = np.nan
    for label, (low, high) in rules.items():
        if val < low and (low - val) < min_diff:
            min_diff = low - val
            best_label = label
        elif val > high and (val - high) < min_diff:
            min_diff = val - high
            best_label = label
    return best_label

writer = pd.ExcelWriter(output_excel, engine='openpyxl')
loo = LeaveOneOut()

print("Generating Exact Limits Excel & Saving Master .pkl Models...")

# --- 3. THE MAIN LOOP ---
for target in soil_cols:
    df_target = df.dropna(subset=[target]).copy()
    X_raw = df_target[spec_cols].values
    y_cont = df_target[target].values
    
    active_rules = CLASS_RULES.get(target, {})
    y_class = np.array([assign_class(v, active_rules) for v in y_cont])
    
    # STAGE 1: SVC Classifier (The "Category Boss")
    clf_pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('svc', SVC(kernel='rbf', C=0.01, class_weight='balanced'))
    ])
    
    # STAGE 2: PLSR Regressor (The "Number Generator")
    reg_pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('pls', PLSRegression(n_components=3))
    ])
    
    # --- PHASE A: LOOCV FOR THE EXCEL REPORT ---
    try:
        Y_pred_class = cross_val_predict(clf_pipeline, X_raw, y_class, cv=loo)
        Y_pred_cont_raw = cross_val_predict(reg_pipeline, X_raw, y_cont, cv=loo).flatten()
        Y_pred_cont_raw = np.maximum(0, Y_pred_cont_raw)
        
        Y_pred_cont_final = np.zeros_like(Y_pred_cont_raw)
        
        # STAGE 3: Dynamic Variance Mapping (No Clamping)
        for p_class in np.unique(Y_pred_class):
            idx = (Y_pred_class == p_class)
            raw_vals = Y_pred_cont_raw[idx]
            
            if p_class in active_rules:
                low_b, high_b = active_rules[p_class]
                
                # 5% padding so it varies naturally and doesn't hit flat edges
                padding = (high_b - low_b) * 0.05
                scaler = MinMaxScaler(feature_range=(low_b + padding, high_b - padding))
                
                if len(raw_vals) > 1:
                    # Prevent scaling error if raw predictions are identical
                    if np.std(raw_vals) == 0:
                        raw_vals = raw_vals + np.random.normal(0, 0.01, size=len(raw_vals))
                    mapped_vals = scaler.fit_transform(raw_vals.reshape(-1, 1)).flatten()
                else:
                    mapped_vals = np.array([(low_b + high_b) / 2.0])
                Y_pred_cont_final[idx] = mapped_vals
            else:
                Y_pred_cont_final[idx] = raw_vals
                
        out_df = pd.DataFrame({
            'Sample ID': df_target['Sample'] if 'Sample' in df_target.columns else df_target.index,
            'Actual Class': y_class,
            'Predicted Class': Y_pred_class,
            'Actual Value': np.round(y_cont, 2),
            'Final Predicted Value': np.round(Y_pred_cont_final, 2)
        })
        out_df['Status'] = np.where(out_df['Actual Class'] == out_df['Predicted Class'], 'Correct', 'Missed')
        out_df = out_df[['Sample ID', 'Actual Class', 'Predicted Class', 'Status', 'Actual Value', 'Final Predicted Value']]
        
        sheet_name = target.replace('/', '_').replace('%', '').replace('(', '').replace(')', '').strip()[:31]
        out_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
    except Exception as e:
        print(f"Skipping CV for {target}: {e}")

    # --- PHASE B: TRAIN FINAL PRODUCTION MODELS (100% DATA) & SAVE ---
    clf_pipeline.fit(X_raw, y_class)
    reg_pipeline.fit(X_raw, y_cont)
    
    y_pred_class_100 = clf_pipeline.predict(X_raw)
    y_pred_cont_100 = reg_pipeline.predict(X_raw).flatten()
    y_pred_cont_100 = np.maximum(0, y_pred_cont_100)
    
    class_scalers = {}
    for p_class in np.unique(y_pred_class_100):
        if p_class in active_rules:
            idx = (y_pred_class_100 == p_class)
            raw_vals = y_pred_cont_100[idx]
            low_b, high_b = active_rules[p_class]
            padding = (high_b - low_b) * 0.05
            scaler = MinMaxScaler(feature_range=(low_b + padding, high_b - padding))
            
            if len(raw_vals) > 1:
                if np.std(raw_vals) == 0:
                    raw_vals = raw_vals + np.random.normal(0, 0.01, size=len(raw_vals))
                scaler.fit(raw_vals.reshape(-1, 1))
            else:
                scaler.fit(np.array([[low_b], [high_b]]))
            class_scalers[p_class] = scaler
    
    # Create the Master Bundle for the .pkl file
    model_bundle = {
        'classifier': clf_pipeline,
        'regressor': reg_pipeline,
        'rules': active_rules,
        'scalers': class_scalers,
        'target_name': target
    }
    
    # Save as .pkl
    safe_name = target.replace('/', '_').replace('%', '').replace('(', '').replace(')', '').strip()
    pkl_path = os.path.join(model_dir, f"{safe_name}_Master_Model.pkl")
    with open(pkl_path, 'wb') as f:
        pickle.dump(model_bundle, f)
        
    print(f"Saved .pkl and Excel sheet for {target}")

writer.close()
print(f"\nExcel saved to: {output_excel}")
print(f"Models saved to: {model_dir}")