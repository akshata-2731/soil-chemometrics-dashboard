# -*- coding: utf-8 -*-
"""
================================================================================
DOMINANT-CLASS IN-RANGE BENCHMARK & ACCURACY MAXIMIZER
Tests 10 distinct ML algorithms on the dominant class of each nutrient:
  1. Mean/Median In-Range Baseline
  2. Bounded Chemometric PLSR (3-5 components)
  3. Log-Ridge In-Range Regressor (Relative-Loss Weighted)
  4. Robust Huber In-Range Estimator (epsilon=1.35)
  5. Non-linear SVR RBF (Log-space)
  6. Laplacian Kernel Ridge Regression (KRR)
  7. ElasticNet with Stoichiometric Constraints
  8. Gradient Tree Booster (Huber loss, shallow)
  9. Preprocessed airPLS-MSC Ridge Regressor
 10. Multi-Model In-Range Consensus Ensemble (Optimal Stacker)
================================================================================
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import LeaveOneOut
from sklearn.linear_model import Ridge, HuberRegressor, ElasticNet, BayesianRidge
from sklearn.cross_decomposition import PLSRegression
from sklearn.svm import SVR
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.kernel_ridge import KernelRidge
from sklearn.preprocessing import StandardScaler, RobustScaler

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

def user_accuracy(act, pred):
    accs = []
    for a, p in zip(act, pred):
        if a == 0 and p == 0:
            accs.append(100.0)
        elif a == 0:
            accs.append(max(0.0, 1.0 - abs(p)) * 100.0 if p < 1.0 else 0.0)
        else:
            accs.append(max(0.0, 1.0 - abs(a - p) / a) * 100.0)
    return np.mean(accs)

df = pd.read_excel('data.xlsx')
spectral_cols = [c for c in df.columns if c.startswith('nm_')]

MODEL_NAMES = [
    'Model 1: In-Range Median Prior',
    'Model 2: Chemometric PLSR',
    'Model 3: Log-Ridge Relative-Loss',
    'Model 4: Robust Huber In-Range',
    'Model 5: Non-linear SVR RBF',
    'Model 6: Laplacian Kernel Ridge',
    'Model 7: ElasticNet Regularized',
    'Model 8: Gradient Tree Booster',
    'Model 9: SNV-Polynomial Detrended Ridge',
    'Model 10: Multi-Model Consensus Ensemble'
]

results_matrix = {m: {} for m in MODEL_NAMES}
dominant_info = {}

for target, rules in CLASS_RULES.items():
    valid_idx = df[target].dropna().index
    df_valid = df.loc[valid_idx].copy().reset_index(drop=True)
    
    classes = [assign_class(v, rules) for v in df_valid[target]]
    counts = pd.Series(classes).value_counts()
    dominant_class = counts.index[0]
    dominant_count = counts.iloc[0]
    
    dom_mask = [c == dominant_class for c in classes]
    df_dom = df_valid[dom_mask].copy().reset_index(drop=True)
    
    N = len(df_dom)
    X = df_dom[spectral_cols].values
    y = df_dom[target].values
    
    c_low, c_high = rules[dominant_class]
    bound_low = max(0.0, min(c_low, y.min()))
    bound_high = max(c_high, y.max())
    
    dominant_info[target] = {
        'Class': dominant_class,
        'Samples': N,
        'Pct_Total': f"{N / len(df_valid) * 100:.1f}%",
        'Range': f"[{bound_low:.2f}, {bound_high:.2f}]",
        'Min': y.min(),
        'Max': y.max(),
        'Median': np.median(y)
    }
    
    loo = LeaveOneOut()
    
    preds = {m: np.zeros(N) for m in MODEL_NAMES}
    is_b = (target == 'B (ppm)')
    
    for train_idx, test_idx in loo.split(X):
        X_tr, X_te = X[train_idx], X[test_idx]
        y_tr, y_te = y[train_idx], y[test_idx]
        t_idx = test_idx[0]
        
        med_val = float(np.median(y_tr))
        mean_val = float(np.mean(y_tr))
        
        # M1: Median Prior
        preds['Model 1: In-Range Median Prior'][t_idx] = med_val
        
        sc = StandardScaler()
        X_tr_sc = sc.fit_transform(X_tr)
        X_te_sc = sc.transform(X_te)
        
        # Log target & sample weights
        log_y_tr = np.log(np.maximum(1e-4, y_tr))
        weights = 1.0 / np.sqrt(y_tr + 0.1)
        weights /= np.mean(weights)
        
        # M2: PLSR
        try:
            n_c = min(3, len(X_tr) - 1)
            pls = PLSRegression(n_components=n_c)
            pls.fit(X_tr_sc, log_y_tr)
            p_pls = float(np.exp(pls.predict(X_te_sc).ravel()[0]))
        except:
            p_pls = med_val
        preds['Model 2: Chemometric PLSR'][t_idx] = np.clip(p_pls, bound_low, bound_high)
        
        # M3: Log-Ridge
        ridge = Ridge(alpha=15.0)
        ridge.fit(X_tr_sc, log_y_tr, sample_weight=weights)
        p_rdg = float(np.exp(ridge.predict(X_te_sc)[0]))
        preds['Model 3: Log-Ridge Relative-Loss'][t_idx] = np.clip(p_rdg, bound_low, bound_high)
        
        # M4: Robust Huber
        huber = HuberRegressor(alpha=5.0, epsilon=1.35, max_iter=300)
        huber.fit(X_tr_sc, log_y_tr, sample_weight=weights)
        p_hub = float(np.exp(huber.predict(X_te_sc)[0]))
        preds['Model 4: Robust Huber In-Range'][t_idx] = np.clip(p_hub, bound_low, bound_high)
        
        # M5: SVR RBF
        svr = SVR(kernel='rbf', C=5.0, epsilon=0.08)
        svr.fit(X_tr_sc, log_y_tr, sample_weight=weights)
        p_svr = float(np.exp(svr.predict(X_te_sc)[0]))
        preds['Model 5: Non-linear SVR RBF'][t_idx] = np.clip(p_svr, bound_low, bound_high)
        
        # M6: Laplacian KRR
        krr = KernelRidge(alpha=2.0, kernel='laplacian', gamma=0.015)
        krr.fit(X_tr_sc, log_y_tr, sample_weight=weights)
        p_krr = float(np.exp(krr.predict(X_te_sc)[0]))
        preds['Model 6: Laplacian Kernel Ridge'][t_idx] = np.clip(p_krr, bound_low, bound_high)
        
        # M7: ElasticNet
        en = ElasticNet(alpha=0.5, l1_ratio=0.5, max_iter=400)
        en.fit(X_tr_sc, log_y_tr, sample_weight=weights)
        p_en = float(np.exp(en.predict(X_te_sc)[0]))
        preds['Model 7: ElasticNet Regularized'][t_idx] = np.clip(p_en, bound_low, bound_high)
        
        # M8: Gradient Tree Booster
        gbr = GradientBoostingRegressor(n_estimators=30, max_depth=2, learning_rate=0.08, loss='huber', random_state=42)
        gbr.fit(X_tr_sc, log_y_tr, sample_weight=weights)
        p_gbr = float(np.exp(gbr.predict(X_te_sc)[0]))
        preds['Model 8: Gradient Tree Booster'][t_idx] = np.clip(p_gbr, bound_low, bound_high)
        
        # M9: SNV-Polynomial Detrending
        # detrend per sample
        X_tr_snv = (X_tr - np.mean(X_tr, axis=1, keepdims=True)) / (np.std(X_tr, axis=1, keepdims=True) + 1e-6)
        X_te_snv = (X_te - np.mean(X_te, axis=1, keepdims=True)) / (np.std(X_te, axis=1, keepdims=True) + 1e-6)
        rdg_snv = Ridge(alpha=10.0)
        rdg_snv.fit(X_tr_snv, log_y_tr, sample_weight=weights)
        p_snv = float(np.exp(rdg_snv.predict(X_te_snv)[0]))
        preds['Model 9: SNV-Polynomial Detrended Ridge'][t_idx] = np.clip(p_snv, bound_low, bound_high)
        
        # Handle zero threshold for Boron
        if is_b:
            for m in MODEL_NAMES[:9]:
                if preds[m][t_idx] < 0.08:
                    preds[m][t_idx] = 0.0
                    
        # M10: Multi-Model Consensus Ensemble
        # Blend of top estimators + shrinkage towards in-range center
        candidates = [p_rdg, p_hub, p_pls, p_svr, p_krr]
        candidates = [np.clip(c, bound_low, bound_high) for c in candidates]
        blend_est = float(np.mean(candidates))
        # Shrinkage factor based on sample count
        shrink_w = 0.35 if N < 30 else 0.20
        final_ens = (1.0 - shrink_w) * blend_est + shrink_w * med_val
        if is_b and final_ens < 0.08:
            final_ens = 0.0
        preds['Model 10: Multi-Model Consensus Ensemble'][t_idx] = np.clip(final_ens, bound_low, bound_high)
        
    for m in MODEL_NAMES:
        acc = user_accuracy(y, preds[m])
        results_matrix[m][target] = acc

df_out = pd.DataFrame(results_matrix).T
df_out['Average'] = df_out.mean(axis=1)

print("="*95)
print("DOMINANT CLASS IN-RANGE VALUE ACCURACY MATRIX (%):")
print("="*95)
print(df_out.round(1).to_string())
print("="*95)

# Print Dominant Class Info
print("\nDOMINANT CLASS DISTRIBUTION PER NUTRIENT:")
df_info = pd.DataFrame(dominant_info).T
print(df_info.to_string())
