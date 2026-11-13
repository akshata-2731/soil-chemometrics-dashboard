import os
import joblib
import pandas as pd
import numpy as np
from sklearn.cross_decomposition import PLSRegression
from sklearn.svm import SVC, SVR
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor, GradientBoostingRegressor, RandomForestClassifier
from sklearn.linear_model import Ridge, BayesianRidge, ElasticNet
from sklearn.neighbors import KNeighborsRegressor, KNeighborsClassifier
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import lightgbm as lgb
import warnings

warnings.filterwarnings('ignore')

WAVELENGTH_ORDER = [410,435,460,485,510,535,560,585,610,645,680,705,730,760,810,860,900,940,320,280,200]
FEATURE_NAMES = ["nm_" + str(nm) for nm in WAVELENGTH_ORDER]
soil_cols = ['OC%', 'Ca (meq)', 'Mg (meq)', 'N Kg/ha', 'P2O5', 'K2O', 'SO4', 'Fe (ppm)', 'Mn (ppm)', 'Cu (ppm)', 'Zn (ppm)', 'B (ppm)']

TARGET_CLEAN = {
    'OC%': 'OC', 'N Kg/ha': 'N', 'P2O5': 'P', 'K2O': 'K', 'Ca (meq)': 'Ca',
    'Mg (meq)': 'Mg', 'SO4': 'S', 'Fe (ppm)': 'Fe', 'Mn (ppm)': 'Mn',
    'Cu (ppm)': 'Cu', 'Zn (ppm)': 'Zn', 'B (ppm)': 'B'
}

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

def get_base_regressor(model_name):
    if "LightGBM" in model_name: return lgb.LGBMRegressor(n_estimators=50, random_state=42)
    elif "Hybrid_RF" in model_name or "RandomForest" in model_name: return RandomForestRegressor(n_estimators=50)
    elif "SVR" in model_name or "Geodesic" in model_name: return SVR(kernel='rbf')
    elif "PLSR" in model_name: return PLSRegression(n_components=3)
    elif "ExtraTrees" in model_name: return ExtraTreesRegressor(n_estimators=50)
    elif "GradientBoosting" in model_name: return GradientBoostingRegressor(n_estimators=50)
    elif "BayesianRidge" in model_name: return BayesianRidge()
    elif "KNN" in model_name: return KNeighborsRegressor(n_neighbors=5, weights='distance')
    elif "ElasticNet" in model_name: return ElasticNet()
    else: return PLSRegression(n_components=3)

def get_base_classifier(model_name, target):
    # If the model explicitly says SVC or something else, use it. Otherwise use the user's specific rules.
    if "SVC" in model_name: return SVC(kernel='rbf', C=10, class_weight='balanced')
    elif "KNN" in model_name: return KNeighborsClassifier(n_neighbors=3)
    else:
        if target in ['Ca (meq)', 'K2O', 'SO4', 'Fe (ppm)', 'Mn (ppm)', 'Cu (ppm)']:
            return RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42)
        elif target in ['N Kg/ha', 'P2O5', 'Zn (ppm)']:
            return LinearDiscriminantAnalysis()
        elif target in ['OC%', 'B (ppm)']:
            return KNeighborsClassifier(n_neighbors=3)
        elif target == 'Mg (meq)':
            return SVC(kernel='rbf', C=10, class_weight='balanced')
        else:
            return RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42)

def build_models():
    print("Loading dataset...")
    df = pd.read_excel('data/data.xlsx')
    df.fillna(0, inplace=True)
    
    spec_cols = [c for c in df.columns if c.startswith('nm_')]
    zero_mask = (df[spec_cols] == 0).any(axis=1)
    df = df[~zero_mask].reset_index(drop=True)

    import sys
    specific_model = sys.argv[1] if len(sys.argv) > 1 else None
    
    models_to_build = [
        "Model_1_TwoStage", "Model_2_TransformerCNN", "Model_3_BiLSTM", "Model_4_Stacking", 
        "Model_6_CV", "Model_9_Fit", "Model_10_LightGBM", "Model_11_TabPFN",
        "Hybrid_SVC_SVR", "Hybrid_RF_PLSR",
        "B01_PLSR", "B02_SVR_21D", "B03_3D_ExtraTrees", "B04_3D_RandomForest",
        "B05_3D_KernelRidge", "B06_2D_SpectralRatio", "B07_3D_SVR", "B08_GradientBoosting",
        "B09_BayesianRidge", "B10_KNN", "B11_ElasticNet", "B12_LightGBM",
        "B20_GeodesicCovariance", "B21_ContinuumDepth", "B22_OptimalSelector", 
        "B23_TwoStage_SVC_PLSR", "B24_Heterogeneous_TwoStage", "B26_BalancedTertiles", 
        "B28_BoundaryBuffer", "B29_NDSI_Stacking", "B30_DualBand_K", "TwoStage_Hybrid_Full"
    ]

    if specific_model and specific_model in models_to_build:
        models_to_build = [specific_model]
    elif specific_model and specific_model == "Frozen_Optimal_Models":
        # Handled by train_frozen_models.py
        return

    for model_name in models_to_build:
        model_dir = os.path.join("models", model_name)
        os.makedirs(model_dir, exist_ok=True)
        print(f"Retraining {model_name} with user bounding logic...")

        for target in soil_cols:
            if target not in df.columns: continue
            
            df_target = df.dropna(subset=[target]).copy()
            X_raw = df_target[spec_cols].values
            y_cont = df_target[target].values
            
            active_rules = CLASS_RULES.get(target, {})
            y_class = np.array([assign_class(v, active_rules) for v in y_cont])
            
            clf = get_base_classifier(model_name, target)
            reg = get_base_regressor(model_name)
            
            sc_clf = StandardScaler()
            X_tr_c = sc_clf.fit_transform(X_raw)
            if len(np.unique(y_class)) > 1:
                clf.fit(X_tr_c, y_class)
                train_class_preds = clf.predict(X_tr_c)
            else:
                train_class_preds = y_class
                
            sc_reg = StandardScaler()
            X_tr_r = sc_reg.fit_transform(X_raw)
            # Safe PLSR components
            if isinstance(reg, PLSRegression):
                reg.n_components = min(3, len(X_tr_r)-1)
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
            
            clean_name = TARGET_CLEAN[target]
            joblib.dump(payload, os.path.join(model_dir, f"{clean_name}_model.pkl"))

if __name__ == "__main__":
    build_models()
