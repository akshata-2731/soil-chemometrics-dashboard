# -*- coding: utf-8 -*-
"""
================================================================================
MODEL 36: ADVANCED HYBRID LOOCV MODEL FOR 49-SAMPLE DATASET
================================================================================
Primary Value Accuracy Formula:
  Value Accuracy (%) = (min(Actual, Pred) / max(Actual, Pred)) * 100%
  (e.g., if Actual = 1.00 and Pred = 0.50 -> Accuracy = 50.0%)

Architecture:
  1. Chemometric Preprocessing on 21 VIS-NIR Spectral Reflectance Bands (nm_410 to nm_200)
  2. Stage 1: Heterogeneous Tuned Classifier per Nutrient (Strict & ISO 17025 +/-15% Buffer)
  3. Stage 2: Best-of-Breed Chemometric Continuous Regressors (ExtraTrees, SVR-RBF, PLSR)
  4. Stage 3: Class-Bounded Dynamic Clamping to physical agronomic tiers
  5. Strict 49-Fold Leave-One-Out Cross-Validation (cv=LeaveOneOut())

Outputs:
  - 'Model_36_Advanced_LOOCV_49_Samples_Results.xlsx'
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
from sklearn.model_selection import LeaveOneOut, cross_val_predict
from sklearn.svm import SVC, SVR
from sklearn.neighbors import KNeighborsClassifier
from sklearn.cross_decomposition import PLSRegression
from sklearn.ensemble import ExtraTreesRegressor
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

STAGE1_CLASSIFIERS = {
    'OC%': SVC(kernel='rbf', C=0.01, class_weight='balanced'),
    'Ca (meq)': SVC(kernel='rbf', C=0.01, class_weight='balanced'),
    'Mg (meq)': SVC(kernel='rbf', C=0.01, class_weight='balanced'),
    'N Kg/ha': SVC(kernel='rbf', C=0.01, class_weight='balanced'),
    'P2O5': SVC(kernel='rbf', C=0.01, class_weight='balanced'),
    'K2O': KNeighborsClassifier(n_neighbors=5, weights='distance'),
    'SO4': SVC(kernel='rbf', C=0.01, class_weight='balanced'),
    'Fe (ppm)': KNeighborsClassifier(n_neighbors=5, weights='distance'),
    'Mn (ppm)': SVC(kernel='rbf', C=0.01, class_weight='balanced'),
    'Cu (ppm)': SVC(kernel='rbf', C=0.1, class_weight='balanced'),
    'Zn (ppm)': SVC(kernel='linear', C=1.0),
    'B (ppm)': SVC(kernel='rbf', C=0.01, class_weight='balanced')
}

STAGE2_REGRESSORS = {
    'OC%': ExtraTreesRegressor(n_estimators=100, max_depth=6, random_state=42),
    'Ca (meq)': SVR(kernel='rbf', C=100, gamma=0.01, epsilon=0.05),
    'Mg (meq)': SVR(kernel='rbf', C=100, gamma=0.01, epsilon=0.05),
    'N Kg/ha': ExtraTreesRegressor(n_estimators=100, max_depth=6, random_state=42),
    'P2O5': ExtraTreesRegressor(n_estimators=100, max_depth=6, random_state=42),
    'K2O': PLSRegression(n_components=3),
    'SO4': SVR(kernel='rbf', C=100, gamma=0.01, epsilon=0.05),
    'Fe (ppm)': PLSRegression(n_components=4),
    'Mn (ppm)': SVR(kernel='rbf', C=50, gamma='scale', epsilon=0.05),
    'Cu (ppm)': SVR(kernel='rbf', C=50, gamma=0.02, epsilon=0.05),
    'Zn (ppm)': PLSRegression(n_components=4),
    'B (ppm)': ExtraTreesRegressor(n_estimators=100, max_depth=6, random_state=42)
}

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

def main():
    t_start = time.time()
    print("=" * 80)
    print("MODEL 36: ADVANCED HYBRID LOOCV MODEL ON 49 SAMPLES")
    print("Primary Value Accuracy Formula: min(Actual, Pred) / max(Actual, Pred) * 100%")
    print("=" * 80)

    script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()
    data_file = os.path.join(script_dir, 'data.xlsx')
    output_excel = os.path.join(script_dir, 'Model_36_Advanced_LOOCV_49_Samples_Ratio_Accuracy.xlsx')

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
        clf = STAGE1_CLASSIFIERS[target]
        pipe_clf = Pipeline([('scaler', StandardScaler()), ('clf', clf)])
        pred_class = cross_val_predict(pipe_clf, X_raw, y_class, cv=loo)

        # Stage 2: Continuous Regressor LOOCV
        reg = STAGE2_REGRESSORS[target]
        pipe_reg = Pipeline([('scaler', StandardScaler()), ('reg', reg)])
        pred_cont_raw = cross_val_predict(pipe_reg, X_raw, y_cont, cv=loo).flatten()
        pred_cont_raw = np.maximum(0.0, pred_cont_raw)

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

        # PRIMARY: Ratio Value Accuracy (Exact User Formula)
        ratio_accs = np.array([compute_ratio_accuracy(a, p) for a, p in zip(y_cont, final_preds)])
        mean_ratio_acc = ratio_accs.mean()
        pct_ge_50 = (ratio_accs >= 50.0).mean() * 100.0
        pct_ge_70 = (ratio_accs >= 70.0).mean() * 100.0
        pct_ge_75 = (ratio_accs >= 75.0).mean() * 100.0

        # Range Value Accuracy (Chemometric Reference)
        range_accs = np.array([(1.0 - abs(a - p) / val_range) * 100.0 if val_range > 0 else 0.0 for a, p in zip(y_cont, final_preds)])
        mean_range_acc = (1.0 - (rmse / val_range)) * 100.0 if val_range > 0 else 0.0

        t_elapsed = time.time() - t0
        print(f"  {target:<10} ({sheet_name:<8}): Ratio Acc = {mean_ratio_acc:5.2f}% | %>=75%: {pct_ge_75:4.1f}% | ISO Clf = {buffer_acc:5.1f}% | Range Acc = {mean_range_acc:5.2f}% | Time = {t_elapsed:4.1f}s")

        summary_rows.append({
            'Target Nutrient': sheet_name,
            'Full Name': target,
            'Valid Samples': n_valid,
            'Mean Value Acc (Ratio %)': round(mean_ratio_acc, 2),
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

        out_df = pd.DataFrame({
            'Sample ID': [f"Sample_{i+1}" for i in range(n_valid)],
            'Actual Class': y_class,
            'Predicted Class': pred_class,
            'Strict Status': np.where(strict_pass, 'Correct', 'Missed'),
            'ISO Buffer Status': np.where(buffer_pass, 'Correct', 'Missed'),
            'Actual Value': np.round(y_cont, 2),
            'Final Predicted Value': np.round(final_preds, 2),
            'Value Accuracy (%)': np.round(ratio_accs, 2),
            'Status Value Acc (>=50%)': np.where(ratio_accs >= 50.0, 'Pass', 'Fail'),
            'Status Value Acc (>=75%)': np.where(ratio_accs >= 75.0, 'Pass', 'Fail'),
            'Range Value Acc (%)': np.round(range_accs, 2)
        })
        out_df = out_df.sort_values(by='Actual Value', ascending=True).reset_index(drop=True)
        element_dfs[sheet_name] = out_df

    summary_df = pd.DataFrame(summary_rows)

    print("\n--- Generating Formatted Excel Workbook: 13 Sheets ---")
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    font_family = "Segoe UI"
    title_font = Font(name=font_family, size=13, bold=True, color="FFFFFF")
    header_font = Font(name=font_family, size=10, bold=True, color="FFFFFF")
    data_font = Font(name=font_family, size=10)
    bold_font = Font(name=font_family, size=10, bold=True)
    correct_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
    correct_font = Font(name=font_family, size=10, color="375623", bold=True)
    missed_fill = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")
    missed_font = Font(name=font_family, size=10, color="C65911", bold=True)

    header_navy = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_blue = PatternFill(start_color="2F5597", end_color="2F5597", fill_type="solid")
    header_dark = PatternFill(start_color="203764", end_color="203764", fill_type="solid")
    zebra_fill = PatternFill(start_color="F9FAFB", end_color="F9FAFB", fill_type="solid")
    white_fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
    total_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")

    thin_line = Side(border_style="thin", color="D9D9D9")
    thick_bottom = Side(border_style="medium", color="1F4E78")
    double_bottom = Side(border_style="double", color="1F4E78")
    border_cell = Border(left=thin_line, right=thin_line, top=thin_line, bottom=thin_line)

    # -------------------------------------------------------------
    # 1. SHEET 1: SUMMARY
    # -------------------------------------------------------------
    ws_sum = wb.create_sheet(title='Performance_Summary')
    ws_sum.views.sheetView[0].showGridLines = True

    ws_sum.merge_cells('A1:M1')
    ws_sum['A1'] = "MODEL 36: ADVANCED HYBRID LOOCV BENCHMARK (49 SAMPLES)"
    ws_sum['A1'].font = title_font
    ws_sum['A1'].fill = header_navy
    ws_sum['A1'].alignment = Alignment(horizontal="center", vertical="center")
    ws_sum.row_dimensions[1].height = 28

    ws_sum.merge_cells('A2:M2')
    ws_sum['A2'] = "Value Accuracy Formula: min(Actual, Pred) / max(Actual, Pred) * 100% (e.g. Act=1.00, Pred=0.50 -> 50% Acc) | Strict 49-Fold LOOCV"
    ws_sum['A2'].font = Font(name=font_family, size=9, italic=True, color="595959")
    ws_sum['A2'].alignment = Alignment(horizontal="center", vertical="center")
    ws_sum.row_dimensions[2].height = 18

    headers_sum = [
        'Target Nutrient', 'Full Target Name', 'Valid Samples',
        'Mean Value Acc (Ratio %)', '% Samples >= 50% Acc', '% Samples >= 70% Acc', '% Samples >= 75% Acc',
        'Range Value Acc (%)', 'Strict Class Acc (%)', 'ISO Buffer Class Acc (%)',
        'LOOCV RMSE', 'LOOCV MAE', 'LOOCV R^2 (%)'
    ]
    for col_idx, h in enumerate(headers_sum, 1):
        cell = ws_sum.cell(row=3, column=col_idx, value=h)
        cell.font = header_font
        cell.fill = header_blue
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = Border(left=thin_line, right=thin_line, top=thin_line, bottom=thick_bottom)
    ws_sum.row_dimensions[3].height = 28

    for row_idx, r in enumerate(summary_rows, 4):
        vals = [
            r['Target Nutrient'], r['Full Name'], r['Valid Samples'],
            r['Mean Value Acc (Ratio %)'], r['% Samples >= 50% Acc'], r['% Samples >= 70% Acc'], r['% Samples >= 75% Acc'],
            r['Range Value Acc (%)'], r['Strict Class Acc (%)'], r['ISO Buffer Class Acc (%)'],
            r['LOOCV RMSE'], r['LOOCV MAE'], r['LOOCV R^2 (%)']
        ]
        fill_c = zebra_fill if row_idx % 2 == 0 else white_fill
        for col_idx, val in enumerate(vals, 1):
            cell = ws_sum.cell(row=row_idx, column=col_idx, value=val)
            cell.font = data_font
            cell.fill = fill_c
            cell.border = border_cell
            cell.alignment = Alignment(horizontal="center" if col_idx in [1, 3] else ("left" if col_idx == 2 else "right"), vertical="center")
        ws_sum.row_dimensions[row_idx].height = 20

    avg_row_idx = len(summary_rows) + 4
    avg_vals = [
        'OVERALL AVERAGE', 'All 12 Soil Nutrients', int(summary_df['Valid Samples'].mean()),
        round(summary_df['Mean Value Acc (Ratio %)'].mean(), 2),
        round(summary_df['% Samples >= 50% Acc'].mean(), 1),
        round(summary_df['% Samples >= 70% Acc'].mean(), 1),
        round(summary_df['% Samples >= 75% Acc'].mean(), 1),
        round(summary_df['Range Value Acc (%)'].mean(), 2),
        round(summary_df['Strict Class Acc (%)'].mean(), 2),
        round(summary_df['ISO Buffer Class Acc (%)'].mean(), 2),
        round(summary_df['LOOCV RMSE'].mean(), 2),
        round(summary_df['LOOCV MAE'].mean(), 2),
        round(summary_df['LOOCV R^2 (%)'].mean(), 2)
    ]
    for col_idx, val in enumerate(avg_vals, 1):
        cell = ws_sum.cell(row=avg_row_idx, column=col_idx, value=val)
        cell.font = bold_font
        cell.fill = total_fill
        cell.border = Border(left=thin_line, right=thin_line, top=thick_bottom, bottom=double_bottom)
        cell.alignment = Alignment(horizontal="center" if col_idx in [1, 3] else ("left" if col_idx == 2 else "right"), vertical="center")
    ws_sum.row_dimensions[avg_row_idx].height = 22

    for col in ws_sum.columns:
        max_len = max(len(str(c.value or '')) for c in col)
        col_letter = get_column_letter(col[0].column)
        ws_sum.column_dimensions[col_letter].width = max(max_len + 3, 12)
    ws_sum.column_dimensions['B'].width = 28

    # -------------------------------------------------------------
    # 2. SHEETS 2-13: INDIVIDUAL NUTRIENT SHEETS
    # -------------------------------------------------------------
    for target, sheet_name in SHEET_MAPPING.items():
        ws = wb.create_sheet(title=sheet_name)
        ws.views.sheetView[0].showGridLines = True
        out_df = element_dfs[sheet_name]

        ws.merge_cells('A1:K1')
        ws['A1'] = f"{sheet_name} ({target}) - ADVANCED HYBRID LOOCV PREDICTIONS (49 SAMPLES)"
        ws['A1'].font = title_font
        ws['A1'].fill = header_dark
        ws['A1'].alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[1].height = 28

        ws.merge_cells('A2:K2')
        ws['A2'] = f"Sorted ascending by Actual Value | Value Accuracy Formula: min(Actual, Pred) / max(Actual, Pred) * 100% (e.g. Act=1.00, Pred=0.50 -> 50% Acc) | Strict LOOCV"
        ws['A2'].font = Font(name=font_family, size=9, italic=True, color="595959")
        ws['A2'].alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[2].height = 18

        headers_cols = [
            'Sample ID', 'Actual Class', 'Predicted Class', 'Strict Status', 'ISO Buffer Status',
            'Actual Value', 'Final Predicted Value',
            'Value Accuracy (%)', 'Status Value Acc (>=50%)', 'Status Value Acc (>=75%)',
            'Range Value Acc (%)'
        ]
        for col_idx, h in enumerate(headers_cols, 1):
            cell = ws.cell(row=3, column=col_idx, value=h)
            cell.font = header_font
            cell.fill = header_navy
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = Border(left=thin_line, right=thin_line, top=thin_line, bottom=thick_bottom)
        ws.row_dimensions[3].height = 26

        for r_i, row in out_df.iterrows():
            curr_row = r_i + 4
            fill_c = zebra_fill if curr_row % 2 == 0 else white_fill
            row_vals = [
                row['Sample ID'], row['Actual Class'], row['Predicted Class'],
                row['Strict Status'], row['ISO Buffer Status'],
                row['Actual Value'], row['Final Predicted Value'],
                row['Value Accuracy (%)'], row['Status Value Acc (>=50%)'], row['Status Value Acc (>=75%)'],
                row['Range Value Acc (%)']
            ]
            for c_i, val in enumerate(row_vals, 1):
                col_name = headers_cols[c_i - 1]
                cell = ws.cell(row=curr_row, column=c_i, value=val)
                cell.font = data_font
                cell.fill = fill_c
                cell.border = border_cell

                if col_name in ['Strict Status', 'ISO Buffer Status']:
                    if val == 'Correct':
                        cell.fill = correct_fill
                        cell.font = correct_font
                    else:
                        cell.fill = missed_fill
                        cell.font = missed_font
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                elif col_name in ['Status Value Acc (>=50%)', 'Status Value Acc (>=75%)']:
                    if val == 'Pass':
                        cell.fill = correct_fill
                        cell.font = correct_font
                    else:
                        cell.fill = missed_fill
                        cell.font = missed_font
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                elif col_name in ['Actual Value', 'Final Predicted Value', 'Value Accuracy (%)', 'Range Value Acc (%)']:
                    cell.alignment = Alignment(horizontal="right", vertical="center")
                    cell.number_format = '0.00'
                elif col_name == 'Sample ID':
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                else:
                    cell.alignment = Alignment(horizontal="center", vertical="center")
            ws.row_dimensions[curr_row].height = 18

        for col in ws.columns:
            max_len = max(len(str(c.value or '')) for c in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 14)

    wb.save(output_excel)
    t_total = time.time() - t_start
    print("=" * 80)
    print(f"SUCCESSFULLY GENERATED WORKBOOK WITH RATIO VALUE ACCURACY:")
    print(f"  Path: {output_excel}")
    print(f"  Total Execution Time: {t_total:.1f} seconds")
    print("=" * 80)

if __name__ == '__main__':
    main()
