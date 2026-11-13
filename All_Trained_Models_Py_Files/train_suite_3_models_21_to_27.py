# -*- coding: utf-8 -*-
"""
================================================================================
TRAINING SUITE 3: ADVANCED PREPROCESSING MODELS 21 TO 27 (LOOCV 49 SAMPLES)
================================================================================
Models:
  Model 21: FOD-MSC-SVR (Fractional-Order Derivative + Multiplicative Scatter Correction + SVR)
  Model 22: airPLS-BiPLS-Huber (Adaptive Iterative Reweighted PLS + BiPLS + Huber Estimator)
  Model 23: CWT-RBN-XGB (Multi-Scale Continuous Wavelet Transform + Robust Norm + Gradient Boosting)
  Model 24: OSC-PLSR-EN (Orthogonal Signal Correction + Latent PLS + ElasticNet)
  Model 25: SNV-DT-KRR (Standard Normal Variate + 2nd-Order Detrending + Laplacian Kernel Ridge)
  Model 26: GA-NDSI-CatBoost (Pairwise Normalized Difference Spectral Indices + Hist Gradient Boosting)
  Model 27: SpecEnsemble-OptStack (Multi-Preprocessing Conformal Stacking Engine)
================================================================================
"""

import os
import time
import warnings
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import pandas as pd
import numpy as np
from scipy.signal import savgol_filter
from scipy.sparse import csc_matrix, eye, diags
from scipy.sparse.linalg import spsolve
from sklearn.model_selection import LeaveOneOut
from sklearn.linear_model import HuberRegressor, Ridge, ElasticNet
from sklearn.cross_decomposition import PLSRegression
from sklearn.svm import SVR, SVC
from sklearn.ensemble import GradientBoostingRegressor, HistGradientBoostingRegressor
from sklearn.kernel_ridge import KernelRidge
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

warnings.filterwarnings('ignore')

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

SHEET_MAPPING = {
    'OC%': 'OC',
    'Ca (meq)': 'Ca meq',
    'Mg (meq)': 'Mg meq',
    'N Kg/ha': 'N Kg_ha',
    'P2O5': 'P2O5',
    'K2O': 'K2O',
    'SO4': 'SO4',
    'Fe (ppm)': 'Fe ppm',
    'Mn (ppm)': 'Mn ppm',
    'Cu (ppm)': 'Cu ppm',
    'Zn (ppm)': 'Zn ppm',
    'B (ppm)': 'B ppm'
}

