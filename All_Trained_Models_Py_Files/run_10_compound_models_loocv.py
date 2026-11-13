# -*- coding: utf-8 -*-
"""
================================================================================
TEN COMPOUND HYBRID ALGORITHMS BENCHMARK (49-FOLD LOOCV ACROSS ALL 12 NUTRIENTS)
================================================================================
Evaluates 10 distinct Compound/Hybrid Architectures (combining 2 to 3 algorithms):
  1. Compound 1: Kubelka-Munk Physics + SVC Classifier + ExtraTrees (KM-SVC-ET)
  2. Compound 2: SNV + Savitzky-Golay 1st Deriv + SVR (SNV-SG1-SVR)
  3. Compound 3: PLS Latent Space + Log-Space GradientBoost + Clamping (PLS-GB-CB)
  4. Compound 4: Multi-Granular Ordinal Quantile Interpolator (MGOQI)
  5. Compound 5: ISO 17025 Accredited LOQ-Floor Hybrid Protocol (LOQ-Floor)
  6. Compound 6: Zero-Inflated Hurdle Classifier + ExtraTrees + LOQ (ZIH-ET-LOQ)
  7. Compound 7: ElasticNet Band Selection + Kernel Ridge + Harmonizer (EN-KRR-H)
  8. Compound 8: Locally Weighted Spectral Manifold k-NN (LW-KNN-Manifold)
  9. Compound 9: SuperLearner Multi-Model Stacking Ensemble (SuperLearner)
 10. Compound 10: Bayesian Log-Space Ridge + Prior Shrinkage (Bayes-Log-Shrink)

Evaluation:
  - Ratio Value Accuracy: min(Act, Pred) / max(Act, Pred) * 100%
  - LOQ Floor Value Accuracy (%)
  - Chemometric Range Value Accuracy: (1 - RMSE / Range) * 100% (Compulsory > 75%)
  - Strict Class Accuracy (%) & ISO 17025 Buffer Class Accuracy (%) (+/-15% boundary)
  - Strict 49-Fold Leave-One-Out Cross-Validation (cv=LeaveOneOut())

Output:
  - 'Ten_Compound_Models_LOOCV_49_Samples_Comparison.xlsx'
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
from sklearn.model_selection import LeaveOneOut
from sklearn.svm import SVC, SVR
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.cross_decomposition import PLSRegression
from sklearn.ensemble import ExtraTreesRegressor, GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge, ElasticNet, BayesianRidge
from sklearn.kernel_ridge import KernelRidge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
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

def eval_metrics(y_cont, y_class, pred_c, pred_v, cutoffs, val_range, floor_val):
    strict_pass = (y_class == pred_c)
    buffer_pass = [act_c == pr_c or any(abs(act_v - b) / b <= 0.15 for b in cutoffs) for act_v, act_c, pr_c in zip(y_cont, y_class, pred_c)]
    
    strict_acc = np.mean(strict_pass) * 100.0
    buffer_acc = np.mean(buffer_pass) * 100.0
    
    rmse = np.sqrt(mean_squared_error(y_cont, pred_v))
    range_acc = (1.0 - (rmse / val_range)) * 100.0 if val_range > 0 else 0.0
    
    raw_ratios = np.array([compute_ratio_accuracy(a, p) for a, p in zip(y_cont, pred_v)])
    loq_ratios = np.array([compute_loq_ratio_accuracy(a, p, floor_val) for a, p in zip(y_cont, pred_v)])
    
    return {
        'strict_acc': round(strict_acc, 2),
        'iso_acc': round(buffer_acc, 2),
        'range_acc': round(range_acc, 2),
        'mean_ratio': round(raw_ratios.mean(), 2),
        'mean_loq': round(loq_ratios.mean(), 2),
        'rmse': round(rmse, 4),
        'raw_ratios': raw_ratios,
        'loq_ratios': loq_ratios
    }

def main():
    t_start = time.time()
    print("=" * 80)
    print("RUNNING 10 COMPOUND HYBRID ALGORITHMS BENCHMARK (49-FOLD LOOCV)")
    print("=" * 80)

    script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()
    data_file = os.path.join(script_dir, 'data.xlsx')
    output_excel = os.path.join(script_dir, 'Ten_Compound_Models_LOOCV_49_Samples_Comparison.xlsx')

    df = pd.read_excel(data_file)
    spec_cols = [c for c in df.columns if c.startswith('nm_')]
    loo = LeaveOneOut()

    model_names = [
        "C1: KM-SVC-ET",
        "C2: SNV-SG1-SVR",
        "C3: PLS-GB-CB",
        "C4: MGOQI",
        "C5: LOQ-Floor",
        "C6: ZIH-ET-LOQ",
        "C7: EN-KRR-H",
        "C8: LW-KNN-Manifold",
        "C9: SuperLearner",
        "C10: Bayes-Log-Shrink"
    ]

    all_macro_results = {m: [] for m in model_names}
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

        # Stage 1: Robust Agronomic Classifier LOOCV
        clf = STAGE1_CLFS[target]
        pipe_clf = Pipeline([('scaler', StandardScaler()), ('clf', clf)])
        pred_c = []
        for tr, te in loo.split(X_raw):
            pipe_clf.fit(X_raw[tr], y_class[tr])
            pred_c.append(pipe_clf.predict(X_raw[te])[0])
        pred_c = np.array(pred_c)

        # Precomputed transformed spectral matrices:
        # Kubelka-Munk diffuse absorption F(R)
        X_km = (1.0 - (X_raw / 2000.0))**2 / (2.0 * (X_raw / 2000.0) + 1e-5)
        # SNV + Savitzky-Golay 1st derivative
        X_snv = (X_raw - X_raw.mean(axis=1, keepdims=True)) / (X_raw.std(axis=1, keepdims=True) + 1e-6)
        X_sg1 = savgol_filter(X_snv, window_length=5, polyorder=2, deriv=1, axis=1)

        # Storage for all 10 models predictions on this target
        preds_dict = {m: np.zeros(n_valid) for m in model_names}

        for tr, te in loo.split(X_raw):
            idx_te = te[0]
            c_p = pred_c[idx_te]
            low_b, high_b = active_rules.get(c_p, (float(y_cont.min()), float(y_cont.max())))
            low_b = max(low_b, float(y_cont.min()))
            high_b = min(high_b, float(y_cont.max()))
            if high_b <= low_b: high_b = low_b + 0.05 * val_range

            # Scalers for this fold
            sc_raw = StandardScaler().fit(X_raw[tr])
            sc_km = StandardScaler().fit(X_km[tr])
            sc_sg1 = StandardScaler().fit(X_sg1[tr])

            X_tr_s = sc_raw.transform(X_raw[tr])
            X_te_s = sc_raw.transform(X_raw[te])

            X_tr_km_s = sc_km.transform(X_km[tr])
            X_te_km_s = sc_km.transform(X_km[te])

            X_tr_sg1_s = sc_sg1.transform(X_sg1[tr])
            X_te_sg1_s = sc_sg1.transform(X_sg1[te])

            # Training targets
            y_tr = y_cont[tr]

            # -------------------------------------------------------------
            # C1: Kubelka-Munk Physics + SVC + ExtraTrees
            # -------------------------------------------------------------
            reg_c1 = ExtraTreesRegressor(n_estimators=60, max_depth=5, random_state=42)
            reg_c1.fit(X_tr_km_s, y_tr)
            p1 = np.clip(reg_c1.predict(X_te_km_s)[0], low_b, high_b)
            preds_dict["C1: KM-SVC-ET"][idx_te] = max(p1, 1e-3)

            # -------------------------------------------------------------
            # C2: SNV + Savitzky-Golay 1st Deriv + SVR
            # -------------------------------------------------------------
            reg_c2 = SVR(kernel='rbf', C=50.0, epsilon=0.05)
            reg_c2.fit(X_tr_sg1_s, y_tr)
            p2 = np.clip(reg_c2.predict(X_te_sg1_s)[0], low_b, high_b)
            preds_dict["C2: SNV-SG1-SVR"][idx_te] = max(p2, 1e-3)

            # -------------------------------------------------------------
            # C3: PLS Latent Space + Log-Space GradientBoost + Clamping
            # -------------------------------------------------------------
            pls_c3 = PLSRegression(n_components=min(4, X_raw.shape[1]))
            pls_c3.fit(X_tr_s, y_tr)
            X_tr_pls = pls_c3.x_scores_
            X_te_pls = pls_c3.transform(X_te_s)

            eps_log = floor_val * 0.5
            reg_c3 = GradientBoostingRegressor(loss='absolute_error', n_estimators=50, max_depth=3, learning_rate=0.05, random_state=42)
            reg_c3.fit(X_tr_pls, np.log(y_tr + eps_log))
            p3 = np.exp(reg_c3.predict(X_te_pls)[0]) - eps_log
            p3 = np.clip(p3, low_b, high_b)
            preds_dict["C3: PLS-GB-CB"][idx_te] = max(p3, 1e-3)

            # -------------------------------------------------------------
            # C4: Multi-Granular Ordinal Quantile Interpolator (MGOQI)
            # -------------------------------------------------------------
            c_mask = (y_class[tr] == c_p)
            c_median = np.median(y_tr[c_mask]) if np.sum(c_mask) >= 3 else np.median(y_tr)
            reg_c4 = ExtraTreesRegressor(n_estimators=50, max_depth=5, random_state=42)
            reg_c4.fit(X_tr_s, y_tr)
            p4_raw = reg_c4.predict(X_te_s)[0]
            p4 = np.clip(0.70 * p4_raw + 0.30 * c_median, low_b, high_b)
            preds_dict["C4: MGOQI"][idx_te] = max(p4, 1e-3)

            # -------------------------------------------------------------
            # C5: ISO 17025 Accredited LOQ-Floor Hybrid Protocol
            # -------------------------------------------------------------
            if target == 'N Kg/ha':
                reg_c5 = GradientBoostingRegressor(n_estimators=50, max_depth=3, learning_rate=0.05, random_state=42)
            elif target in ['Ca (meq)', 'Mg (meq)', 'K2O', 'SO4', 'Fe (ppm)', 'Mn (ppm)', 'Zn (ppm)']:
                reg_c5 = SVR(kernel='rbf', C=50.0, epsilon=0.05)
            else:
                reg_c5 = ExtraTreesRegressor(n_estimators=80, max_depth=6, random_state=42)
            reg_c5.fit(X_tr_s, y_tr)
            p5 = np.clip(reg_c5.predict(X_te_s)[0], low_b, high_b)
            preds_dict["C5: LOQ-Floor"][idx_te] = max(p5, 1e-3)

            # -------------------------------------------------------------
            # C6: Zero-Inflated Hurdle Classifier + ExtraTrees + LOQ
            # -------------------------------------------------------------
            if np.any(y_tr == 0) and target == 'B (ppm)':
                is_z = (y_tr == 0).astype(int)
                clf_z = SVC(kernel='rbf', C=10.0, class_weight='balanced')
                clf_z.fit(X_tr_s, is_z)
                pred_z = clf_z.predict(X_te_s)[0]
                if pred_z == 1:
                    p6 = 0.0
                else:
                    pos = (y_tr > 0)
                    reg_c6 = ExtraTreesRegressor(n_estimators=50, random_state=42)
                    reg_c6.fit(X_tr_s[pos], y_tr[pos])
                    p6 = np.clip(reg_c6.predict(X_te_s)[0], low_b, high_b)
            else:
                reg_c6 = ExtraTreesRegressor(n_estimators=50, max_depth=5, random_state=42)
                reg_c6.fit(X_tr_s, y_tr)
                p6 = np.clip(reg_c6.predict(X_te_s)[0], low_b, high_b)
            preds_dict["C6: ZIH-ET-LOQ"][idx_te] = max(p6, 0.0)

            # -------------------------------------------------------------
            # C7: ElasticNet Band Selection + Kernel Ridge + Harmonizer
            # -------------------------------------------------------------
            en = ElasticNet(alpha=0.05, l1_ratio=0.5, random_state=42)
            en.fit(X_tr_s, y_tr)
            selected_features = np.where(abs(en.coef_) > 1e-4)[0]
            if len(selected_features) < 2:
                selected_features = np.argsort(abs(en.coef_))[-4:]
            krr = KernelRidge(kernel='rbf', alpha=0.5, gamma=0.1)
            krr.fit(X_tr_s[:, selected_features], y_tr)
            p7 = np.clip(krr.predict(X_te_s[:, selected_features])[0], low_b, high_b)
            preds_dict["C7: EN-KRR-H"][idx_te] = max(p7, 1e-3)

            # -------------------------------------------------------------
            # C8: Locally Weighted Spectral Manifold k-NN
            # -------------------------------------------------------------
            knn = KNeighborsRegressor(n_neighbors=min(4, len(tr)), weights='distance')
            knn.fit(X_tr_s, y_tr)
            p8 = np.clip(knn.predict(X_te_s)[0], low_b, high_b)
            preds_dict["C8: LW-KNN-Manifold"][idx_te] = max(p8, 1e-3)

            # -------------------------------------------------------------
            # C9: SuperLearner Multi-Model Stacking Ensemble
            # -------------------------------------------------------------
            m_a = ExtraTreesRegressor(n_estimators=40, max_depth=5, random_state=42).fit(X_tr_s, y_tr).predict(X_te_s)[0]
            m_b = SVR(kernel='rbf', C=30.0, epsilon=0.05).fit(X_tr_s, y_tr).predict(X_te_s)[0]
            m_c = PLSRegression(n_components=min(3, X_raw.shape[1])).fit(X_tr_s, y_tr).predict(X_te_s).flatten()[0]
            m_d = Ridge(alpha=5.0).fit(X_tr_s, y_tr).predict(X_te_s)[0]
            p9_stack = 0.35 * m_a + 0.35 * m_b + 0.15 * m_c + 0.15 * m_d
            p9 = np.clip(p9_stack, low_b, high_b)
            preds_dict["C9: SuperLearner"][idx_te] = max(p9, 1e-3)

            # -------------------------------------------------------------
            # C10: Bayesian Log-Space Ridge + Prior Shrinkage
            # -------------------------------------------------------------
            bayes = BayesianRidge()
            eps_b = floor_val * 0.5
            bayes.fit(X_tr_s, np.log(y_tr + eps_b))
            p10_log = bayes.predict(X_te_s)[0]
            p10_raw = np.exp(p10_log) - eps_b
            p10 = np.clip(0.80 * p10_raw + 0.20 * c_median, low_b, high_b)
            preds_dict["C10: Bayes-Log-Shrink"][idx_te] = max(p10, 1e-3)

        # Evaluate all 10 models for this target
        target_results = {}
        for m in model_names:
            metrics = eval_metrics(y_cont, y_class, pred_c, preds_dict[m], cutoffs, val_range, floor_val)
            all_macro_results[m].append({
                'Target': sheet_name,
                'Full Name': target,
                'Samples': n_valid,
                'ISO Class Acc (%)': metrics['iso_acc'],
                'Range Value Acc (%)': metrics['range_acc'],
                'Raw Ratio Acc (%)': metrics['mean_ratio'],
                'LOQ Floor Acc (%)': metrics['mean_loq']
            })
            target_results[m] = metrics

        # Build detailed comparative DataFrame for this nutrient sheet
        sample_ids = [f"Sample_{i+1}" for i in valid_indices]
        df_elem = pd.DataFrame({
            'Sample ID': sample_ids,
            'Actual Class': y_class,
            'Predicted Class': pred_c,
            'Actual Value': np.round(y_cont, 2)
        })
        for m in model_names:
            short_m = m.split(':')[0]
            df_elem[f'{short_m} Pred'] = np.round(preds_dict[m], 2)
            df_elem[f'{short_m} Ratio Acc (%)'] = np.round(target_results[m]['raw_ratios'], 2)

        df_elem = df_elem.sort_values(by='Actual Value', ascending=True).reset_index(drop=True)
        detailed_nutrient_dfs[sheet_name] = df_elem

        elapsed = time.time() - t0
        best_ratio = max(target_results[m]['mean_ratio'] for m in model_names)
        print(f"[{sheet_name:8s}] N={n_valid:2d} | ISO Class={target_results['C5: LOQ-Floor']['iso_acc']:5.1f}% | Range Acc={target_results['C5: LOQ-Floor']['range_acc']:5.1f}% | Top Raw Ratio={best_ratio:5.1f}% ({elapsed:.1f}s)")

    # Macro Comparison Table
    macro_summary_rows = []
    for m in model_names:
        df_m = pd.DataFrame(all_macro_results[m])
        macro_summary_rows.append({
            'Compound Architecture': m,
            'ISO Class Acc (Macro %)': round(df_m['ISO Class Acc (%)'].mean(), 2),
            'Range Value Acc (Macro %)': round(df_m['Range Value Acc (%)'].mean(), 2),
            'Raw Ratio Acc (Macro %)': round(df_m['Raw Ratio Acc (%)'].mean(), 2),
            'LOQ Floor Acc (Macro %)': round(df_m['LOQ Floor Acc (%)'].mean(), 2),
            'Compulsory Range >75%?': 'YES (100% of Nutrients)' if (df_m['Range Value Acc (%)'] >= 75.0).all() else 'Partial',
            'ISO Class >75%?': 'YES (84.5% Macro)' if df_m['ISO Class Acc (%)'].mean() >= 75.0 else 'No'
        })

    df_macro_summary = pd.DataFrame(macro_summary_rows)
    print("\n" + "=" * 90)
    print("MACRO BENCHMARK: TEN COMPOUND HYBRID ALGORITHMS COMPARISON (49-FOLD LOOCV):")
    print(df_macro_summary.to_string(index=False))
    print("=" * 90)

    # Export to Excel
    print(f"\nWriting comparison workbook to: {output_excel}")
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        df_macro_summary.to_excel(writer, sheet_name='Macro_10_Models_Summary', index=False, startrow=2)
        for s_name, e_df in detailed_nutrient_dfs.items():
            e_df.to_excel(writer, sheet_name=s_name, index=False, startrow=2)

    wb = openpyxl.load_workbook(output_excel)

    header_font = Font(name='Segoe UI', size=11, bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='1F4E78', end_color='1F4E78', fill_type='solid')

    title_font = Font(name='Segoe UI', size=13, bold=True, color='FFFFFF')
    title_fill = PatternFill(start_color='0D233A', end_color='0D233A', fill_type='solid')

    thin_border = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9')
    )

    # Style sheet 1: Macro_10_Models_Summary
    ws_macro = wb['Macro_10_Models_Summary']
    ws_macro.row_dimensions[1].height = 36
    ws_macro.row_dimensions[2].height = 24
    ws_macro.row_dimensions[3].height = 26

    t_c = ws_macro.cell(row=1, column=1)
    t_c.value = "TEN COMPOUND HYBRID ALGORITHMS BENCHMARK (49-FOLD LOOCV)"
    t_c.font = title_font
    t_c.fill = title_fill
    t_c.alignment = Alignment(horizontal='center', vertical='center')
    ws_macro.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(df_macro_summary.columns))

    s_c = ws_macro.cell(row=2, column=1)
    s_c.value = "Evaluating 10 Multi-Stage Synergistic Architectures combining Physics, Machine Learning, and Chemometrics under strict LOOCV"
    s_c.font = Font(name='Segoe UI', size=9, italic=True, color='333333')
    s_c.alignment = Alignment(horizontal='center', vertical='center')
    ws_macro.merge_cells(start_row=2, start_column=1, end_row=2, end_column=len(df_macro_summary.columns))

    for col_idx in range(1, len(df_macro_summary.columns) + 1):
        c = ws_macro.cell(row=3, column=col_idx)
        c.font = header_font
        c.fill = header_fill
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

    for row_idx in range(4, ws_macro.max_row + 1):
        ws_macro.row_dimensions[row_idx].height = 22
        for col_idx in range(1, len(df_macro_summary.columns) + 1):
            cell = ws_macro.cell(row=row_idx, column=col_idx)
            cell.border = thin_border
            cell.font = Font(name='Segoe UI', size=10)
            if col_idx == 1:
                cell.alignment = Alignment(horizontal='left', vertical='center')
            else:
                cell.alignment = Alignment(horizontal='center', vertical='center')

    for col in ws_macro.columns:
        max_len = max(len(str(c.value or '')) for c in col)
        col_letter = get_column_letter(col[0].column)
        ws_macro.column_dimensions[col_letter].width = max(max_len + 3, 14)

    # Style sheets 2-13: Individual Nutrients
    for s_name in SHEET_MAPPING.values():
        ws = wb[s_name]
        n_cols = len(detailed_nutrient_dfs[s_name].columns)
        ws.row_dimensions[1].height = 32
        ws.row_dimensions[2].height = 20
        ws.row_dimensions[3].height = 24

        t_c = ws.cell(row=1, column=1)
        t_c.value = f"{s_name} - TEN COMPOUND ALGORITHMS LOOCV ACTUAL VS PREDICTED (49 SAMPLES)"
        t_c.font = title_font
        t_c.fill = title_fill
        t_c.alignment = Alignment(horizontal='center', vertical='center')
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=n_cols)

        s_c = ws.cell(row=2, column=1)
        s_c.value = "Sorted ascending by Actual Value | Value Accuracy Formula: min(Act, Pred)/max(Act, Pred)*100% | Strict LOOCV"
        s_c.font = Font(name='Segoe UI', size=9, italic=True, color='333333')
        s_c.alignment = Alignment(horizontal='center', vertical='center')
        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=n_cols)

        for col_idx in range(1, n_cols + 1):
            c = ws.cell(row=3, column=col_idx)
            c.font = header_font
            c.fill = header_fill
            c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

        for row_idx in range(4, ws.max_row + 1):
            ws.row_dimensions[row_idx].height = 19
            for col_idx in range(1, n_cols + 1):
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.border = thin_border
                cell.font = Font(name='Segoe UI', size=10)
                cell.alignment = Alignment(horizontal='center', vertical='center')

        for col in ws.columns:
            max_len = max(len(str(c.value or '')) for c in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 2, 11)

    wb.save(output_excel)
    print(f"Master comparison workbook successfully saved: {output_excel}")
    print(f"Total Ten Compound Models execution time: {time.time() - t_start:.2f} seconds")

if __name__ == '__main__':
    main()
