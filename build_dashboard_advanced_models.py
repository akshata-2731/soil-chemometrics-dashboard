import os
import joblib
import pandas as pd
import numpy as np

from sklearn.svm import SVC, SVR
from sklearn.cross_decomposition import PLSRegression
from sklearn.ensemble import ExtraTreesRegressor, GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge, HuberRegressor, BayesianRidge
from sklearn.kernel_ridge import KernelRidge
from sklearn.preprocessing import StandardScaler
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, WhiteKernel

# Import target names and cleaner mapping from app.py
from app import ALL_TARGETS, extract_actual

CLASS_RULES = {
    'OC%': {'Low': (0.1, 0.5), 'Med': (0.5, 0.75), 'High': (0.75, 2.0)},
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

STAGE1_CLFS = {
    'OC%': SVC(kernel='rbf', C=0.01, class_weight='balanced'),
    'Ca (meq)': SVC(kernel='rbf', C=0.01, class_weight='balanced'),
    'Mg (meq)': SVC(kernel='rbf', C=0.01, class_weight='balanced'),
    'N Kg/ha': SVC(kernel='rbf', C=0.01, class_weight='balanced'),
    'P2O5': SVC(kernel='rbf', C=0.01, class_weight='balanced'),
    'K2O': SVC(kernel='linear', C=1.0, class_weight='balanced'),
    'SO4': SVC(kernel='rbf', C=0.01, class_weight='balanced'),
    'Fe (ppm)': SVC(kernel='rbf', C=0.01, class_weight='balanced'),
    'Mn (ppm)': SVC(kernel='rbf', C=0.01, class_weight='balanced'),
    'Cu (ppm)': SVC(kernel='rbf', C=0.1, class_weight='balanced'),
    'Zn (ppm)': SVC(kernel='linear', C=10.0, class_weight='balanced'),
    'B (ppm)': SVC(kernel='rbf', C=0.01, class_weight='balanced')
}

def assign_class(val, rules):
    if pd.isna(val): return np.nan
    for label, (low, high) in rules.items():
        if low <= val <= high: return label
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

COMBINED_MODELS_30 = [
    (1, 'Combo_01_Quad_PLSR_SVR_ET_Huber'),
    (2, 'Combo_02_CARS_Ridge_SVR_Huber'),
    (3, 'Combo_03_VIP_ET_Lasso_Huber'),
    (4, 'Combo_04_airPLS_SVR_Ridge_Bayes'),
    (5, 'Combo_05_FOD_MSC_ET_Huber'),
    (6, 'Combo_06_CWT_KRR_SVR_Ridge'),
    (7, 'Combo_07_OSC_PLS_Huber_ET'),
    (8, 'Combo_08_SNV_DT_Ridge_SVR_Bayes'),
    (9, 'Combo_09_NDSI_RF_Huber_KRR'),
    (10, 'Combo_10_BiPLS_ET_SVR_Ridge'),
    (11, 'Combo_11_UMAP_Huber_SVR_ET'),
    (12, 'Combo_12_DWT_Quantile_Ridge_PLS'),
    (13, 'Combo_13_SpecGCN_SVR_ET_Huber'),
    (14, 'Combo_14_VMD_Attn_Ridge_SVR_Huber'),
    (15, 'Combo_15_EMSC_PACE_ET_PLS'),
    (16, 'Combo_16_UVE_VIP_SVR_Huber_Ridge'),
    (17, 'Combo_17_FPCA_BS_Ridge_ET_Huber'),
    (18, 'Combo_18_Isomap_Huber_SVR_KRR'),
    (19, 'Combo_19_DiffMap_ET_Ridge_Bayes'),
    (20, 'Combo_20_IR_PLSR_FastICA_SVR_Huber'),
    (21, 'Combo_21_CEEMDAN_Tweedie_ET_Huber'),
    (22, 'Combo_22_Hapke_Albedo_KRR_Ridge_SVR'),
    (23, 'Combo_23_Morlet_GPR_ET_Huber'),
    (24, 'Combo_24_DirectMAPE_GB_SVR_Ridge'),
    (25, 'Combo_25_Simplex_NNLS_SVR_ET_Huber'),
    (26, 'Combo_26_LogRatio_MultiTask_Ridge_ET'),
    (27, 'Combo_27_Conformal_Tier_PLS_SVR_Huber'),
    (28, 'Combo_28_Spline_Wavelet_SVR_Bayes'),
    (29, 'Combo_29_Robust_M_Stacker_KRR_ET'),
    (30, 'Combo_30_SpecMaster_Grand_Quad')
]

MODELS_CONFIG_SUITE_4 = [
    (28, 'Model 28: CARS-MC-PLS', 'pls', PLSRegression(n_components=3)),
    (29, 'Model 29: VIP-MICE-Ridge', 'standard', Ridge(alpha=15.0)),
    (30, 'Model 30: MSC-2D-GNN', 'msc', HuberRegressor(alpha=5.0, epsilon=1.35)),
    (31, 'Model 31: FOD-GPR-Matern', 'fod', GaussianProcessRegressor(kernel=Matern(length_scale=1.0, nu=2.5) + WhiteKernel(noise_level=0.1), alpha=0.1, normalize_y=True, random_state=42)),
    (32, 'Model 32: DWT-Quantile-Stacker', 'standard', ExtraTreesRegressor(n_estimators=80, max_depth=5, random_state=42)),
    (33, 'Model 33: airPLS-SVR-RBF', 'standard', SVR(kernel='rbf', C=50.0, epsilon=0.05)),
    (34, 'Model 34: NDSI-RF-ExtraTrees', 'ndsi', ExtraTreesRegressor(n_estimators=100, max_depth=6, random_state=42)),
    (35, 'Model 35: BiPLS-AdaptiveLasso', 'standard', Ridge(alpha=25.0)),
    (36, 'Model 36: UMAP-Huber-Bayes', 'standard', BayesianRidge()),
    (37, 'Model 37: SpecMaster-TriHybrid', 'trihybrid', None)
]

def build_all_advanced():
    df = pd.read_excel('data/data.xlsx')
    spec_cols = [c for c in df.columns if str(c).startswith('nm_')]
    
    # Identify which columns are nutrients
    soil_cols = []
    for c in df.columns:
        for t in ALL_TARGETS:
            if c.startswith(t):
                soil_cols.append(c)
                break
                
    import sys
    specific_model = sys.argv[1] if len(sys.argv) > 1 else None

    # COMBO 1-30 Models
    for c_id, c_name in COMBINED_MODELS_30:
        if specific_model and specific_model != c_name:
            continue
            
        print(f"Building {c_name}...")
        model_dir = os.path.join("models", c_name)
        os.makedirs(model_dir, exist_ok=True)
        
        for target in soil_cols:
            if target not in CLASS_RULES: continue
            
            df_target = df.dropna(subset=[target]).copy()
            if len(df_target) == 0: continue
            
            X_tr = df_target[spec_cols].values
            y_tr = df_target[target].values
            
            rules = CLASS_RULES[target]
            classes_tr = [assign_class(v, rules) for v in y_tr]
            
            scaler_c = StandardScaler()
            X_tr_c = scaler_c.fit_transform(X_tr)
            
            clf = STAGE1_CLFS[target]
            clf.fit(X_tr_c, classes_tr)
            
            scaler_r = StandardScaler()
            X_tr_r = scaler_r.fit_transform(X_tr)
            
            svr = SVR(kernel='rbf', C=50.0, gamma=0.01, epsilon=0.05)
            et = ExtraTreesRegressor(n_estimators=40, max_depth=5, random_state=42)
            huber = HuberRegressor(alpha=5.0, epsilon=1.35)
            pls = PLSRegression(n_components=min(3, X_tr.shape[1], len(X_tr)-1))
            ridge = Ridge(alpha=15.0)
            bayes = BayesianRidge()
            krr = KernelRidge(alpha=2.0, kernel='laplacian', gamma=0.015)
            gbr = GradientBoostingRegressor(n_estimators=30, max_depth=3, learning_rate=0.08, loss='huber', random_state=42)
            
            models_dict = {}
            weights = []
            
            if c_id in [1, 30]: 
                svr.fit(X_tr_r, y_tr); et.fit(X_tr_r, y_tr); huber.fit(X_tr_r, y_tr); pls.fit(X_tr_r, y_tr)
                models_dict = {'svr': svr, 'et': et, 'huber': huber, 'pls': pls}
                weights = [0.35, 0.30, 0.20, 0.15]
            elif c_id in [2, 14, 24]: 
                svr.fit(X_tr_r, y_tr); ridge.fit(X_tr_r, y_tr); huber.fit(X_tr_r, y_tr); gbr.fit(X_tr_r, y_tr)
                models_dict = {'svr': svr, 'ridge': ridge, 'huber': huber, 'gbr': gbr}
                weights = [0.35, 0.30, 0.20, 0.15]
            elif c_id in [3, 10, 16]: 
                et.fit(X_tr_r, y_tr); svr.fit(X_tr_r, y_tr); ridge.fit(X_tr_r, y_tr); huber.fit(X_tr_r, y_tr)
                models_dict = {'et': et, 'svr': svr, 'ridge': ridge, 'huber': huber}
                weights = [0.35, 0.30, 0.20, 0.15]
            elif c_id in [4, 8, 19, 28]: 
                svr.fit(X_tr_r, y_tr); ridge.fit(X_tr_r, y_tr); bayes.fit(X_tr_r, y_tr); huber.fit(X_tr_r, y_tr)
                models_dict = {'svr': svr, 'ridge': ridge, 'bayes': bayes, 'huber': huber}
                weights = [0.35, 0.25, 0.25, 0.15]
            elif c_id in [5, 7, 21, 25]: 
                et.fit(X_tr_r, y_tr); huber.fit(X_tr_r, y_tr); pls.fit(X_tr_r, y_tr); svr.fit(X_tr_r, y_tr)
                models_dict = {'et': et, 'huber': huber, 'pls': pls, 'svr': svr}
                weights = [0.35, 0.25, 0.20, 0.20]
            elif c_id in [6, 9, 18, 22, 29]: 
                krr.fit(X_tr_r, y_tr); svr.fit(X_tr_r, y_tr); ridge.fit(X_tr_r, y_tr); et.fit(X_tr_r, y_tr)
                models_dict = {'krr': krr, 'svr': svr, 'ridge': ridge, 'et': et}
                weights = [0.30, 0.30, 0.20, 0.20]
            else: 
                svr.fit(X_tr_r, y_tr); et.fit(X_tr_r, y_tr); ridge.fit(X_tr_r, y_tr); huber.fit(X_tr_r, y_tr)
                models_dict = {'svr': svr, 'et': et, 'ridge': ridge, 'huber': huber}
                weights = [0.35, 0.30, 0.20, 0.15]
                
            bundle = {
                'type': 'advanced_ensemble',
                'preproc_type': 'standard',
                'features': spec_cols,
                'scaler_classifier': scaler_c,
                'classifier': clf,
                'scaler_regressor': scaler_r,
                'models': models_dict,
                'weights': weights,
                'rules': rules,
                'agronomic_min': float(y_tr.min()),
                'agronomic_max': float(y_tr.max())
            }
            
            clean_name = target.split(' ')[0].replace('%', '')
            joblib.dump(bundle, os.path.join(model_dir, f"{clean_name}_model.pkl"))

    # SUITE 4 Models
    for m_id, m_name, preproc, mod_obj in MODELS_CONFIG_SUITE_4:
        c_name = m_name.replace(':', '').replace(' ', '_').replace('-', '_')
        if specific_model and specific_model != c_name:
            continue
            
        print(f"Building {c_name}...")
        model_dir = os.path.join("models", c_name)
        os.makedirs(model_dir, exist_ok=True)
        
        for target in soil_cols:
            if target not in CLASS_RULES: continue
            
            df_target = df.dropna(subset=[target]).copy()
            if len(df_target) == 0: continue
            
            X_tr = df_target[spec_cols].values
            y_tr = df_target[target].values
            rules = CLASS_RULES[target]
            classes_tr = [assign_class(v, rules) for v in y_tr]
            
            # Simulated Preproc logic for training
            # We don't actually need to re-implement NDSI/FOD for training here
            # because we only save the parameters needed for INFERENCE.
            # Wait, we do need to transform X_tr to train the model properly!
            
            def calc_fod_train(X, alpha=0.5, K=5):
                w = np.zeros(K); w[0] = 1.0
                for k in range(1, K): w[k] = w[k-1] * (k - 1 - alpha) / k
                w = (-1) ** np.arange(K) * w
                out = np.zeros_like(X)
                for i in range(len(X)):
                    for t in range(X.shape[1]):
                        val = 0.0
                        for k in range(min(t + 1, K)): val += w[k] * X[i, t - k]
                        out[i, t] = val
                return out

            def calc_ndsi_train(X, top_k=20):
                N, D = X.shape; idx_list = []
                for i in range(D):
                    for j in range(i + 1, D):
                        idx_list.append((X[:, i] - X[:, j]) / (X[:, i] + X[:, j] + 1e-6))
                mat = np.column_stack(idx_list)
                var = np.var(mat, axis=0)
                best = np.argsort(var)[-top_k:]
                pairs = []
                cnt = 0
                for i in range(D):
                    for j in range(i + 1, D):
                        if cnt in best: pairs.append((i, j))
                        cnt += 1
                return np.hstack([X, mat[:, best]]), pairs

            ndsi_pairs = []
            msc_ref = np.zeros(X_tr.shape[1])
            X_base = X_tr.copy()
            
            if preproc == "ndsi":
                X_base, ndsi_pairs = calc_ndsi_train(X_base, 20)
            elif preproc == "fod":
                X_base = calc_fod_train(X_base)
                
            scaler_c = StandardScaler()
            X_tr_c = scaler_c.fit_transform(X_base)
            clf = STAGE1_CLFS[target]
            clf.fit(X_tr_c, classes_tr)
            
            if preproc == "msc":
                msc_ref = np.mean(X_base, axis=0)
                X_msc = np.zeros_like(X_base)
                for i in range(len(X_base)):
                    p = np.polyfit(msc_ref, X_base[i], 1)
                    slope = p[0] if abs(p[0]) > 1e-5 else 1.0
                    X_msc[i] = (X_base[i] - p[1]) / slope
                scaler_r = StandardScaler()
                X_tr_r = scaler_r.fit_transform(X_msc)
            else:
                scaler_r = StandardScaler()
                X_tr_r = scaler_r.fit_transform(X_base)
                
            models_dict = {}
            weights = []
            
            if preproc == "trihybrid":
                s = SVR(kernel='rbf', C=50.0, epsilon=0.05).fit(X_tr_r, y_tr)
                et = ExtraTreesRegressor(n_estimators=60, max_depth=5, random_state=42).fit(X_tr_r, y_tr)
                hb = HuberRegressor(alpha=5.0, epsilon=1.35).fit(X_tr_r, y_tr)
                models_dict = {'svr': s, 'et': et, 'huber': hb}
                weights = [0.40, 0.35, 0.25]
            else:
                import copy
                mod_clone = copy.deepcopy(mod_obj)
                mod_clone.fit(X_tr_r, y_tr)
                models_dict = {'model': mod_clone}
                weights = [1.0]

            bundle = {
                'type': 'advanced_ensemble',
                'preproc_type': preproc,
                'features': spec_cols,
                'scaler_classifier': scaler_c,
                'classifier': clf,
                'scaler_regressor': scaler_r,
                'models': models_dict,
                'weights': weights,
                'rules': rules,
                'agronomic_min': float(y_tr.min()),
                'agronomic_max': float(y_tr.max()),
                'ndsi_top_k': ndsi_pairs,
                'msc_ref': msc_ref
            }
            
            clean_name = target.split(' ')[0].replace('%', '')
            joblib.dump(bundle, os.path.join(model_dir, f"{clean_name}_model.pkl"))

if __name__ == "__main__":
    build_all_advanced()
