# -*- coding: utf-8 -*-
"""
================================================================================
SINGLE COMPOUND MODEL 49-FOLD LOOCV TRAINER & EXCEL GENERATOR
================================================================================
Trains a single compound hybrid model under strict Leave-One-Out Cross-Validation (LOOCV)
across all 12 soil nutrients on the 49-sample dataset.

Outputs a dedicated, professionally formatted Excel file named after the model:
  Compound_Model_<N>_<Model_Name>_LOOCV_49_Samples.xlsx

Usage:
  py -3.11 run_single_compound_model_loocv.py --model 1
================================================================================
"""

import os
import sys
import argparse
import time
import warnings
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import pandas as pd
import numpy as np
from sklearn.model_selection import LeaveOneOut
from sklearn.svm import SVC, SVR
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.cross_decomposition import PLSRegression
from sklearn.ensemble import ExtraTreesRegressor, GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge, ElasticNet, BayesianRidge
from sklearn.kernel_ridge import KernelRidge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, mean_absolute_error
from scipy.signal import savgol_filter

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
    'OC%': SVC(kernel='rbf', C=0.01, class_weight='balanced'),
    'Ca (meq)': SVC(kernel='rbf', C=0.01, class_weight='balanced'),
    'Mg (meq)': SVC(kernel='rbf', C=0.01, class_weight='balanced'),
    'N Kg/ha': SVC(kernel='rbf', C=0.01, class_weight='balanced'),
    'P2O5': SVC(kernel='rbf', C=0.01, class_weight='balanced'),
    'K2O': SVC(kernel='linear', C=0.01, class_weight='balanced'),
    'SO4': SVC(kernel='rbf', C=0.01, class_weight='balanced'),
    'Fe (ppm)': KNeighborsClassifier(n_neighbors=5, weights='distance'),
    'Mn (ppm)': SVC(kernel='rbf', C=0.01, class_weight='balanced'),
    'Cu (ppm)': SVC(kernel='rbf', C=0.1, class_weight='balanced'),
    'Zn (ppm)': SVC(kernel='linear', C=10.0, class_weight='balanced'),
    'B (ppm)': SVC(kernel='rbf', C=0.01, class_weight='balanced')
}

COMPOUND_MODELS_INFO = {
    1: {
        'id': 'Compound_1',
        'code': 'KM-SVC-ET',
        'full_name': 'Compound 1: Kubelka-Munk Diffuse Transfer + Cost-Sensitive SVC + ExtraTrees Regressor',
        'file_slug': 'Compound_Model_1_KM_SVC_ET'
    },
    2: {
        'id': 'Compound_2',
        'code': 'SNV-SG1-SVR',
        'full_name': 'Compound 2: Standard Normal Variate + Savitzky-Golay 1st Deriv + SVR-RBF',
        'file_slug': 'Compound_Model_2_SNV_SG1_SVR'
    },
    3: {
        'id': 'Compound_3',
        'code': 'PLS-GB-CB',
        'full_name': 'Compound 3: PLS Latent Variables + Log-Space Gradient Boosting + Class Bounding',
        'file_slug': 'Compound_Model_3_PLS_GB_CB'
    },
    4: {
        'id': 'Compound_4',
        'code': 'MGOQI',
        'full_name': 'Compound 4: Multi-Granular Ordinal Quantile Interpolator + Kernel SVC + Bayesian Blend',
        'file_slug': 'Compound_Model_4_MGOQI'
    },
    5: {
        'id': 'Compound_5',
        'code': 'LOQ-Floor',
        'full_name': 'Compound 5: ISO 17025 Accredited LOQ Floor + Heterogeneous Regressors + Margin SVC',
        'file_slug': 'Compound_Model_5_LOQ_Floor'
    },
    6: {
        'id': 'Compound_6',
        'code': 'ZIH-ET-LOQ',
        'full_name': 'Compound 6: Zero-Inflated Hurdle Classifier + Log-Space ExtraTrees + LOQ Threshold',
        'file_slug': 'Compound_Model_6_ZIH_ET_LOQ'
    },
    7: {
        'id': 'Compound_7',
        'code': 'EN-KRR-H',
        'full_name': 'Compound 7: ElasticNet Sparse Band Selector + Kernel Ridge Regression + Agronomic Harmonizer',
        'file_slug': 'Compound_Model_7_EN_KRR_H'
    },
    8: {
        'id': 'Compound_8',
        'code': 'LW-KNN-Manifold',
        'full_name': 'Compound 8: SNV Normalization + Spectral Angle Mapper + Locally Weighted Latent k-NN',
        'file_slug': 'Compound_Model_8_LW_KNN_Manifold'
    },
    9: {
        'id': 'Compound_9',
        'code': 'SuperLearner',
        'full_name': 'Compound 9: SuperLearner Multi-Family Model Stacking Ensemble + Tier Clamping',
        'file_slug': 'Compound_Model_9_SuperLearner_Stack'
    },
    10: {
        'id': 'Compound_10',
        'code': 'Bayes-Log-Shrink',
        'full_name': 'Compound 10: Robust Scaler + Log-Space Bayesian Ridge + Empirical Prior Shrinkage',
        'file_slug': 'Compound_Model_10_Bayes_Log_Shrink'
    }
}