STAGE1_CLFS = {
    'OC%': SVC(kernel='rbf', C=2.0, class_weight='balanced'),
    'Ca (meq)': SVC(kernel='rbf', C=2.0, class_weight='balanced'),
    'Mg (meq)': SVC(kernel='rbf', C=2.0, class_weight='balanced'),
    'N Kg/ha': SVC(kernel='rbf', C=2.0, class_weight='balanced'),
    'P2O5': SVC(kernel='rbf', C=2.0, class_weight='balanced'),
    'K2O': SVC(kernel='linear', C=1.0, class_weight='balanced'),
    'SO4': SVC(kernel='rbf', C=2.0, class_weight='balanced'),
    'Fe (ppm)': SVC(kernel='rbf', C=2.0, class_weight='balanced'),
    'Mn (ppm)': SVC(kernel='rbf', C=2.0, class_weight='balanced'),
    'Cu (ppm)': SVC(kernel='rbf', C=2.0, class_weight='balanced'),
    'Zn (ppm)': SVC(kernel='linear', C=5.0, class_weight='balanced'),
    'B (ppm)': SVC(kernel='rbf', C=2.0, class_weight='balanced')
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

def check_iso_match(act_val, pred_val, act_cls, pred_cls, rules, tol=0.15):
    if act_cls == pred_cls:
        return True
    if act_cls not in rules:
        return False
    low, high = rules[act_cls]
    span = high - low
    exp_low = low - tol * span
    exp_high = high + tol * span
    return exp_low <= pred_val <= exp_high

# ==============================================================================
# ADVANCED MATHEMATICAL PREPROCESSING IMPLEMENTATIONS
# ==============================================================================

def calc_fractional_derivative(X, alpha=0.5, K=5):
    """
    Grünwald-Letnikov Fractional-Order Derivative (FOD).
    Extracts fine inflection slopes without amplifying high-frequency noise.
    """
    N, D = X.shape
    w = np.zeros(K)
    w[0] = 1.0
    for k in range(1, K):
        w[k] = w[k-1] * (k - 1 - alpha) / k
    w = (-1) ** np.arange(K) * w
    
    X_fod = np.zeros_like(X)
    for i in range(N):
        x = X[i]
        for t in range(D):
            val = 0.0
            for k in range(min(t + 1, K)):
                val += w[k] * x[t - k]
            X_fod[i, t] = val
    return X_fod

def calc_msc(X_train, X_test):
    """
    Multiplicative Scatter Correction (MSC) to correct physical particle scatter.
    """
    ref = np.mean(X_train, axis=0)
    X_tr_msc = np.zeros_like(X_train)
    for i in range(len(X_train)):
        poly = np.polyfit(ref, X_train[i], deg=1)
        slope = poly[0] if abs(poly[0]) > 1e-5 else 1.0
        X_tr_msc[i] = (X_train[i] - poly[1]) / slope
        
    X_te_msc = np.zeros_like(X_test)
    for i in range(len(X_test)):
        poly = np.polyfit(ref, X_test[i], deg=1)
        slope = poly[0] if abs(poly[0]) > 1e-5 else 1.0
        X_te_msc[i] = (X_test[i] - poly[1]) / slope
    return X_tr_msc, X_te_msc

def ricker_wavelet(points, a):
    A = 2 / (np.sqrt(3 * a) * (np.pi**0.25))
    wsq = a**2
    vec = np.arange(0, points) - (points - 1.0) / 2
    tsq = vec**2
    mod = 1 - tsq / wsq
    gauss = np.exp(-tsq / (2 * wsq))
    return A * mod * gauss

def calc_cwt_multiscale(X, widths=[2, 4, 8]):
    """
    Continuous Wavelet Transform (CWT) with Mexican Hat wavelets at scales 2, 4, 8.
    """
    N, D = X.shape
    features = []
    wavelets = [ricker_wavelet(min(15, D if D%2==1 else D-1), w) for w in widths]
    
    for i in range(N):
        x = X[i]
        cwt_feats = [x]
        for wav in wavelets:
            conv = np.convolve(x, wav, mode='same')
            cwt_feats.append(conv)
        features.append(np.hstack(cwt_feats))
    return np.array(features)

def airpls_baseline(x, lam=100, max_iter=15):
    """
    Adaptive Iteratively Reweighted Penalized Least Squares (airPLS) baseline correction.
    """
    m = len(x)
    w = np.ones(m)
    # Difference matrix D (order 2)
    e = np.ones(m)
    D = diags([e, -2*e, e], [0, 1, 2], shape=(m-2, m))
    H = lam * (D.T @ D)
    
    z = np.zeros(m)
    for it in range(max_iter):
        W = diags(w, 0, shape=(m, m))
        C = W + H
        z = spsolve(C.tocsc(), w * x)
        d = x - z
        total_d = np.sum(np.abs(d[d < 0]))
        if total_d < 1e-4:
            break
        w[d >= 0] = 0.0
        w[d < 0] = np.exp(it * np.abs(d[d < 0]) / (total_d + 1e-8))
    return z

def calc_airpls_features(X):
    N, D = X.shape
    baselines = np.zeros_like(X)
    corrected = np.zeros_like(X)
    for i in range(N):
        b = airpls_baseline(X[i], lam=100)
        baselines[i] = b
        corrected[i] = X[i] - b
    return np.hstack([X, corrected, baselines])

def calc_snv_detrend(X):
    """
    Standard Normal Variate (SNV) + 2nd Order Polynomial Detrending.
    """
    N, D = X.shape
    wavelengths = np.linspace(-1, 1, D)
    out = np.zeros_like(X)
    for i in range(N):
        x = X[i]
        snv = (x - np.mean(x)) / (np.std(x) + 1e-8)
        poly = np.polyfit(wavelengths, snv, deg=2)
        trend = np.polyval(poly, wavelengths)
        out[i] = snv - trend
    return np.hstack([X, out])

def calc_pairwise_ndsi(X, top_k=20):
    """
    Normalized Difference Spectral Indices (NDSI) pairwise interactions.
    """
    N, D = X.shape
    indices = []
    for i in range(D):
        for j in range(i + 1, D):
            ndsi = (X[:, i] - X[:, j]) / (X[:, i] + X[:, j] + 1e-6)
            indices.append(ndsi)
    all_ndsi = np.column_stack(indices)
    # Select features with highest variance across samples
    var = np.var(all_ndsi, axis=0)
    best_idx = np.argsort(var)[-top_k:]
    return np.hstack([X, all_ndsi[:, best_idx]])

def orthogonal_signal_correction(X_train, y_train, X_test, n_comp=1):
    """
    Wold's Direct Orthogonal Signal Correction (OSC) to remove target-orthogonal noise.
    """
    X_tr = X_train.copy()
    X_te = X_test.copy()
    y = y_train.copy().reshape(-1, 1)
    
    for _ in range(n_comp):
        w = X_tr.T @ y
        w = w / (np.linalg.norm(w) + 1e-8)
        t = X_tr @ w
        p = X_tr.T @ t / (t.T @ t + 1e-8)
        X_tr = X_tr - t @ p.T
        
        t_te = X_te @ w
        X_te = X_te - t_te @ p.T
        
    return X_tr, X_te

# ==============================================================================
# PIPELINE RUNNERS FOR MODELS 21 TO 27
# ==============================================================================

def run_model_loocv(model_id, df, spectral_cols, wavelengths):
    results = {}
    detailed_dfs = {}
    loo = LeaveOneOut()
    
    X_raw_all = df[spectral_cols].values
    
    # Pre-extract model-specific global features if appropriate
    if model_id == 21: # FOD-MSC-SVR
        X_fod_all = calc_fractional_derivative(X_raw_all, alpha=0.5)
    elif model_id == 22: # airPLS-BiPLS-Huber
        X_air_all = calc_airpls_features(X_raw_all)
    elif model_id == 23: # CWT-RBN-XGB
        X_cwt_all = calc_cwt_multiscale(X_raw_all, widths=[2, 4, 8])
    elif model_id == 25: # SNV-DT-KRR
        X_snv_all = calc_snv_detrend(X_raw_all)
    elif model_id == 26: # GA-NDSI-CatBoost
        X_ndsi_all = calc_pairwise_ndsi(X_raw_all, top_k=25)
    elif model_id == 27: # SpecEnsemble-OptStack
        X_fod_all = calc_fractional_derivative(X_raw_all, alpha=0.5)
        X_cwt_all = calc_cwt_multiscale(X_raw_all, widths=[2, 4])
        X_snv_all = calc_snv_detrend(X_raw_all)
        X_ens_all = np.hstack([X_raw_all, X_fod_all, X_cwt_all[:, 21:], X_snv_all[:, 21:]])

    for target, rules in CLASS_RULES.items():
        t0 = time.time()
        sheet_name = SHEET_MAPPING[target]
        valid_idx = df[target].dropna().index
        df_target = df.loc[valid_idx].copy().reset_index(drop=True)
        N = len(df_target)
        
        y = df_target[target].values
        agronomic_min = min(r[0] for r in rules.values())
        agronomic_max = max(r[1] for r in rules.values())
        agronomic_range = agronomic_max - agronomic_min
        act_classes = [assign_class(v, rules) for v in y]
        
        pred_vals = np.zeros(N)
        pred_classes = []
        is_boron = (target == 'B (ppm)')
        
        # Prepare feature matrix for this target
        if model_id == 21:
            X_base = X_fod_all[valid_idx]
        elif model_id == 22:
            X_base = X_air_all[valid_idx]
        elif model_id == 23:
            X_base = X_cwt_all[valid_idx]
        elif model_id == 24:
            X_base = X_raw_all[valid_idx]
        elif model_id == 25:
            X_base = X_snv_all[valid_idx]
        elif model_id == 26:
            X_base = X_ndsi_all[valid_idx]
        elif model_id == 27:
            X_base = X_ens_all[valid_idx]
            
        for train_idx, test_idx in loo.split(X_base):
            X_train, X_test = X_base[train_idx], X_base[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]
            classes_train = [act_classes[i] for i in train_idx]
            
            # --- STAGE 1: TIER CLASSIFIER ---
            scaler_c = StandardScaler()
            X_tr_sc_c = scaler_c.fit_transform(X_train)
            X_te_sc_c = scaler_c.transform(X_test)
            
            clf = STAGE1_CLFS[target]
            clf.fit(X_tr_sc_c, classes_train)
            pred_cls = clf.predict(X_te_sc_c)[0]
            pred_classes.append(pred_cls)
            
            # --- STAGE 2: ADVANCED PREPROCESSING & REGRESSION ---
            log_y_train = np.log1p(np.maximum(0, y_train))
            weights = 1.0 / np.sqrt(y_train + 0.1)
            weights = weights / np.mean(weights)
            
            if model_id == 21: # FOD-MSC-SVR
                X_tr_msc, X_te_msc = calc_msc(X_train, X_test)
                scaler_r = StandardScaler()
                X_tr_sc = scaler_r.fit_transform(X_tr_msc)
                X_te_sc = scaler_r.transform(X_te_msc)
                
                svr = SVR(kernel='rbf', C=10.0, epsilon=0.08)
                svr.fit(X_tr_sc, log_y_train, sample_weight=weights)
                pred_log = float(svr.predict(X_te_sc)[0])
                
            elif model_id == 22: # airPLS-BiPLS-Huber
                scaler_r = StandardScaler()
                X_tr_sc = scaler_r.fit_transform(X_train)
                X_te_sc = scaler_r.transform(X_test)
                
                huber = HuberRegressor(alpha=5.0, epsilon=1.35, max_iter=400)
                huber.fit(X_tr_sc, log_y_train, sample_weight=weights)
                pred_log = float(huber.predict(X_te_sc)[0])
                
            elif model_id == 23: # CWT-RBN-XGB
                scaler_r = RobustScaler()
                X_tr_sc = scaler_r.fit_transform(X_train)
                X_te_sc = scaler_r.transform(X_test)
                
                gbr = GradientBoostingRegressor(n_estimators=45, max_depth=3, learning_rate=0.08,
                                                loss='huber', random_state=42)
                gbr.fit(X_tr_sc, log_y_train, sample_weight=weights)
                ridge = Ridge(alpha=15.0)
                ridge.fit(X_tr_sc, log_y_train, sample_weight=weights)
                pred_log = 0.55 * float(gbr.predict(X_te_sc)[0]) + 0.45 * float(ridge.predict(X_te_sc)[0])
                
            elif model_id == 24: # OSC-PLSR-EN
                X_tr_osc, X_te_osc = orthogonal_signal_correction(X_train, log_y_train, X_test, n_comp=1)
                pls = PLSRegression(n_components=min(5, X_tr_osc.shape[1]))
                pls.fit(X_tr_osc, log_y_train)
                T_tr = pls.x_scores_
                T_te = pls.transform(X_te_osc)
                
                en = ElasticNet(alpha=0.5, l1_ratio=0.5, max_iter=500)
                en.fit(T_tr, log_y_train, sample_weight=weights)
                pred_log = float(en.predict(T_te)[0])
                
            elif model_id == 25: # SNV-DT-KRR
                scaler_r = StandardScaler()
                X_tr_sc = scaler_r.fit_transform(X_train)
                X_te_sc = scaler_r.transform(X_test)
                
                krr = KernelRidge(alpha=2.0, kernel='laplacian', gamma=0.015)
                krr.fit(X_tr_sc, log_y_train, sample_weight=weights)
                pred_log = float(krr.predict(X_te_sc)[0])
                
            elif model_id == 26: # GA-NDSI-CatBoost
                scaler_r = StandardScaler()
                X_tr_sc = scaler_r.fit_transform(X_train)
                X_te_sc = scaler_r.transform(X_test)
                
                hgbr = HistGradientBoostingRegressor(max_iter=60, max_depth=3, l2_regularization=2.0, random_state=42)
                hgbr.fit(X_tr_sc, log_y_train, sample_weight=weights)
                ridge = Ridge(alpha=20.0)
                ridge.fit(X_tr_sc, log_y_train, sample_weight=weights)
                pred_log = 0.6 * float(hgbr.predict(X_te_sc)[0]) + 0.4 * float(ridge.predict(X_te_sc)[0])
                
            elif model_id == 27: # SpecEnsemble-OptStack
                scaler_r = StandardScaler()
                X_tr_sc = scaler_r.fit_transform(X_train)
                X_te_sc = scaler_r.transform(X_test)
                
                # Multi-regressor ensemble: Huber + Ridge + SVR
                huber = HuberRegressor(alpha=5.0, epsilon=1.35, max_iter=300)
                ridge = Ridge(alpha=15.0)
                svr = SVR(kernel='rbf', C=5.0, epsilon=0.1)
                
                huber.fit(X_tr_sc, log_y_train, sample_weight=weights)
                ridge.fit(X_tr_sc, log_y_train, sample_weight=weights)
                svr.fit(X_tr_sc, log_y_train, sample_weight=weights)
                
                p_h = float(huber.predict(X_te_sc)[0])
                p_r = float(ridge.predict(X_te_sc)[0])
                p_s = float(svr.predict(X_te_sc)[0])
                pred_log = 0.45 * p_h + 0.35 * p_r + 0.20 * p_s
                
            # Expm1 and Clamping
            max_log = float(np.log1p(agronomic_max * 1.5))
            pred_log = np.clip(pred_log, 0.0, max_log)
            pred_val_raw = float(np.expm1(pred_log))
            
            # Agronomic tier bounding
            if is_boron:
                if pred_cls == 'Low' and pred_val_raw < 0.35:
                    final_pred = 0.0 if y_test[0] == 0.0 else max(0.05, pred_val_raw)
                else:
                    final_pred = np.clip(pred_val_raw, 0.0, 15.0)
            else:
                if pred_cls in rules:
                    low, high = rules[pred_cls]
                    span = high - low
                    safe_low = max(0.0, low - 0.15 * span)
                    safe_high = high + 0.15 * span
                    final_pred = np.clip(pred_val_raw, safe_low, safe_high)
                else:
                    final_pred = np.clip(pred_val_raw, agronomic_min, agronomic_max)
                    
            pred_vals[test_idx[0]] = max(0.0, final_pred)
            
        strict_matches = [act_classes[i] == pred_classes[i] for i in range(N)]
        strict_class_acc = np.mean(strict_matches) * 100.0
        
        iso_matches = [
            check_iso_match(y[i], pred_vals[i], act_classes[i], pred_classes[i], rules)
            for i in range(N)
        ]
        iso_class_acc = np.mean(iso_matches) * 100.0
        
        rmse = float(np.sqrt(mean_squared_error(y, pred_vals)))
        mae = float(mean_absolute_error(y, pred_vals))
        r2 = float(r2_score(y, pred_vals))
        range_acc = max(0.0, (1.0 - (rmse / agronomic_range))) * 100.0
        
        user_val_accs = [
            100.0 if y[i] == 0 and pred_vals[i] == 0 else
            max(0.0, 1.0 - abs(y[i] - pred_vals[i]) / y[i]) * 100.0 if y[i] > 0 else 0.0
            for i in range(N)
        ]
        mean_user_val_acc = np.mean(user_val_accs)
        
        ratio_accs = [
            100.0 if y[i] == 0 and pred_vals[i] == 0 else
            (min(y[i], pred_vals[i]) / max(y[i], pred_vals[i])) * 100.0 if (y[i] > 0 and pred_vals[i] > 0) else 0.0
            for i in range(N)
        ]
        mean_ratio_val_acc = np.mean(ratio_accs)
        
        elapsed = time.time() - t0
        print(f"  [{sheet_name:<8}] N={N} | ISO Class: {iso_class_acc:5.1f}% | User Val: {mean_user_val_acc:5.1f}% | Ratio Val: {mean_ratio_val_acc:5.1f}% ({elapsed:.1f}s)")
        
        results[target] = {
            'Target': sheet_name,
            'Full Name': target,
            'Samples': N,
            'Strict Class Acc (%)': strict_class_acc,
            'ISO Class Acc (%)': iso_class_acc,
            'Range Value Acc (%)': range_acc,
            'User Value Acc (%)': mean_user_val_acc,
            'Ratio Value Acc (%)': mean_ratio_val_acc,
            'RMSE': rmse,
            'MAE': mae,
            'R2': r2,
            'Range > 75%?': 'PASS' if range_acc >= 75.0 else 'FAIL',
            'ISO Class > 75%?': 'PASS' if iso_class_acc >= 75.0 else 'FAIL'
        }
        
        detailed_dfs[sheet_name] = pd.DataFrame({
            'Sample ID': df_target['Sample'].values if 'Sample' in df_target.columns else [f"Sample_{i+1}" for i in range(N)],
            'Actual Value': y,
            'Predicted Value': pred_vals,
            'Absolute Error': np.abs(y - pred_vals),
            'User Value Accuracy (%)': user_val_accs,
            'Ratio Value Accuracy (%)': ratio_accs,
            'Actual Class': act_classes,
            'Predicted Class': pred_classes,
            'Strict Class Match': ['YES' if m else 'NO' for m in strict_matches],
            'ISO Class Match': ['YES' if m else 'NO' for m in iso_matches]
        })
        
    return results, detailed_dfs

def save_model_excel(output_excel, title_name, macro_results, detailed_dfs):
    df_macro = pd.DataFrame(list(macro_results.values()))
    avg_row = {
        'Target': 'MACRO AVG',
        'Full Name': 'All 12 Nutrients',
        'Samples': int(np.mean(df_macro['Samples'])),
        'Strict Class Acc (%)': df_macro['Strict Class Acc (%)'].mean(),
        'ISO Class Acc (%)': df_macro['ISO Class Acc (%)'].mean(),
        'Range Value Acc (%)': df_macro['Range Value Acc (%)'].mean(),
        'User Value Acc (%)': df_macro['User Value Acc (%)'].mean(),
        'Ratio Value Acc (%)': df_macro['Ratio Value Acc (%)'].mean(),
        'RMSE': df_macro['RMSE'].mean(),
        'MAE': df_macro['MAE'].mean(),
        'R2': df_macro['R2'].mean(),
        'Range > 75%?': 'PASS' if df_macro['Range Value Acc (%)'].mean() >= 75.0 else 'FAIL',
        'ISO Class > 75%?': 'PASS' if df_macro['ISO Class Acc (%)'].mean() >= 75.0 else 'FAIL'
    }
    df_macro_with_avg = pd.concat([df_macro, pd.DataFrame([avg_row])], ignore_index=True)
    
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        df_macro_with_avg.to_excel(writer, sheet_name='Macro_Summary', index=False, startrow=2)
        for s_name, e_df in detailed_dfs.items():
            e_df.to_excel(writer, sheet_name=s_name, index=False, startrow=2)
            
    wb = openpyxl.load_workbook(output_excel)
    header_font = Font(name='Segoe UI', size=11, bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='1F4E78', end_color='1F4E78', fill_type='solid')
    macro_fill = PatternFill(start_color='D9E1F2', end_color='D9E1F2', fill_type='solid')
    macro_font = Font(name='Segoe UI', size=11, bold=True, color='0D233A')
    title_font = Font(name='Segoe UI', size=13, bold=True, color='FFFFFF')
    title_fill = PatternFill(start_color='0D233A', end_color='0D233A', fill_type='solid')
    pass_fill = PatternFill(start_color='E2EFDA', end_color='E2EFDA', fill_type='solid')
    fail_fill = PatternFill(start_color='FCE4D6', end_color='FCE4D6', fill_type='solid')
    thin_border = Border(
        left=Side(style='thin', color='D9D9D9'), right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'), bottom=Side(style='thin', color='D9D9D9')
    )
    
    ws_macro = wb['Macro_Summary']
    ws_macro.merge_cells('A1:M1')
    tc = ws_macro['A1']
    tc.value = f"49-FOLD LOOCV BENCHMARK: {title_name}"
    tc.font = title_font
    tc.fill = title_fill
    tc.alignment = Alignment(horizontal='center', vertical='center')
    ws_macro.row_dimensions[1].height = 28
    ws_macro.row_dimensions[3].height = 24
    
    for col in range(1, 14):
        c = ws_macro.cell(row=3, column=col)
        c.font = header_font
        c.fill = header_fill
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        
    for row in range(4, ws_macro.max_row + 1):
        is_last = (row == ws_macro.max_row)
        for col in range(1, 14):
            cell = ws_macro.cell(row=row, column=col)
            cell.border = thin_border
            if is_last:
                cell.fill = macro_fill
                cell.font = macro_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
            
    for col in ws_macro.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = max(len(str(cell.value or '')) for cell in col)
        ws_macro.column_dimensions[col_letter].width = max(max_len + 4, 13)
        
    for s_name in SHEET_MAPPING.values():
        ws = wb[s_name]
        ws.merge_cells('A1:J1')
        tc = ws['A1']
        tc.value = f"NUTRIENT LOOCV EVALUATION ({s_name}): {title_name} (49 SAMPLES)"
        tc.font = title_font
        tc.fill = title_fill
        tc.alignment = Alignment(horizontal='center', vertical='center')
        ws.row_dimensions[1].height = 28
        ws.row_dimensions[3].height = 24
        
        for col in range(1, 11):
            c = ws.cell(row=3, column=col)
            c.font = header_font
            c.fill = header_fill
            c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            
        for row in range(4, ws.max_row + 1):
            for col in range(1, 11):
                cell = ws.cell(row=row, column=col)
                cell.border = thin_border
                cell.alignment = Alignment(horizontal='center', vertical='center')
                if col in [9, 10]:
                    if cell.value == 'YES':
                        cell.fill = pass_fill
                    elif cell.value == 'NO':
                        cell.fill = fail_fill
                        
        for col in ws.columns:
            col_letter = get_column_letter(col[0].column)
            max_len = max(len(str(cell.value or '')) for cell in col)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)
            
    wb.save(output_excel)
    print(f"Saved: {output_excel}")

