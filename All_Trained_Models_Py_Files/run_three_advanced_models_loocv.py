# -*- coding: utf-8 -*-
"""
================================================================================
THREE ADVANCED MODELS BENCHMARK (49-FOLD LOOCV ACROSS ALL 12 NUTRIENTS)
================================================================================
Models Evaluated:
  1. Model 1: Multi-Granular Ordinal Quantile & Class-Bounded Hybrid (MGOQI)
  2. Model 2: Accredited Laboratory LOQ Floor Calibration Protocol (LOQ-Floor)
  3. Model 3: Direct Log-Ratio MALE (Mean Absolute Log Error) Optimizer (DMLRO)

Evaluation Metric:
  - Ratio Value Accuracy: min(Actual, Pred) / max(Actual, Pred) * 100%
  - LOQ Floor Value Accuracy: min(max(A, LOQ), max(P, LOQ)) / max(max(A, LOQ), max(P, LOQ)) * 100%
  - Chemometric Range Value Accuracy: (1 - RMSE / Range) * 100% (Compulsory > 75%)
  - Strict Class Accuracy (%) & ISO 17025 Buffer Class Accuracy (%) (+/-15% boundary)
  - Strict 49-Fold Leave-One-Out Cross-Validation (cv=LeaveOneOut())

Output:
  - 'Three_Advanced_Models_LOOCV_49_Samples_Comparison.xlsx'
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
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import ExtraTreesRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
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

def evaluate_predictions(y_cont, y_class, pred_c, pred_v, cutoffs, val_range, floor_val):
    strict_pass = (y_class == pred_c)
    buffer_pass = [act_c == pr_c or any(abs(act_v - b) / b <= 0.15 for b in cutoffs) for act_v, act_c, pr_c in zip(y_cont, y_class, pred_c)]
    
    strict_acc = np.mean(strict_pass) * 100.0
    buffer_acc = np.mean(buffer_pass) * 100.0
    
    rmse = np.sqrt(mean_squared_error(y_cont, pred_v))
    mae = mean_absolute_error(y_cont, pred_v)
    r2 = r2_score(y_cont, pred_v)
    
    range_acc = (1.0 - (rmse / val_range)) * 100.0 if val_range > 0 else 0.0
    
    raw_ratios = np.array([compute_ratio_accuracy(a, p) for a, p in zip(y_cont, pred_v)])
    loq_ratios = np.array([compute_loq_ratio_accuracy(a, p, floor_val) for a, p in zip(y_cont, pred_v)])
    
    mean_raw_ratio = raw_ratios.mean()
    mean_loq_ratio = loq_ratios.mean()
    pct_ge_50 = (raw_ratios >= 50.0).mean() * 100.0
    pct_ge_75 = (raw_ratios >= 75.0).mean() * 100.0
    
    return {
        'Strict Class Acc (%)': round(strict_acc, 2),
        'ISO Buffer Class Acc (%)': round(buffer_acc, 2),
        'Range Value Acc (%)': round(range_acc, 2),
        'Mean Value Acc (Ratio %)': round(mean_raw_ratio, 2),
        'Value Acc with LOQ Floor (%)': round(mean_loq_ratio, 2),
        '% Samples >= 50% Acc': round(pct_ge_50, 1),
        '% Samples >= 75% Acc': round(pct_ge_75, 1),
        'LOOCV RMSE': round(rmse, 4),
        'LOOCV MAE': round(mae, 4),
        'LOOCV R^2 (%)': round(r2 * 100.0, 2),
        'raw_ratios': raw_ratios,
        'loq_ratios': loq_ratios,
        'pred_class': pred_c,
        'pred_val': pred_v,
        'strict_pass': strict_pass,
        'buffer_pass': buffer_pass
    }

def main():
    t_start = time.time()
    print("=" * 80)
    print("RUNNING THREE ADVANCED MODELS BENCHMARK (49-FOLD LOOCV)")
    print("=" * 80)

    script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()
    data_file = os.path.join(script_dir, 'data.xlsx')
    output_excel = os.path.join(script_dir, 'Three_Advanced_Models_LOOCV_49_Samples_Comparison.xlsx')

    df = pd.read_excel(data_file)
    spec_cols = [c for c in df.columns if c.startswith('nm_')]
    loo = LeaveOneOut()

    m1_summaries, m2_summaries, m3_summaries = [], [], []
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

        # Stage 1: Classifier LOOCV (common high-accuracy stage)
        clf = STAGE1_CLFS[target]
        pipe_clf = Pipeline([('scaler', StandardScaler()), ('clf', clf)])
        pred_c = []
        for tr, te in loo.split(X_raw):
            pipe_clf.fit(X_raw[tr], y_class[tr])
            pred_c.append(pipe_clf.predict(X_raw[te])[0])
        pred_c = np.array(pred_c)

        # -------------------------------------------------------------
        # MODEL 1: Multi-Granular Ordinal Quantile Interpolator (MGOQI)
        # -------------------------------------------------------------
        # Predict continuous within class using class-conditioned median & quantile blend
        p1_vals = []
        for tr, te in loo.split(X_raw):
            sc = StandardScaler()
            X_tr_s = sc.fit_transform(X_raw[tr])
            X_te_s = sc.transform(X_raw[te])
            c_pred = pred_c[te[0]]
            
            # Sub-bucket samples belonging to predicted class in training set
            c_mask = (y_class[tr] == c_pred)
            if np.sum(c_mask) >= 3:
                # Quantile anchor within class
                c_vals = y_cont[tr][c_mask]
                c_q25 = np.percentile(c_vals, 25)
                c_q50 = np.percentile(c_vals, 50)
                c_q75 = np.percentile(c_vals, 75)
            else:
                c_q25 = c_q50 = c_q75 = np.median(y_cont[tr])
                
            # Secondary regressor
            reg1 = ExtraTreesRegressor(n_estimators=50, max_depth=5, random_state=42)
            reg1.fit(X_tr_s, y_cont[tr])
            p_raw = reg1.predict(X_te_s)[0]
            
            # Quantile constrained blend (70% regressor, 30% class median)
            p_blend = 0.70 * p_raw + 0.30 * c_q50
            if c_pred in active_rules:
                low_b, high_b = active_rules[c_pred]
                low_b = max(low_b, float(y_cont.min()))
                high_b = min(high_b, float(y_cont.max()))
                if high_b <= low_b: high_b = low_b + 0.05 * val_range
                p_blend = np.clip(p_blend, low_b, high_b)
            p1_vals.append(max(p_blend, 1e-3))
            
        p1_vals = np.array(p1_vals)
        res_m1 = evaluate_predictions(y_cont, y_class, pred_c, p1_vals, cutoffs, val_range, floor_val)

        # -------------------------------------------------------------
        # MODEL 2: Accredited Laboratory LOQ Floor Calibration (LOQ-Floor)
        # -------------------------------------------------------------
        # Tuned Model 37 Regressor + Analytical LOQ Detection Limit Anchoring
        p2_vals = []
        for tr, te in loo.split(X_raw):
            sc = StandardScaler()
            X_tr_s = sc.fit_transform(X_raw[tr])
            X_te_s = sc.transform(X_raw[te])
            c_pred = pred_c[te[0]]
            
            if target in ['N Kg/ha']:
                reg2 = GradientBoostingRegressor(n_estimators=50, max_depth=3, learning_rate=0.05, random_state=42)
            elif target in ['Ca (meq)', 'Mg (meq)', 'K2O', 'SO4', 'Fe (ppm)', 'Mn (ppm)', 'Zn (ppm)']:
                reg2 = SVR(kernel='rbf', C=50.0, epsilon=0.05)
            else:
                reg2 = ExtraTreesRegressor(n_estimators=100, max_depth=6, random_state=42)
                
            reg2.fit(X_tr_s, y_cont[tr])
            p_val = max(0.0, reg2.predict(X_te_s)[0])
            
            # Class-bound
            if c_pred in active_rules:
                low_b, high_b = active_rules[c_pred]
                low_b = max(low_b, float(y_cont.min()))
                high_b = min(high_b, float(y_cont.max()))
                if high_b <= low_b: high_b = low_b + 0.05 * val_range
                p_val = np.clip(p_val, low_b, high_b)
            p2_vals.append(p_val)
            
        p2_vals = np.array(p2_vals)
        res_m2 = evaluate_predictions(y_cont, y_class, pred_c, p2_vals, cutoffs, val_range, floor_val)

        # -------------------------------------------------------------
        # MODEL 3: Direct MALE Log-Ratio Optimizer (DMLRO)
        # -------------------------------------------------------------
        # Directly optimizes L1 error in log-space: min |ln(y) - ln(p)|
        p3_vals = []
        for tr, te in loo.split(X_raw):
            sc = StandardScaler()
            X_tr_s = sc.fit_transform(X_raw[tr])
            X_te_s = sc.transform(X_raw[te])
            c_pred = pred_c[te[0]]
            
            # Train in log-space with LOQ offset
            eps = floor_val * 0.5
            y_log_tr = np.log(y_cont[tr] + eps)
            
            reg3 = GradientBoostingRegressor(loss='absolute_error', n_estimators=60, max_depth=3, learning_rate=0.05, random_state=42)
            reg3.fit(X_tr_s, y_log_tr)
            p_log = reg3.predict(X_te_s)[0]
            p_val = max(1e-4, np.exp(p_log) - eps)
            
            # Bound within class interval
            if c_pred in active_rules:
                low_b, high_b = active_rules[c_pred]
                low_b = max(low_b, float(y_cont.min()))
                high_b = min(high_b, float(y_cont.max()))
                if high_b <= low_b: high_b = low_b + 0.05 * val_range
                p_val = np.clip(p_val, low_b, high_b)
            p3_vals.append(p_val)
            
        p3_vals = np.array(p3_vals)
        res_m3 = evaluate_predictions(y_cont, y_class, pred_c, p3_vals, cutoffs, val_range, floor_val)

        # Append summaries
        m1_summaries.append({'Target': sheet_name, 'Name': target, 'N': n_valid, **{f'M1_{k}': v for k, v in res_m1.items() if not isinstance(v, (np.ndarray, list))}})
        m2_summaries.append({'Target': sheet_name, 'Name': target, 'N': n_valid, **{f'M2_{k}': v for k, v in res_m2.items() if not isinstance(v, (np.ndarray, list))}})
        m3_summaries.append({'Target': sheet_name, 'Name': target, 'N': n_valid, **{f'M3_{k}': v for k, v in res_m3.items() if not isinstance(v, (np.ndarray, list))}})

        # Detailed dataframe per nutrient comparing all 3
        sample_ids = [f"Sample_{i+1}" for i in valid_indices]
        df_elem = pd.DataFrame({
            'Sample ID': sample_ids,
            'Actual Class': y_class,
            'Predicted Class': pred_c,
            'Strict Status': ['Correct' if sp else 'Missed' for sp in res_m2['strict_pass']],
            'ISO Buffer Status': ['Correct' if bp else 'Missed' for bp in res_m2['buffer_pass']],
            'Actual Value': np.round(y_cont, 2),
            'Model 1 Pred': np.round(p1_vals, 2),
            'Model 1 Ratio Acc (%)': np.round(res_m1['raw_ratios'], 2),
            'Model 2 Pred (LOQ)': np.round(p2_vals, 2),
            'Model 2 Ratio Acc (%)': np.round(res_m2['raw_ratios'], 2),
            'Model 2 LOQ Acc (%)': np.round(res_m2['loq_ratios'], 2),
            'Model 3 Pred (Log-L1)': np.round(p3_vals, 2),
            'Model 3 Ratio Acc (%)': np.round(res_m3['raw_ratios'], 2)
        }).sort_values(by='Actual Value', ascending=True).reset_index(drop=True)
        
        detailed_nutrient_dfs[sheet_name] = df_elem
        elapsed = time.time() - t0
        print(f"[{sheet_name:8s}] N={n_valid:2d} | ISO Class={res_m2['ISO Buffer Class Acc (%)']:5.1f}% | M1 Ratio={res_m1['Mean Value Acc (Ratio %)']:5.1f}% | M2 Ratio={res_m2['Mean Value Acc (Ratio %)']:5.1f}% (LOQ={res_m2['Value Acc with LOQ Floor (%)']:5.1f}%) | M3 Ratio={res_m3['Mean Value Acc (Ratio %)']:5.1f}% ({elapsed:.1f}s)")

    # Macro Comparison Table
    macro_rows = []
    for s_name in SHEET_MAPPING.values():
        m1 = next(r for r in m1_summaries if r['Target'] == s_name)
        m2 = next(r for r in m2_summaries if r['Target'] == s_name)
        m3 = next(r for r in m3_summaries if r['Target'] == s_name)
        macro_rows.append({
            'Target Nutrient': s_name,
            'Full Name': m1['Name'],
            'Samples': m1['N'],
            'ISO Class Acc (%)': m2['M2_ISO Buffer Class Acc (%)'],
            'Range Value Acc (%)': m2['M2_Range Value Acc (%)'],
            'Model 1 (Ordinal) Ratio Acc (%)': m1['M1_Mean Value Acc (Ratio %)'],
            'Model 2 (LOQ-Floor) Raw Ratio (%)': m2['M2_Mean Value Acc (Ratio %)'],
            'Model 2 (LOQ-Floor) Adjusted (%)': m2['M2_Value Acc with LOQ Floor (%)'],
            'Model 3 (Log-L1) Ratio Acc (%)': m3['M3_Mean Value Acc (Ratio %)']
        })

    df_macro = pd.DataFrame(macro_rows)
    avg_row = {
        'Target Nutrient': 'OVERALL AVERAGE',
        'Full Name': 'All 12 Soil Nutrients',
        'Samples': int(round(df_macro['Samples'].mean())),
        'ISO Class Acc (%)': round(df_macro['ISO Class Acc (%)'].mean(), 2),
        'Range Value Acc (%)': round(df_macro['Range Value Acc (%)'].mean(), 2),
        'Model 1 (Ordinal) Ratio Acc (%)': round(df_macro['Model 1 (Ordinal) Ratio Acc (%)'].mean(), 2),
        'Model 2 (LOQ-Floor) Raw Ratio (%)': round(df_macro['Model 2 (LOQ-Floor) Raw Ratio (%)'].mean(), 2),
        'Model 2 (LOQ-Floor) Adjusted (%)': round(df_macro['Model 2 (LOQ-Floor) Adjusted (%)'].mean(), 2),
        'Model 3 (Log-L1) Ratio Acc (%)': round(df_macro['Model 3 (Log-L1) Ratio Acc (%)'].mean(), 2)
    }
    df_macro = pd.concat([df_macro, pd.DataFrame([avg_row])], ignore_index=True)

    print("\n" + "=" * 80)
    print("MACRO THREE-MODEL BENCHMARK COMPARISON:")
    print(df_macro.to_string(index=False))
    print("=" * 80)

    # Export to Excel
    print(f"\nWriting comparison workbook to: {output_excel}")
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        df_macro.to_excel(writer, sheet_name='Three_Models_Comparison', index=False, startrow=2)
        for s_name, e_df in detailed_nutrient_dfs.items():
            e_df.to_excel(writer, sheet_name=s_name, index=False, startrow=2)

    wb = openpyxl.load_workbook(output_excel)

    header_font = Font(name='Segoe UI', size=11, bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='1F4E78', end_color='1F4E78', fill_type='solid')

    title_font = Font(name='Segoe UI', size=13, bold=True, color='FFFFFF')
    title_fill = PatternFill(start_color='0D233A', end_color='0D233A', fill_type='solid')

    avg_font = Font(name='Segoe UI', size=11, bold=True, color='000000')
    avg_fill = PatternFill(start_color='D9E1F2', end_color='D9E1F2', fill_type='solid')

    thin_border = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9')
    )

    # Style sheet 1: Three_Models_Comparison
    ws_comp = wb['Three_Models_Comparison']
    ws_comp.row_dimensions[1].height = 36
    ws_comp.row_dimensions[2].height = 24
    ws_comp.row_dimensions[3].height = 26

    t_cell = ws_comp.cell(row=1, column=1)
    t_cell.value = "THREE ADVANCED MODELS BENCHMARK COMPARISON (49-FOLD LOOCV)"
    t_cell.font = title_font
    t_cell.fill = title_fill
    t_cell.alignment = Alignment(horizontal='center', vertical='center')
    ws_comp.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(df_macro.columns))

    s_cell = ws_comp.cell(row=2, column=1)
    s_cell.value = "Comparing Model 1 (Ordinal Quantile), Model 2 (LOQ-Floor), and Model 3 (Log-L1 MALE) under strict LOOCV"
    s_cell.font = Font(name='Segoe UI', size=9, italic=True, color='333333')
    s_cell.alignment = Alignment(horizontal='center', vertical='center')
    ws_comp.merge_cells(start_row=2, start_column=1, end_row=2, end_column=len(df_macro.columns))

    for col_idx in range(1, len(df_macro.columns) + 1):
        c = ws_comp.cell(row=3, column=col_idx)
        c.font = header_font
        c.fill = header_fill
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

    for row_idx in range(4, ws_comp.max_row + 1):
        ws_comp.row_dimensions[row_idx].height = 20
        is_avg = (row_idx == ws_comp.max_row)
        for col_idx in range(1, len(df_macro.columns) + 1):
            cell = ws_comp.cell(row=row_idx, column=col_idx)
            cell.border = thin_border
            if is_avg:
                cell.font = avg_font
                cell.fill = avg_fill
                cell.alignment = Alignment(horizontal='center', vertical='center')
            else:
                cell.font = Font(name='Segoe UI', size=10)
                if col_idx in [1, 2]:
                    cell.alignment = Alignment(horizontal='left', vertical='center')
                else:
                    cell.alignment = Alignment(horizontal='center', vertical='center')

    for col in ws_comp.columns:
        max_len = max(len(str(c.value or '')) for c in col)
        col_letter = get_column_letter(col[0].column)
        ws_comp.column_dimensions[col_letter].width = max(max_len + 3, 14)

    # Style sheets 2-13: Individual Nutrients
    for s_name in SHEET_MAPPING.values():
        ws = wb[s_name]
        n_cols = len(detailed_nutrient_dfs[s_name].columns)
        ws.row_dimensions[1].height = 32
        ws.row_dimensions[2].height = 20
        ws.row_dimensions[3].height = 24

        t_c = ws.cell(row=1, column=1)
        t_c.value = f"{s_name} - THREE MODELS SAMPLE-BY-SAMPLE LOOCV COMPARISON (49 SAMPLES)"
        t_c.font = title_font
        t_c.fill = title_fill
        t_c.alignment = Alignment(horizontal='center', vertical='center')
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=n_cols)

        s_c = ws.cell(row=2, column=1)
        s_c.value = "Sorted ascending by Actual Value | Value Accuracy: min(Act, Pred)/max(Act, Pred)*100% | Strict LOOCV"
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
            ws.column_dimensions[col_letter].width = max(max_len + 3, 13)

    wb.save(output_excel)
    print(f"Master comparison workbook successfully saved: {output_excel}")
    print(f"Total Three Models execution time: {time.time() - t_start:.2f} seconds")

if __name__ == '__main__':
    main()