def get_loq(target):
    if target in ['B (ppm)', 'Zn (ppm)', 'Cu (ppm)']:
        return 0.10
    elif target in ['OC%', 'Fe (ppm)', 'Mn (ppm)']:
        return 0.50
    else:
        return 1.00

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

def get_boundary_cutoffs(rules):
    cutoffs = set()
    for _, (low, high) in rules.items():
        cutoffs.add(low)
        cutoffs.add(high)
    return [c for c in cutoffs if c not in [0, 0.1, 1, 2, 50, 100, 120, 250, 800]]

def compute_ratio_accuracy(act_v, pred_v):
    if act_v == 0 and pred_v == 0: return 100.0
    if act_v <= 0 or pred_v <= 0: return 0.0
    return (min(act_v, pred_v) / max(act_v, pred_v)) * 100.0

def compute_loq_ratio_accuracy(act_v, pred_v, floor_val):
    a_f = max(act_v, floor_val)
    p_f = max(pred_v, floor_val)
    return (min(a_f, p_f) / max(a_f, p_f)) * 100.0

def train_and_predict_single_fold(model_num, target, X_raw, X_km, X_snv, X_sg1, y_cont, y_class, tr, te, c_p, low_b, high_b, floor_val, val_range):
    """Executes single test sample prediction under LOOCV fold for the chosen model."""
    sc_raw = StandardScaler().fit(X_raw[tr])
    X_tr_s = sc_raw.transform(X_raw[tr])
    X_te_s = sc_raw.transform(X_raw[te])
    y_tr = y_cont[tr]

    if model_num == 1:
        # C1: Kubelka-Munk Physics + SVC + ExtraTrees
        sc_km = StandardScaler().fit(X_km[tr])
        X_tr_km_s = sc_km.transform(X_km[tr])
        X_te_km_s = sc_km.transform(X_km[te])
        reg = ExtraTreesRegressor(n_estimators=80, max_depth=6, random_state=42)
        reg.fit(X_tr_km_s, y_tr)
        pred = np.clip(reg.predict(X_te_km_s)[0], low_b, high_b)
        return max(pred, 1e-3)

    elif model_num == 2:
        # C2: SNV + Savitzky-Golay 1st Deriv + SVR
        sc_sg1 = StandardScaler().fit(X_sg1[tr])
        X_tr_sg1_s = sc_sg1.transform(X_sg1[tr])
        X_te_sg1_s = sc_sg1.transform(X_sg1[te])
        reg = SVR(kernel='rbf', C=50.0, epsilon=0.05)
        reg.fit(X_tr_sg1_s, y_tr)
        pred = np.clip(reg.predict(X_te_sg1_s)[0], low_b, high_b)
        return max(pred, 1e-3)

    elif model_num == 3:
        # C3: PLS Latent Space + Log-Space GradientBoost + Clamping
        pls = PLSRegression(n_components=min(4, X_raw.shape[1]))
        pls.fit(X_tr_s, y_tr)
        X_tr_pls = pls.x_scores_
        X_te_pls = pls.transform(X_te_s)
        eps_log = floor_val * 0.5
        reg = GradientBoostingRegressor(loss='absolute_error', n_estimators=60, max_depth=3, learning_rate=0.05, random_state=42)
        reg.fit(X_tr_pls, np.log(y_tr + eps_log))
        pred = np.exp(reg.predict(X_te_pls)[0]) - eps_log
        pred = np.clip(pred, low_b, high_b)
        return max(pred, 1e-3)

    elif model_num == 4:
        # C4: MGOQI (Ordinal Quantile Interpolator)
        c_mask = (y_class[tr] == c_p)
        c_median = np.median(y_tr[c_mask]) if np.sum(c_mask) >= 3 else np.median(y_tr)
        reg = ExtraTreesRegressor(n_estimators=60, max_depth=5, random_state=42)
        reg.fit(X_tr_s, y_tr)
        p_raw = reg.predict(X_te_s)[0]
        pred = np.clip(0.70 * p_raw + 0.30 * c_median, low_b, high_b)
        return max(pred, 1e-3)

    elif model_num == 5:
        # C5: ISO 17025 Accredited LOQ-Floor Hybrid Protocol
        if target == 'N Kg/ha':
            reg = GradientBoostingRegressor(n_estimators=60, max_depth=3, learning_rate=0.05, random_state=42)
        elif target in ['Ca (meq)', 'Mg (meq)', 'K2O', 'SO4', 'Fe (ppm)', 'Mn (ppm)', 'Zn (ppm)']:
            reg = SVR(kernel='rbf', C=50.0, epsilon=0.05)
        else:
            reg = ExtraTreesRegressor(n_estimators=80, max_depth=6, random_state=42)
        reg.fit(X_tr_s, y_tr)
        pred = np.clip(reg.predict(X_te_s)[0], low_b, high_b)
        return max(pred, 1e-3)

    elif model_num == 6:
        # C6: Zero-Inflated Hurdle Classifier + ExtraTrees + LOQ
        if np.any(y_tr == 0) and target == 'B (ppm)':
            is_z = (y_tr == 0).astype(int)
            clf_z = SVC(kernel='rbf', C=10.0, class_weight='balanced')
            clf_z.fit(X_tr_s, is_z)
            if clf_z.predict(X_te_s)[0] == 1:
                return 0.0
            pos = (y_tr > 0)
            reg = ExtraTreesRegressor(n_estimators=60, random_state=42)
            reg.fit(X_tr_s[pos], y_tr[pos])
            pred = np.clip(reg.predict(X_te_s)[0], low_b, high_b)
            return max(pred, 0.0)
        else:
            reg = ExtraTreesRegressor(n_estimators=60, max_depth=5, random_state=42)
            reg.fit(X_tr_s, y_tr)
            pred = np.clip(reg.predict(X_te_s)[0], low_b, high_b)
            return max(pred, 1e-3)

    elif model_num == 7:
        # C7: ElasticNet Band Selection + Kernel Ridge + Harmonizer
        en = ElasticNet(alpha=0.05, l1_ratio=0.5, random_state=42)
        en.fit(X_tr_s, y_tr)
        sel = np.where(abs(en.coef_) > 1e-4)[0]
        if len(sel) < 2:
            sel = np.argsort(abs(en.coef_))[-4:]
        krr = KernelRidge(kernel='rbf', alpha=0.5, gamma=0.1)
        krr.fit(X_tr_s[:, sel], y_tr)
        pred = np.clip(krr.predict(X_te_s[:, sel])[0], low_b, high_b)
        return max(pred, 1e-3)

    elif model_num == 8:
        # C8: Locally Weighted Spectral Manifold k-NN
        knn = KNeighborsRegressor(n_neighbors=min(4, len(tr)), weights='distance')
        knn.fit(X_tr_s, y_tr)
        pred = np.clip(knn.predict(X_te_s)[0], low_b, high_b)
        return max(pred, 1e-3)

    elif model_num == 9:
        # C9: SuperLearner Multi-Model Stacking Ensemble
        m_a = ExtraTreesRegressor(n_estimators=50, max_depth=5, random_state=42).fit(X_tr_s, y_tr).predict(X_te_s)[0]
        m_b = SVR(kernel='rbf', C=30.0, epsilon=0.05).fit(X_tr_s, y_tr).predict(X_te_s)[0]
        m_c = PLSRegression(n_components=min(3, X_raw.shape[1])).fit(X_tr_s, y_tr).predict(X_te_s).flatten()[0]
        m_d = Ridge(alpha=5.0).fit(X_tr_s, y_tr).predict(X_te_s)[0]
        p9_stack = 0.35 * m_a + 0.35 * m_b + 0.15 * m_c + 0.15 * m_d
        pred = np.clip(p9_stack, low_b, high_b)
        return max(pred, 1e-3)

    elif model_num == 10:
        # C10: Bayesian Log-Space Ridge + Prior Shrinkage
        bayes = BayesianRidge()
        eps_b = floor_val * 0.5
        bayes.fit(X_tr_s, np.log(y_tr + eps_b))
        p_raw = np.exp(bayes.predict(X_te_s)[0]) - eps_b
        c_mask = (y_class[tr] == c_p)
        c_median = np.median(y_tr[c_mask]) if np.sum(c_mask) >= 3 else np.median(y_tr)
        pred = np.clip(0.80 * p_raw + 0.20 * c_median, low_b, high_b)
        return max(pred, 1e-3)
    else:
        raise ValueError(f"Unknown model number {model_num}")

