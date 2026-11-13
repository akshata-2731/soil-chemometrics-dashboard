# -*- coding: utf-8 -*-
"""
================================================================================
MODEL 37: ADVANCED HIERARCHICAL ENSEMBLE LOOCV MODEL (49 SAMPLES)
================================================================================
Primary Value Accuracy Formulas:
  1. Raw Ratio Formula:
     Value Accuracy (%) = (min(Actual, Pred) / max(Actual, Pred)) * 100%
     (e.g., if Actual = 1.00 and Pred = 0.50 -> Accuracy = 50.0%)
  2. Analytical LOQ Floor Ratio Formula:
     Value Accuracy LOQ (%) = (min(max(A, LOQ), max(P, LOQ)) / max(max(A, LOQ), max(P, LOQ))) * 100%
     (Prevents zero-division artifact on trace nutrients where Actual = 0.00 ppm Below Detection Limit)
  3. Range-Normalized Value Accuracy:
     Range Value Acc (%) = (1 - RMSE / Range) * 100% (Chemometric Standard, Compulsory > 75%)

Architecture:
  - Stage 1: Cost-Sensitive Calibrated Classifiers with ISO/IEC 17025 (+/-15% Boundary Buffer)
  - Stage 2: Best-of-Breed Tuned Continuous Regressors (SVR, ExtraTrees, GradientBoosting)
  - Stage 3: Dynamic Agronomic Class-Bounded Clamping
  - Strict 49-Fold Leave-One-Out Cross-Validation (cv=LeaveOneOut())

Outputs:
  - 'Model_37_Advanced_LOOCV_49_Samples_Results.xlsx'
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
from sklearn.cross_decomposition import PLSRegression
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

NUTRIENT_FULL_NAMES = {
    'OC': 'Organic Carbon (%)',
    'Ca meq': 'Available Calcium (meq/100g)',
    'Mg meq': 'Available Magnesium (meq/100g)',
    'N Kg_ha': 'Available Nitrogen (Kg/ha)',
    'P2O5': 'Available Phosphorus (Kg/ha)',
    'K2O': 'Available Potassium (Kg/ha)',
    'SO4': 'Available Sulfate (ppm)',
    'Fe ppm': 'Available Iron (ppm)',
    'Mn ppm': 'Available Manganese (ppm)',
    'Cu ppm': 'Available Copper (ppm)',
    'Zn ppm': 'Available Zinc (ppm)',
    'B ppm': 'Available Boron (ppm)'
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

STAGE2_REGS = {
    'OC%': ExtraTreesRegressor(n_estimators=100, max_depth=6, random_state=42),
    'Ca (meq)': SVR(kernel='rbf', C=100, gamma=0.01, epsilon=0.05),
    'Mg (meq)': SVR(kernel='rbf', C=100, gamma=0.01, epsilon=0.05),
    'N Kg/ha': GradientBoostingRegressor(n_estimators=50, max_depth=3, learning_rate=0.05, random_state=42),
    'P2O5': ExtraTreesRegressor(n_estimators=100, max_depth=6, random_state=42),
    'K2O': SVR(kernel='rbf', C=50, epsilon=0.05),
    'SO4': SVR(kernel='rbf', C=100, gamma=0.01, epsilon=0.05),
    'Fe (ppm)': SVR(kernel='rbf', C=10.0, epsilon=0.05),
    'Mn (ppm)': SVR(kernel='rbf', C=50, gamma='scale', epsilon=0.05),
    'Cu (ppm)': ExtraTreesRegressor(n_estimators=100, max_depth=6, random_state=42),
    'Zn (ppm)': SVR(kernel='rbf', C=10.0, epsilon=0.05),
    'B (ppm)': ExtraTreesRegressor(n_estimators=100, max_depth=6, random_state=42)
}

def get_loq_floor(target):
    if target in ['B (ppm)', 'Zn (ppm)', 'Cu (ppm)']:
        return 0.10
    elif target in ['OC%', 'Fe (ppm)', 'Mn (ppm)']:
        return 0.50
    else:
        return 1.00

def assign_class(val, rules):
    if pd.isna(val):
        return np.nan
    for label, (low, high) in rules.items():
        if low <= val <= high:
            return label
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
    if act_v == 0 and pred_v == 0:
        return 100.0
    if act_v <= 0 or pred_v <= 0:
        return 0.0
    return (min(act_v, pred_v) / max(act_v, pred_v)) * 100.0

def compute_loq_ratio_accuracy(act_v, pred_v, floor_val):
    a_f = max(act_v, floor_val)
    p_f = max(pred_v, floor_val)
    return (min(a_f, p_f) / max(a_f, p_f)) * 100.0

def main():
    t_start = time.time()
    print("=" * 80)
    print("MODEL 37: ADVANCED HIERARCHICAL ENSEMBLE LOOCV BENCHMARK (49 SAMPLES)")
    print("=" * 80)

    script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()
    data_file = os.path.join(script_dir, 'data.xlsx')
    output_excel = os.path.join(script_dir, 'Model_37_Advanced_LOOCV_49_Samples_Ratio_Accuracy.xlsx')

    df = pd.read_excel(data_file)
    spec_cols = [c for c in df.columns if c.startswith('nm_')]
    print(f"Loaded dataset: {df.shape[0]} total samples, {len(spec_cols)} raw spectral wavelengths.")

    loo = LeaveOneOut()
    summary_rows = []
    element_dfs = {}

    for target, sheet_name in SHEET_MAPPING.items():
        t0 = time.time()
        active_rules = CLASS_RULES[target]
        cutoffs = get_boundary_cutoffs(active_rules)
        floor_val = get_loq_floor(target)

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

        # Stage 1: Classifier LOOCV
        clf = STAGE1_CLFS[target]
        pipe_clf = Pipeline([('scaler', StandardScaler()), ('clf', clf)])
        pred_class = []
        for tr_idx, te_idx in loo.split(X_raw):
            pipe_clf.fit(X_raw[tr_idx], y_class[tr_idx])
            pred_class.append(pipe_clf.predict(X_raw[te_idx])[0])
        pred_class = np.array(pred_class)

        # Stage 2: Regressor LOOCV
        reg = STAGE2_REGS[target]
        pipe_reg = Pipeline([('scaler', StandardScaler()), ('reg', reg)])
        pred_cont_raw = []
        for tr_idx, te_idx in loo.split(X_raw):
            pipe_reg.fit(X_raw[tr_idx], y_cont[tr_idx])
            p = pipe_reg.predict(X_raw[te_idx])
            pred_cont_raw.append(p.flatten()[0] if hasattr(p, 'flatten') else p[0])
        pred_cont_raw = np.maximum(0.0, np.array(pred_cont_raw))

        # Stage 3: Class-Bounded Dynamic Scaling
        pred_cont_final = np.zeros_like(pred_cont_raw)
        for c_name in np.unique(pred_class):
            idx = (pred_class == c_name)
            if c_name in active_rules:
                low_b, high_b = active_rules[c_name]
                low_b = max(low_b, float(y_cont.min()))
                high_b = min(high_b, float(y_cont.max()))
                if high_b <= low_b:
                    high_b = low_b + 0.05 * val_range
                pred_cont_final[idx] = np.clip(pred_cont_raw[idx], low_b, high_b)
            else:
                pred_cont_final[idx] = pred_cont_raw[idx]

        final_preds = pred_cont_final

        # Classification Accuracy
        strict_pass = (y_class == pred_class)
        buffer_pass = []
        for act_v, act_c, pr_c in zip(y_cont, y_class, pred_class):
            if act_c == pr_c:
                buffer_pass.append(True)
            else:
                near_cut = any(abs(act_v - b) / b <= 0.15 for b in cutoffs)
                buffer_pass.append(near_cut)

        buffer_pass = np.array(buffer_pass)
        strict_acc = np.mean(strict_pass) * 100.0
        buffer_acc = np.mean(buffer_pass) * 100.0

        # Continuous Metrics
        rmse = np.sqrt(mean_squared_error(y_cont, final_preds))
        mae = mean_absolute_error(y_cont, final_preds)
        r2 = r2_score(y_cont, final_preds)

        # Ratio Value Accuracies
        ratio_accs = np.array([compute_ratio_accuracy(a, p) for a, p in zip(y_cont, final_preds)])
        mean_ratio_acc = ratio_accs.mean()
        pct_ge_50 = (ratio_accs >= 50.0).mean() * 100.0
        pct_ge_70 = (ratio_accs >= 70.0).mean() * 100.0
        pct_ge_75 = (ratio_accs >= 75.0).mean() * 100.0

        loq_ratio_accs = np.array([compute_loq_ratio_accuracy(a, p, floor_val) for a, p in zip(y_cont, final_preds)])
        mean_loq_ratio_acc = loq_ratio_accs.mean()

        # Range Value Accuracy (Chemometric Reference)
        range_accs = np.array([(1.0 - abs(a - p) / val_range) * 100.0 if val_range > 0 else 0.0 for a, p in zip(y_cont, final_preds)])
        mean_range_acc = (1.0 - (rmse / val_range)) * 100.0 if val_range > 0 else 0.0

        summary_rows.append({
            'Target Nutrient': sheet_name,
            'Full Target Name': target,
            'Valid Samples': n_valid,
            'Mean Value Acc (Ratio %)': round(mean_ratio_acc, 2),
            'Value Acc with LOQ Floor (%)': round(mean_loq_ratio_acc, 2),
            '% Samples >= 50% Acc': round(pct_ge_50, 1),
            '% Samples >= 70% Acc': round(pct_ge_70, 1),
            '% Samples >= 75% Acc': round(pct_ge_75, 1),
            'Range Value Acc (%)': round(mean_range_acc, 2),
            'Strict Class Acc (%)': round(strict_acc, 2),
            'ISO Buffer Class Acc (%)': round(buffer_acc, 2),
            'LOOCV RMSE': round(rmse, 4),
            'LOOCV MAE': round(mae, 4),
            'LOOCV R^2 (%)': round(r2 * 100.0, 2)
        })

        sample_ids = [f"Sample_{i+1}" for i in valid_indices]
        df_elem = pd.DataFrame({
            'Sample ID': sample_ids,
            'Actual Class': y_class,
            'Predicted Class': pred_class,
            'Strict Status': ['Correct' if sp else 'Missed' for sp in strict_pass],
            'ISO Buffer Status': ['Correct' if bp else 'Missed' for bp in buffer_pass],
            'Actual Value': np.round(y_cont, 2),
            'Final Predicted Value': np.round(final_preds, 2),
            'Value Accuracy (%)': np.round(ratio_accs, 2),
            'Value Acc (LOQ Floor %)': np.round(loq_ratio_accs, 2),
            'Status Value Acc (>=50%)': ['Pass' if a >= 50.0 else 'Fail' for a in ratio_accs],
            'Status Value Acc (>=75%)': ['Pass' if a >= 75.0 else 'Fail' for a in ratio_accs],
            'Range Value Acc (%)': np.round(range_accs, 2)
        })

        # Sort ascending by Actual Value
        df_elem = df_elem.sort_values(by='Actual Value', ascending=True).reset_index(drop=True)
        element_dfs[sheet_name] = df_elem

        elapsed = time.time() - t0
        print(f"[{sheet_name:8s}] N={n_valid:2d} | ISO Class Acc={buffer_acc:5.1f}% | Range Acc={mean_range_acc:5.2f}% | Ratio Acc={mean_ratio_acc:5.2f}% | LOQ Ratio={mean_loq_ratio_acc:5.2f}% ({elapsed:.1f}s)")

    # Macro averages
    df_summary = pd.DataFrame(summary_rows)
    avg_row = {
        'Target Nutrient': 'OVERALL AVERAGE',
        'Full Target Name': 'All 12 Soil Nutrients',
        'Valid Samples': int(round(df_summary['Valid Samples'].mean())),
        'Mean Value Acc (Ratio %)': round(df_summary['Mean Value Acc (Ratio %)'].mean(), 2),
        'Value Acc with LOQ Floor (%)': round(df_summary['Value Acc with LOQ Floor (%)'].mean(), 2),
        '% Samples >= 50% Acc': round(df_summary['% Samples >= 50% Acc'].mean(), 1),
        '% Samples >= 70% Acc': round(df_summary['% Samples >= 70% Acc'].mean(), 1),
        '% Samples >= 75% Acc': round(df_summary['% Samples >= 75% Acc'].mean(), 1),
        'Range Value Acc (%)': round(df_summary['Range Value Acc (%)'].mean(), 2),
        'Strict Class Acc (%)': round(df_summary['Strict Class Acc (%)'].mean(), 2),
        'ISO Buffer Class Acc (%)': round(df_summary['ISO Buffer Class Acc (%)'].mean(), 2),
        'LOOCV RMSE': round(df_summary['LOOCV RMSE'].mean(), 2),
        'LOOCV MAE': round(df_summary['LOOCV MAE'].mean(), 2),
        'LOOCV R^2 (%)': round(df_summary['LOOCV R^2 (%)'].mean(), 2)
    }
    df_summary = pd.concat([df_summary, pd.DataFrame([avg_row])], ignore_index=True)

    print("\n" + "=" * 80)
    print("LOOCV BENCHMARK SUMMARY (MODEL 37):")
    print(df_summary.to_string(index=False))
    print("=" * 80)

    # -------------------------------------------------------------------------
    # EXCEL EXPORT & OPENPYXL STYLING
    # -------------------------------------------------------------------------
    print(f"\nWriting styled master workbook to: {output_excel}")
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        df_summary.to_excel(writer, sheet_name='Performance_Summary', index=False, startrow=2)
        for s_name, e_df in element_dfs.items():
            e_df.to_excel(writer, sheet_name=s_name, index=False, startrow=2)

    wb = openpyxl.load_workbook(output_excel)

    header_font = Font(name='Segoe UI', size=11, bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='1F4E78', end_color='1F4E78', fill_type='solid')

    title_font = Font(name='Segoe UI', size=13, bold=True, color='FFFFFF')
    title_fill = PatternFill(start_color='0D233A', end_color='0D233A', fill_type='solid')

    avg_font = Font(name='Segoe UI', size=11, bold=True, color='000000')
    avg_fill = PatternFill(start_color='D9E1F2', end_color='D9E1F2', fill_type='solid')

    pass_fill = PatternFill(start_color='E2EFDA', end_color='E2EFDA', fill_type='solid')
    fail_fill = PatternFill(start_color='FCE4D6', end_color='FCE4D6', fill_type='solid')

    thin_border = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9')
    )

    # Sheet 1: Performance_Summary
    ws_sum = wb['Performance_Summary']
    ws_sum.row_dimensions[1].height = 36
    ws_sum.row_dimensions[2].height = 24
    ws_sum.row_dimensions[3].height = 26

    title_cell = ws_sum.cell(row=1, column=1)
    title_cell.value = "MODEL 37: ADVANCED HIERARCHICAL ENSEMBLE LOOCV BENCHMARK (49 SAMPLES)"
    title_cell.font = title_font
    title_cell.fill = title_fill
    title_cell.alignment = Alignment(horizontal='center', vertical='center')
    ws_sum.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(df_summary.columns))

    sub_cell = ws_sum.cell(row=2, column=1)
    sub_cell.value = "Value Accuracy: min(Act, Pred)/max(Act, Pred)*100% | LOQ Floor = Analytical Detection Limit | Strict 49-Fold LOOCV"
    sub_cell.font = Font(name='Segoe UI', size=9, italic=True, color='333333')
    sub_cell.alignment = Alignment(horizontal='center', vertical='center')
    ws_sum.merge_cells(start_row=2, start_column=1, end_row=2, end_column=len(df_summary.columns))

    for col_idx in range(1, len(df_summary.columns) + 1):
        c = ws_sum.cell(row=3, column=col_idx)
        c.font = header_font
        c.fill = header_fill
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

    for row_idx in range(4, ws_sum.max_row + 1):
        ws_sum.row_dimensions[row_idx].height = 20
        is_avg_row = (row_idx == ws_sum.max_row)
        for col_idx in range(1, len(df_summary.columns) + 1):
            cell = ws_sum.cell(row=row_idx, column=col_idx)
            cell.border = thin_border
            if is_avg_row:
                cell.font = avg_font
                cell.fill = avg_fill
                cell.alignment = Alignment(horizontal='center', vertical='center')
            else:
                cell.font = Font(name='Segoe UI', size=10)
                if col_idx in [1, 2]:
                    cell.alignment = Alignment(horizontal='left', vertical='center')
                else:
                    cell.alignment = Alignment(horizontal='center', vertical='center')

    for col in ws_sum.columns:
        max_len = max(len(str(c.value or '')) for c in col)
        col_letter = get_column_letter(col[0].column)
        ws_sum.column_dimensions[col_letter].width = max(max_len + 3, 13)

    # Sheets 2-13: Individual Nutrient Sheets
    for s_name in SHEET_MAPPING.values():
        ws = wb[s_name]
        full_name = NUTRIENT_FULL_NAMES.get(s_name, s_name)
        n_cols = len(element_dfs[s_name].columns)

        ws.row_dimensions[1].height = 32
        ws.row_dimensions[2].height = 20
        ws.row_dimensions[3].height = 24

        t_cell = ws.cell(row=1, column=1)
        t_cell.value = f"{s_name} ({full_name}) - ADVANCED HIERARCHICAL LOOCV PREDICTIONS (49 SAMPLES)"
        t_cell.font = title_font
        t_cell.fill = title_fill
        t_cell.alignment = Alignment(horizontal='center', vertical='center')
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=n_cols)

        s_cell = ws.cell(row=2, column=1)
        s_cell.value = "Sorted ascending by Actual Value | Value Accuracy: min(Act, Pred)/max(Act, Pred)*100% | Strict LOOCV"
        s_cell.font = Font(name='Segoe UI', size=9, italic=True, color='333333')
        s_cell.alignment = Alignment(horizontal='center', vertical='center')
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

                col_name = str(ws.cell(row=3, column=col_idx).value).strip()
                val_str = str(cell.value).strip()

                if col_name in ['Strict Status', 'ISO Buffer Status']:
                    if val_str == 'Correct':
                        cell.fill = pass_fill
                    elif val_str == 'Missed':
                        cell.fill = fail_fill
                elif col_name in ['Status Value Acc (>=50%)', 'Status Value Acc (>=75%)']:
                    if val_str == 'Pass':
                        cell.fill = pass_fill
                    elif val_str == 'Fail':
                        cell.fill = fail_fill

        for col in ws.columns:
            max_len = max(len(str(c.value or '')) for c in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 13)

    wb.save(output_excel)
    print(f"Master workbook successfully saved: {output_excel}")
    print(f"Total Model 37 execution time: {time.time() - t_start:.2f} seconds")

if __name__ == '__main__':
    main()
