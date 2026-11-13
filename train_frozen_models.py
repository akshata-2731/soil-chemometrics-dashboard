import os
import joblib
import pandas as pd
import numpy as np
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.cross_decomposition import PLSRegression
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import warnings

warnings.filterwarnings('ignore')

file_path = 'data/data.xlsx'

df = pd.read_excel(file_path)
df.fillna(0, inplace=True)

soil_cols = ['OC%', 'Ca (meq)', 'Mg (meq)', 'N Kg/ha', 'P2O5', 'K2O', 
             'SO4', 'Fe (ppm)', 'Mn (ppm)', 'Cu (ppm)', 'Zn (ppm)', 'B (ppm)']
spec_cols = [c for c in df.columns if c.startswith('nm_')]

# Clean Data: Drop rows where any wavelength is exactly 0
zero_mask = (df[spec_cols] == 0).any(axis=1)
df = df[~zero_mask].reset_index(drop=True)

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
    for label, (low, high) in rules.items():
        if low <= val <= high: return label
    min_diff = float('inf')
    best_label = np.nan
    for label, (low, high) in rules.items():
        if val < low and (low - val) < min_diff:
            min_diff = low - val; best_label = label
        elif val > high and (val - high) < min_diff:
            min_diff = val - high; best_label = label
    return best_label

def get_new_frozen_classifier(nutrient):
    if nutrient in ['Ca (meq)', 'K2O', 'SO4', 'Fe (ppm)', 'Mn (ppm)', 'Cu (ppm)']:
        return RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42)
    elif nutrient in ['N Kg/ha', 'P2O5', 'Zn (ppm)']:
        return LinearDiscriminantAnalysis()
    elif nutrient in ['OC%', 'B (ppm)']:
        return KNeighborsClassifier(n_neighbors=3)
    elif nutrient == 'Mg (meq)':
        return SVC(kernel='rbf', C=10, class_weight='balanced')
    else:
        return RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42)

def train_all_frozen():
    out_dir = "models/Frozen_Optimal_Models"
    os.makedirs(out_dir, exist_ok=True)
    print("Training Frozen Models for dashboard...")

    for target in soil_cols:
        if target not in df.columns:
            continue
            
        df_target = df.copy()
        df_target[target] = pd.to_numeric(df_target[target], errors='coerce')
        df_target = df_target.dropna(subset=[target]).copy()
        
        X_raw = df_target[spec_cols].values
        y_cont = df_target[target].values
        
        active_rules = CLASS_RULES.get(target, {})
        y_class = np.array([assign_class(v, active_rules) for v in y_cont])
        
        clf = get_new_frozen_classifier(target)
        
        sc_clf = StandardScaler()
        X_tr_c = sc_clf.fit_transform(X_raw)
        
        if len(np.unique(y_class)) > 1:
            clf.fit(X_tr_c, y_class)
            train_class_preds = clf.predict(X_tr_c)
        else:
            train_class_preds = y_class
            
        sc_reg = StandardScaler()
        X_tr_r = sc_reg.fit_transform(X_raw)
        reg = PLSRegression(n_components=min(3, len(X_tr_r)-1))
        reg.fit(X_tr_r, y_cont)
        
        train_raws = np.maximum(0, reg.predict(X_tr_r).flatten())
        
        # Fit class scalers based on predictions
        class_scalers = {}
        for pc in active_rules.keys():
            low_b, high_b = active_rules[pc]
            midpoint = (low_b + high_b) / 2.0
            idx_class = (train_class_preds == pc)
            train_raws_in_class = train_raws[idx_class]
            
            padding = (high_b - low_b) * 0.05
            scaler = MinMaxScaler(feature_range=(low_b + padding, high_b - padding))
            
            if len(train_raws_in_class) > 1:
                train_blended = (train_raws_in_class + midpoint) / 2.0
                if np.std(train_blended) == 0:
                    train_blended = train_blended + np.random.normal(0, 0.01, size=len(train_blended))
                scaler.fit(train_blended.reshape(-1, 1))
            else:
                scaler = None
                
            class_scalers[pc] = scaler

        payload = {
            "model": {
                "sc_clf": sc_clf,
                "clf": clf if len(np.unique(y_class)) > 1 else None,
                "fallback_class": y_class[0] if len(np.unique(y_class)) == 1 else None,
                "sc_reg": sc_reg,
                "reg": reg,
                "class_scalers": class_scalers,
                "active_rules": active_rules
            },
            "features": spec_cols,
            "type": "frozen_two_stage"
        }
        
        target_clean = target.split(' ')[0].replace('%', '')
        joblib.dump(payload, os.path.join(out_dir, f"{target_clean}_model.pkl"))
        print(f"Saved {target_clean}_model.pkl")

if __name__ == "__main__":
    train_all_frozen()