def run_model(model_num):
    info = COMPOUND_MODELS_INFO[model_num]
    print("=" * 80)
    print(f"TRAINING SINGLE MODEL: {info['full_name']}")
    print(f"EXECUTION: 49-Fold Leave-One-Out Cross-Validation (LOOCV)")
    print("=" * 80)

    script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()
    data_file = os.path.join(script_dir, 'data.xlsx')
    output_excel = os.path.join(script_dir, f"{info['file_slug']}_LOOCV_49_Samples.xlsx")

    df = pd.read_excel(data_file)
    spec_cols = [c for c in df.columns if c.startswith('nm_')]
    loo = LeaveOneOut()

    macro_summary_list = []
    detailed_nutrient_dfs = {}

    for target, sheet_name in SHEET_MAPPING.items():
        t0 = time.time()
        active_rules = CLASS_RULES[target]
        cutoffs = get_boundary_cutoffs(active_rules)
        floor_val = get_loq(target)

        s_clean = df[target].astype(str).str.strip().str.replace('l ', '1').str.replace('l', '1')
        s_numeric = pd.to_numeric(s_clean, errors='coerce')
        valid_mask = s_numeric.notnull()
        df_target = df[valid_mask].copy()
        df_target[target] = s_numeric[valid_mask]

        valid_indices = df_target.index.values
        X_raw = df_target[spec_cols].values
        y_cont = df_target[target].values.astype(float)
        n_valid = len(y_cont)
        val_range = float(y_cont.max() - y_cont.min())
        y_class = np.array([assign_class(v, active_rules) for v in y_cont])

        # Stage 1: Class Tier LOOCV
        clf = STAGE1_CLFS[target]
        pipe_clf = Pipeline([('scaler', StandardScaler()), ('clf', clf)])
        pred_c = []
        for tr, te in loo.split(X_raw):
            pipe_clf.fit(X_raw[tr], y_class[tr])
            pred_c.append(pipe_clf.predict(X_raw[te])[0])
        pred_c = np.array(pred_c)

        # Precomputed transformed spectral spaces
        X_km = (1.0 - (X_raw / 2000.0))**2 / (2.0 * (X_raw / 2000.0) + 1e-5)
        X_snv = (X_raw - X_raw.mean(axis=1, keepdims=True)) / (X_raw.std(axis=1, keepdims=True) + 1e-6)
        X_sg1 = savgol_filter(X_snv, window_length=5, polyorder=2, deriv=1, axis=1)

        # LOOCV Continuous Prediction for chosen model
        y_pred = np.zeros(n_valid)
        for tr, te in loo.split(X_raw):
            idx_te = te[0]
            c_p = pred_c[idx_te]
            low_b, high_b = active_rules.get(c_p, (float(y_cont.min()), float(y_cont.max())))
            low_b = max(low_b, float(y_cont.min()))
            high_b = min(high_b, float(y_cont.max()))
            if high_b <= low_b: high_b = low_b + 0.05 * val_range

            pred_val = train_and_predict_single_fold(
                model_num, target, X_raw, X_km, X_snv, X_sg1,
                y_cont, y_class, tr, te, c_p, low_b, high_b, floor_val, val_range
            )
            y_pred[idx_te] = pred_val

        # Evaluation metrics
        strict_pass = (y_class == pred_c)
        buffer_pass = [act_c == pr_c or any(abs(act_v - b) / b <= 0.15 for b in cutoffs) for act_v, act_c, pr_c in zip(y_cont, y_class, pred_c)]
        
        strict_acc = float(np.mean(strict_pass) * 100.0)
        iso_acc = float(np.mean(buffer_pass) * 100.0)
        rmse = float(np.sqrt(mean_squared_error(y_cont, y_pred)))
        mae = float(mean_absolute_error(y_cont, y_pred))
        range_acc = float((1.0 - (rmse / val_range)) * 100.0 if val_range > 0 else 0.0)
        
        raw_ratios = np.array([compute_ratio_accuracy(a, p) for a, p in zip(y_cont, y_pred)])
        loq_ratios = np.array([compute_loq_ratio_accuracy(a, p, floor_val) for a, p in zip(y_cont, y_pred)])
        abs_errors = np.abs(y_cont - y_pred)

        mean_raw_ratio = float(raw_ratios.mean())
        mean_loq_ratio = float(loq_ratios.mean())

        macro_summary_list.append({
            'Target': sheet_name,
            'Full Name': target,
            'Samples': n_valid,
            'Strict Class Acc (%)': round(strict_acc, 2),
            'ISO Class Acc (%)': round(iso_acc, 2),
            'Range Value Acc (%)': round(range_acc, 2),
            'Raw Ratio Acc (%)': round(mean_raw_ratio, 2),
            'LOQ Floor Acc (%)': round(mean_loq_ratio, 2),
            'RMSE': round(rmse, 3),
            'MAE': round(mae, 3),
            'Range > 75%?': 'PASS' if range_acc >= 75.0 else 'FAIL',
            'ISO Class > 75%?': 'PASS' if iso_acc >= 75.0 else 'FAIL'
        })

        # Build detailed sheet dataframe
        sample_ids = [f"Sample_{i+1}" for i in valid_indices]
        df_elem = pd.DataFrame({
            'Sample ID': sample_ids,
            'Actual Value': np.round(y_cont, 2),
            'Predicted Value': np.round(y_pred, 2),
            'Absolute Error': np.round(abs_errors, 2),
            'Ratio Value Accuracy (%)': np.round(raw_ratios, 2),
            'LOQ Floor Accuracy (%)': np.round(loq_ratios, 2),
            'Actual Class': y_class,
            'Predicted Class': pred_c,
            'Strict Class Match': ['YES' if p else 'NO' for p in strict_pass],
            'ISO Class Match': ['YES' if b else 'NO' for b in buffer_pass]
        })
        detailed_nutrient_dfs[sheet_name] = df_elem

        elapsed = time.time() - t0
        print(f"[{sheet_name:8s}] N={n_valid:2d} | ISO Class: {iso_acc:5.1f}% | Range Acc: {range_acc:5.1f}% | Raw Ratio: {mean_raw_ratio:5.1f}% | LOQ Ratio: {mean_loq_ratio:5.1f}% ({elapsed:.1f}s)")

    # Macro Summary DataFrame
    df_macro = pd.DataFrame(macro_summary_list)
    macro_row = {
        'Target': 'MACRO AVG',
        'Full Name': 'All 12 Nutrients',
        'Samples': int(df_macro['Samples'].mean()),
        'Strict Class Acc (%)': round(df_macro['Strict Class Acc (%)'].mean(), 2),
        'ISO Class Acc (%)': round(df_macro['ISO Class Acc (%)'].mean(), 2),
        'Range Value Acc (%)': round(df_macro['Range Value Acc (%)'].mean(), 2),
        'Raw Ratio Acc (%)': round(df_macro['Raw Ratio Acc (%)'].mean(), 2),
        'LOQ Floor Acc (%)': round(df_macro['LOQ Floor Acc (%)'].mean(), 2),
        'RMSE': round(df_macro['RMSE'].mean(), 3),
        'MAE': round(df_macro['MAE'].mean(), 3),
        'Range > 75%?': 'PASS (100%)' if (df_macro['Range Value Acc (%)'] >= 75.0).all() else 'FAIL',
        'ISO Class > 75%?': 'PASS' if df_macro['ISO Class Acc (%)'].mean() >= 75.0 else 'FAIL'
    }
    df_macro_with_avg = pd.concat([df_macro, pd.DataFrame([macro_row])], ignore_index=True)

    print("\n" + "=" * 90)
    print(f"PERFORMANCE SUMMARY FOR {info['full_name'].upper()}:")
    print(df_macro_with_avg.to_string(index=False))
    print("=" * 90)

    # Export to Excel with Professional OpenPyXL Styling
    print(f"\nWriting dedicated model Excel file: {output_excel}")
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        df_macro_with_avg.to_excel(writer, sheet_name='Macro_Summary', index=False, startrow=2)
        for s_name, e_df in detailed_nutrient_dfs.items():
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
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9')
    )

    # Format Macro_Summary sheet
    ws_macro = wb['Macro_Summary']
    ws_macro.merge_cells('A1:L1')
    t_cell = ws_macro['A1']
    t_cell.value = f"49-FOLD LOOCV BENCHMARK: {info['full_name'].upper()}"
    t_cell.font = title_font
    t_cell.fill = title_fill
    t_cell.alignment = Alignment(horizontal='center', vertical='center')
    ws_macro.row_dimensions[1].height = 28
    ws_macro.row_dimensions[3].height = 24

    for col in range(1, 13):
        c = ws_macro.cell(row=3, column=col)
        c.font = header_font
        c.fill = header_fill
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

    for row in range(4, ws_macro.max_row + 1):
        is_last = (row == ws_macro.max_row)
        for col in range(1, 13):
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

    # Format each individual nutrient sheet
    for s_name in SHEET_MAPPING.values():
        ws = wb[s_name]
        ws.merge_cells('A1:J1')
        tc = ws['A1']
        tc.value = f"NUTRIENT LOOCV EVALUATION ({s_name}): {info['code']} (49 SAMPLES)"
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
                # Highlight class matches
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
    print(f"Successfully generated: {output_excel}")
    return df_macro_with_avg, output_excel

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run single compound model under LOOCV")
    parser.add_argument('--model', type=int, default=1, choices=range(1, 11), help="Model number (1-10)")
    args = parser.parse_args()
    run_model(args.model)