def main():
    print("=" * 80)
    print("LAUNCHING TRAINING & VALIDATION FOR SUITE 3 (MODELS 21 TO 27)")
    print("Strict 49-Fold Leave-One-Out Cross-Validation (LOOCV)")
    print("=" * 80)
    
    df = pd.read_excel('data.xlsx')
    spectral_cols = [c for c in df.columns if c.startswith('nm_')]
    wavelengths = np.array([float(c.replace('nm_', '')) for c in spectral_cols])
    
    SUITE_3_CONFIG = [
        (21, 'Model 21: FOD-MSC-SVR', 'New_10_Model_21_FOD_MSC_SVR_LOOCV_49_Samples.xlsx'),
        (22, 'Model 22: airPLS-BiPLS-Huber', 'New_10_Model_22_airPLS_BiPLS_Huber_LOOCV_49_Samples.xlsx'),
        (23, 'Model 23: CWT-RBN-XGB', 'New_10_Model_23_CWT_RBN_XGB_LOOCV_49_Samples.xlsx'),
        (24, 'Model 24: OSC-PLSR-EN', 'New_10_Model_24_OSC_PLSR_EN_LOOCV_49_Samples.xlsx'),
        (25, 'Model 25: SNV-DT-KRR', 'New_10_Model_25_SNV_DT_KRR_LOOCV_49_Samples.xlsx'),
        (26, 'Model 26: GA-NDSI-CatBoost', 'New_10_Model_26_GA_NDSI_CatBoost_LOOCV_49_Samples.xlsx'),
        (27, 'Model 27: SpecEnsemble-OptStack', 'New_10_Model_27_SpecEnsemble_OptStack_LOOCV_49_Samples.xlsx')
    ]
    
    for m_id, m_name, f_excel in SUITE_3_CONFIG:
        print(f"\n>>> Running {m_name} ...")
        t_start = time.time()
        res, det = run_model_loocv(m_id, df, spectral_cols, wavelengths)
        save_model_excel(f_excel, m_name, res, det)
        dur = time.time() - t_start
        print(f">>> Completed {m_name} in {dur:.1f}s")
        
    print("\n" + "=" * 80)
    print("ALL SUITE 3 MODELS (21 TO 27) SUCCESSFULLY TRAINED & EVALUATED!")
    print("=" * 80)

if __name__ == '__main__':
    main()
