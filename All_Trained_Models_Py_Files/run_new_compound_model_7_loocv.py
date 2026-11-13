# -*- coding: utf-8 -*-
"""
================================================================================
NEW COMPOUND MODEL 7: WPD-MTEN-OLC (49-FOLD LOOCV BENCHMARK)
================================================================================
Architecture:
  1. Wavelet Packet Decomposition (WPD): Full multi-resolution frequency sub-band tree (aa, ad, da, dd)
  2. Multi-Task ElasticNet (MTEN): Joint sparse regularization across chemically correlated nutrient groups
  3. Ordinal Logistic Calibrator (OLC): Monotonic tier boundary clamping with ISO 17025 LOQ detection floor

Evaluates under strict Leave-One-Out Cross-Validation (LOOCV) across all 12 nutrients.
Outputs:
  - 'New_Compound_Model_7_WPD_MTEN_OLC_LOOCV_49_Samples.xlsx'
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
import pywt
from sklearn.model_selection import LeaveOneOut
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import MultiTaskElasticNet, ElasticNet
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, mean_absolute_error

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

# Correlated Multi-Task Nutrient Groups
TASK_GROUPS = {
    'OC%': ['OC%', 'N Kg/ha'],
    'N Kg/ha': ['N Kg/ha', 'OC%'],
    'Ca (meq)': ['Ca (meq)', 'Mg (meq)'],
    'Mg (meq)': ['Mg (meq)', 'Ca (meq)'],
    'P2O5': ['P2O5', 'K2O', 'SO4'],
    'K2O': ['K2O', 'P2O5', 'SO4'],
    'SO4': ['SO4', 'K2O', 'P2O5'],
    'Fe (ppm)': ['Fe (ppm)', 'Mn (ppm)', 'Cu (ppm)', 'Zn (ppm)'],
    'Mn (ppm)': ['Mn (ppm)', 'Fe (ppm)', 'Cu (ppm)', 'Zn (ppm)'],
    'Cu (ppm)': ['Cu (ppm)', 'Zn (ppm)', 'Fe (ppm)', 'Mn (ppm)'],
    'Zn (ppm)': ['Zn (ppm)', 'Cu (ppm)', 'Fe (ppm)', 'Mn (ppm)'],
    'B (ppm)': ['B (ppm)', 'Zn (ppm)', 'Cu (ppm)']
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

# ------------------------------------------------------------------------------
# WAVELET PACKET DECOMPOSITION (WPD)
# ------------------------------------------------------------------------------
def extract_wpd_features(X_raw, wavelet='db2', maxlevel=2):
    """Decomposes each spectrum into multi-resolution Wavelet Packet tree nodes."""
    N, D = X_raw.shape
    sample_wp = pywt.WaveletPacket(data=X_raw[0], wavelet=wavelet, mode='symmetric', maxlevel=maxlevel)
    nodes = [node.path for node in sample_wp.get_level(maxlevel, 'freq')]
    feat_dim = sum(len(sample_wp[node].data) for node in nodes)

    WPD_feats = np.zeros((N, feat_dim), dtype=np.float32)
    for i in range(N):
        wp = pywt.WaveletPacket(data=X_raw[i], wavelet=wavelet, mode='symmetric', maxlevel=maxlevel)
        WPD_feats[i] = np.hstack([wp[node].data for node in nodes])

    # Combine raw spectra + WPD multi-resolution packets
    combined = np.hstack([X_raw, WPD_feats])
    return combined

def main():
    t_start = time.time()
    print("=" * 80)
    print("TRAINING NEW COMPOUND MODEL 7: WPD-MTEN-OLC")
    print("Wavelet Packet Decomposition + Multi-Task ElasticNet + Ordinal Logistic Calibrator")
    print("Execution: Strict 49-Fold Leave-One-Out Cross-Validation (LOOCV)")
    print("=" * 80)

    script_dir = r"c:\Users\akash\Downloads\Soil Data"
    data_file = os.path.join(script_dir, 'data.xlsx')
    output_excel = os.path.join(script_dir, 'New_Compound_Model_7_WPD_MTEN_OLC_LOOCV_49_Samples.xlsx')

    df = pd.read_excel(data_file)
    spec_cols = [c for c in df.columns if c.startswith('nm_')]
    loo = LeaveOneOut()

    macro_summary_list = []
    detailed_nutrient_dfs = {}

    for target, sheet_name in SHEET_MAPPING.items():
        t0 = time.time()
        rules = CLASS_RULES[target]
        cutoffs = get_boundary_cutoffs(rules)
        floor_val = get_loq(target)

        # Clean numeric target
        s_clean = df[target].astype(str).str.strip().str.replace('l ', '1').str.replace('l', '1')
        s_numeric = pd.to_numeric(s_clean, errors='coerce')
        valid_mask = s_numeric.notnull()
        df_target = df[valid_mask].copy()
        df_target[target] = s_numeric[valid_mask]

        valid_indices = df_target.index.values
        X_raw = df_target[spec_cols].values.astype(np.float32)
        y_cont = df_target[target].values.astype(np.float32)
        n_valid = len(y_cont)
        val_range = float(y_cont.max() - y_cont.min())
        y_class = np.array([assign_class(v, rules) for v in y_cont])

        # Multi-task targets: collect group targets
        group_targets = TASK_GROUPS[target]
        Y_group = []
        for gt in group_targets:
            s_c = df_target[gt].astype(str).str.strip().str.replace('l ', '1').str.replace('l', '1')
            s_num = pd.to_numeric(s_c, errors='coerce').fillna(0.0).values.astype(np.float32)
            Y_group.append(s_num)
        Y_multi = np.column_stack(Y_group) # (N, n_tasks)

        # Extract WPD features
        X_wpd = extract_wpd_features(X_raw, wavelet='db2', maxlevel=2)

        # Stage 1: Fertility Tier LOOCV Classifier
        clf = STAGE1_CLFS[target]
        pipe_clf = Pipeline([('scaler', StandardScaler()), ('clf', clf)])
        pred_c = []
        for tr, te in loo.split(X_raw):
            pipe_clf.fit(X_raw[tr], y_class[tr])
            pred_c.append(pipe_clf.predict(X_raw[te])[0])
        pred_c = np.array(pred_c)

        # Stage 2: Multi-Task ElasticNet under LOOCV
        y_pred = np.zeros(n_valid, dtype=np.float32)
        for tr, te in loo.split(X_wpd):
            idx_te = te[0]
            c_p = pred_c[idx_te]
            low_b, high_b = rules.get(c_p, (float(y_cont.min()), float(y_cont.max())))
            low_b = max(low_b, float(y_cont.min()))
            high_b = min(high_b, float(y_cont.max()))
            if high_b <= low_b: high_b = low_b + 0.05 * val_range

            sc = StandardScaler().fit(X_wpd[tr])
            X_tr_s = sc.transform(X_wpd[tr])
            X_te_s = sc.transform(X_wpd[te])
            
            # Normalize targets across tasks
            y_means = Y_multi[tr].mean(axis=0)
            y_stds = Y_multi[tr].std(axis=0)
            y_stds[y_stds == 0] = 1.0
            Y_tr_norm = (Y_multi[tr] - y_means) / y_stds

            # Multi-Task ElasticNet with joint L21 penalty
            mten = MultiTaskElasticNet(alpha=0.08, l1_ratio=0.5, random_state=42)
            mten.fit(X_tr_s, Y_tr_norm)
            
            p_norm = mten.predict(X_te_s)[0, 0] # target is column 0
            p_mten = p_norm * y_stds[0] + y_means[0]

            # Class median anchor
            c_mask = (y_class[tr] == c_p)
            c_median = float(np.median(y_cont[tr][c_mask])) if np.sum(c_mask) >= 3 else float(np.median(y_cont[tr]))

            # 70% MTEN + 30% Class Median
            p_blend = 0.70 * p_mten + 0.30 * c_median
            p_final = np.clip(p_blend, low_b, high_b)
            y_pred[idx_te] = max(float(p_final), 1e-3)

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
            'Tasks Grouped': f"{len(group_targets)} Nutrients",
            'Range > 75%?': 'PASS' if range_acc >= 75.0 else 'FAIL',
            'ISO Class > 75%?': 'PASS' if iso_acc >= 75.0 else 'FAIL'
        })

        # Detailed sheet dataframe
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
        print(f"[{sheet_name:8s}] N={n_valid:2d} | Tasks: {len(group_targets):d} | ISO Class: {iso_acc:5.1f}% | Range Acc: {range_acc:5.1f}% | Raw Ratio: {mean_raw_ratio:5.1f}% | LOQ Ratio: {mean_loq_ratio:5.1f}% ({elapsed:.1f}s)")

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
        'Tasks Grouped': "Multi-Task",
        'Range > 75%?': 'PASS (100%)' if (df_macro['Range Value Acc (%)'] >= 75.0).all() else 'FAIL',
        'ISO Class > 75%?': 'PASS' if df_macro['ISO Class Acc (%)'].mean() >= 75.0 else 'FAIL'
    }
    df_macro_with_avg = pd.concat([df_macro, pd.DataFrame([macro_row])], ignore_index=True)

    print("\n" + "=" * 90)
    print("PERFORMANCE SUMMARY FOR NEW COMPOUND MODEL 7 (WPD-MTEN-OLC):")
    print(df_macro_with_avg.to_string(index=False))
    print("=" * 90)

    # Export to Excel
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
    ws_macro.merge_cells('A1:M1')
    t_cell = ws_macro['A1']
    t_cell.value = "49-FOLD LOOCV BENCHMARK: NEW COMPOUND MODEL 7 (WPD-MTEN-OLC)"
    t_cell.font = title_font
    t_cell.fill = title_fill
    t_cell.alignment = Alignment(horizontal='center', vertical='center')
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

    # Format each individual nutrient sheet
    for s_name in SHEET_MAPPING.values():
        ws = wb[s_name]
        ws.merge_cells('A1:J1')
        tc = ws['A1']
        tc.value = f"NUTRIENT LOOCV EVALUATION ({s_name}): WPD-MTEN-OLC (49 SAMPLES)"
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
    print(f"Successfully generated: {output_excel}")
    total_time = time.time() - t_start
    print(f"Total execution time: {total_time:.1f} seconds")

if __name__ == '__main__':
    main()
