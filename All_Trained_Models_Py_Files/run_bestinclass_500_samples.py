# -*- coding: utf-8 -*-
"""
Best-In-Class Two-Stage Soil Spectral Model for 500 Samples
===========================================================
Executes:
  1. Full LOOCV on all 502 samples in data.xlsx using parallel workers (n_jobs=-1).
  2. Stage 1: Balanced Actionable Classifier (SVC RBF balanced / Ridge).
  3. Stage 2: 3D Chemometric PLSR Regressor.
  4. Stage 3: Class-Bounded Dynamic Variance Scaling with Exact Physical Limits.
  5. Outputs Actual_vs_Predicted_BestInClass_500_Samples.xlsx matching the 12-sheet
     structure of Actual_vs_Predicted_BestInClass.xlsx, sorted by Actual Value.
  6. Saves final production .pkl pipelines to Final_PKL_Models_BestInClass_500/.
"""

import os
import time
import pickle
import warnings
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import pandas as pd
import numpy as np
from sklearn.model_selection import LeaveOneOut, cross_val_predict
from sklearn.svm import SVC
from sklearn.linear_model import RidgeClassifier
from sklearn.cross_decomposition import PLSRegression
from sklearn.preprocessing import StandardScaler, MinMaxScaler
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

def main():
    t_start = time.time()
    print("=" * 75)
    print("STARTING BEST-IN-CLASS TWO-STAGE MODEL ON 500 SAMPLES")
    print("=" * 75)

    script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()
    data_file = os.path.join(script_dir, 'data.xlsx')
    output_excel = os.path.join(script_dir, 'Actual_vs_Predicted_BestInClass_500_Samples.xlsx')
    model_dir = os.path.join(script_dir, 'Final_PKL_Models_BestInClass_500')
    os.makedirs(model_dir, exist_ok=True)

    df = pd.read_excel(data_file)
    spec_cols = [c for c in df.columns if c.startswith('nm_')]
    print(f"Loaded dataset: {df.shape[0]} total samples, {len(spec_cols)} spectral wavelengths.")

    loo = LeaveOneOut()
    summary_rows = []
    element_dfs = {}

    for target, sheet_name in SHEET_MAPPING.items():
        t0 = time.time()
        active_rules = CLASS_RULES[target]
        # Robust numeric parsing to handle potential typos
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

        # Stage 1: Classifier (Use balanced SVC or Ridge depending on target)
        if target == 'K2O':
            clf = RidgeClassifier(class_weight='balanced')
        else:
            clf = SVC(kernel='rbf', C=0.1, class_weight='balanced')

        clf_pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('clf', clf)
        ])

        # Stage 2: Chemometric PLSR Regressor
        n_comps = 3 if n_valid >= 10 else 2
        reg_pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('pls', PLSRegression(n_components=n_comps))
        ])

        # Parallel LOOCV Execution (n_jobs=-1 for high speed)
        Y_pred_class = cross_val_predict(clf_pipeline, X_raw, y_class, cv=loo, n_jobs=-1)
        Y_pred_cont_raw = cross_val_predict(reg_pipeline, X_raw, y_cont, cv=loo, n_jobs=-1).flatten()
        Y_pred_cont_raw = np.maximum(0.0, Y_pred_cont_raw)

        # Stage 3: Class-Bounded Dynamic Variance Scaling (Adapted to 500-Sample Dynamic Range)
        Y_pred_cont_final = np.zeros_like(Y_pred_cont_raw)
        for p_class in np.unique(Y_pred_class):
            idx = (Y_pred_class == p_class)
            raw_vals = Y_pred_cont_raw[idx]
            if p_class in active_rules:
                rule_low, rule_high = active_rules[p_class]
                low_b = max(rule_low, float(y_cont.min()))
                high_b = min(rule_high, float(y_cont.max()))
                if high_b <= low_b:
                    high_b = low_b + 0.05 * val_range
                # Bound continuous predictions within physical limits without artificial flattening
                Y_pred_cont_final[idx] = np.clip(raw_vals, low_b, high_b)
            else:
                Y_pred_cont_final[idx] = raw_vals

        # Metrics
        clf_acc = (y_class == Y_pred_class).mean() * 100.0
        rmse = np.sqrt(mean_squared_error(y_cont, Y_pred_cont_final))
        mae = mean_absolute_error(y_cont, Y_pred_cont_final)
        r2 = r2_score(y_cont, Y_pred_cont_final)
        nrmse_acc = (1.0 - (rmse / val_range)) * 100.0 if val_range > 0 else 0.0
        pct_sample_ge_70 = np.mean([(1.0 - abs(a - p)/val_range) >= 0.70 for a, p in zip(y_cont, Y_pred_cont_final)]) * 100.0
        pct_sample_ge_75 = np.mean([(1.0 - abs(a - p)/val_range) >= 0.75 for a, p in zip(y_cont, Y_pred_cont_final)]) * 100.0

        t_elapsed = time.time() - t0
        print(f"  {target:<10} ({sheet_name:<8}): Clf Acc = {clf_acc:5.1f}% | Value Acc = {nrmse_acc:5.2f}% | RMSE = {rmse:7.2f} | Time = {t_elapsed:4.1f}s")

        summary_rows.append({
            'Target Nutrient': sheet_name,
            'Full Name': target,
            'Valid Samples': n_valid,
            'Class Accuracy (%)': round(clf_acc, 2),
            'LOOCV Value Acc (%)': round(nrmse_acc, 2),
            'LOOCV RMSE': round(rmse, 4),
            'LOOCV MAE': round(mae, 4),
            'LOOCV R^2 (%)': round(r2 * 100.0, 2),
            '% Samples >= 70% Acc': round(pct_sample_ge_70, 1),
            '% Samples >= 75% Acc': round(pct_sample_ge_75, 1)
        })

        # Create output dataframe for this nutrient, sorted by Actual Value ascending
        out_df = pd.DataFrame({
            'Sample ID': valid_indices,
            'Actual Class': y_class,
            'Predicted Class': Y_pred_class,
            'Status': np.where(y_class == Y_pred_class, 'Correct', 'Missed'),
            'Actual Value': np.round(y_cont, 2),
            'Final Predicted Value': np.round(Y_pred_cont_final, 2)
        })
        out_df = out_df.sort_values(by='Actual Value', ascending=True).reset_index(drop=True)
        element_dfs[sheet_name] = out_df

        # Train Final Production Model on 100% data and save to .pkl
        clf_pipeline.fit(X_raw, y_class)
        reg_pipeline.fit(X_raw, y_cont)
        y_pred_class_100 = clf_pipeline.predict(X_raw)
        y_pred_cont_100 = reg_pipeline.predict(X_raw).flatten()
        y_pred_cont_100 = np.maximum(0, y_pred_cont_100)

        class_scalers = {}
        for p_class in np.unique(y_pred_class_100):
            if p_class in active_rules:
                rule_low, rule_high = active_rules[p_class]
                low_b = max(rule_low, float(y_cont.min()))
                high_b = min(rule_high, float(y_cont.max()))
                if high_b <= low_b:
                    high_b = low_b + 0.05 * val_range
                class_scalers[p_class] = (low_b, high_b)

        model_bundle = {
            'classifier': clf_pipeline,
            'regressor': reg_pipeline,
            'rules': active_rules,
            'scalers': class_scalers,
            'target_name': target,
            'n_samples_trained': n_valid
        }
        pkl_name = f"{sheet_name.replace(' ', '_')}_Master_Model.pkl"
        with open(os.path.join(model_dir, pkl_name), 'wb') as f:
            pickle.dump(model_bundle, f)

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
    border_header = Border(left=thin_line, right=thin_line, top=thin_line, bottom=thick_bottom)
    border_total = Border(left=thin_line, right=thin_line, top=thin_line, bottom=double_bottom)

    # -------------------------------------------------------------
    # SHEET 1: BestInClass_Summary
    # -------------------------------------------------------------
    ws_sum = wb.create_sheet(title="BestInClass_Summary")
    ws_sum.views.sheetView[0].showGridLines = True

    ws_sum.merge_cells("A1:J1")
    t1 = ws_sum["A1"]
    t1.value = "BEST-IN-CLASS TWO-STAGE MODEL PERFORMANCE BENCHMARK (500 SAMPLES)"
    t1.font = title_font
    t1.fill = header_dark
    t1.alignment = Alignment(horizontal="center", vertical="center")
    ws_sum.row_dimensions[1].height = 36

    ws_sum.merge_cells("A2:J2")
    sub1 = ws_sum["A2"]
    sub1.value = "Strict 502-Fold Leave-One-Out Cross-Validation (LOOCV) | Actionable Classifier + 3D PLSR + Dynamic Variance Scaling"
    sub1.font = Font(name=font_family, size=9, italic=True, color="D9E1F2")
    sub1.fill = header_dark
    sub1.alignment = Alignment(horizontal="center", vertical="center")
    ws_sum.row_dimensions[2].height = 20

    sum_cols = [
        "Target Nutrient", "Full Target Name", "Valid Samples",
        "Class Accuracy (%)", "LOOCV Value Acc (%)", "LOOCV RMSE", "LOOCV MAE",
        "LOOCV R^2 (%)", "% Samples >= 70% Acc", "% Samples >= 75% Acc"
    ]
    ws_sum.append([])
    ws_sum.append(sum_cols)
    ws_sum.row_dimensions[4].height = 26

    for col_idx, col_name in enumerate(sum_cols, 1):
        c = ws_sum.cell(row=4, column=col_idx)
        c.font = header_font
        c.fill = header_navy
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = border_header

    for r_idx, row_data in enumerate(summary_rows, 5):
        vals = [
            row_data['Target Nutrient'], row_data['Full Name'], row_data['Valid Samples'],
            row_data['Class Accuracy (%)'], row_data['LOOCV Value Acc (%)'],
            row_data['LOOCV RMSE'], row_data['LOOCV MAE'], row_data['LOOCV R^2 (%)'],
            row_data['% Samples >= 70% Acc'], row_data['% Samples >= 75% Acc']
        ]
        ws_sum.append(vals)
        ws_sum.row_dimensions[r_idx].height = 20
        fill = zebra_fill if r_idx % 2 == 0 else white_fill
        for c_idx in range(1, len(vals) + 1):
            cell = ws_sum.cell(row=r_idx, column=c_idx)
            cell.font = data_font
            cell.fill = fill
            cell.border = border_cell
            if c_idx in [1, 2]:
                cell.alignment = Alignment(horizontal="left", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="right", vertical="center")
            if c_idx in [4, 5]:
                cell.font = bold_font

    # Total Row
    tot_row = 5 + len(summary_rows)
    ws_sum.row_dimensions[tot_row].height = 24
    ws_sum.cell(row=tot_row, column=1, value="OVERALL AVERAGE")
    ws_sum.cell(row=tot_row, column=2, value="All 12 Soil Nutrients")
    ws_sum.cell(row=tot_row, column=3, value=int(summary_df['Valid Samples'].mean()))
    ws_sum.cell(row=tot_row, column=4, value=round(summary_df['Class Accuracy (%)'].mean(), 2))
    ws_sum.cell(row=tot_row, column=5, value=round(summary_df['LOOCV Value Acc (%)'].mean(), 2))
    ws_sum.cell(row=tot_row, column=6, value=round(summary_df['LOOCV RMSE'].mean(), 2))
    ws_sum.cell(row=tot_row, column=7, value=round(summary_df['LOOCV MAE'].mean(), 2))
    ws_sum.cell(row=tot_row, column=8, value=round(summary_df['LOOCV R^2 (%)'].mean(), 2))
    ws_sum.cell(row=tot_row, column=9, value=round(summary_df['% Samples >= 70% Acc'].mean(), 1))
    ws_sum.cell(row=tot_row, column=10, value=round(summary_df['% Samples >= 75% Acc'].mean(), 1))

    for c_idx in range(1, len(sum_cols) + 1):
        c = ws_sum.cell(row=tot_row, column=c_idx)
        c.font = bold_font
        c.fill = total_fill
        c.border = border_total
        if c_idx in [1, 2]:
            c.alignment = Alignment(horizontal="left", vertical="center")
        else:
            c.alignment = Alignment(horizontal="right", vertical="center")

    for col in ws_sum.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws_sum.column_dimensions[col_letter].width = max(max_len + 3, 14)

    # -------------------------------------------------------------
    # SHEETS 2 TO 13: 12 Nutrient Sheets
    # -------------------------------------------------------------
    for sheet_name, df_elem in element_dfs.items():
        ws = wb.create_sheet(title=sheet_name)
        ws.views.sheetView[0].showGridLines = True

        ws.merge_cells("A1:F1")
        top_c = ws["A1"]
        top_c.value = f"{sheet_name.upper()} - TWO-STAGE LOOCV PREDICTIONS (500 SAMPLES)"
        top_c.font = title_font
        top_c.fill = header_navy
        top_c.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[1].height = 30

        cols = ['Sample ID', 'Actual Class', 'Predicted Class', 'Status', 'Actual Value', 'Final Predicted Value']
        ws.append(cols)
        ws.row_dimensions[2].height = 24

        for col_idx, col_name in enumerate(cols, 1):
            c = ws.cell(row=2, column=col_idx)
            c.font = header_font
            c.fill = header_blue
            c.alignment = Alignment(horizontal="center", vertical="center")
            c.border = border_header

        for r_idx, row in df_elem.iterrows():
            curr_row = r_idx + 3
            ws.append(row.tolist())
            ws.row_dimensions[curr_row].height = 19
            fill = zebra_fill if curr_row % 2 == 0 else white_fill

            for c_idx in range(1, len(cols) + 1):
                cell = ws.cell(row=curr_row, column=c_idx)
                cell.font = data_font
                cell.fill = fill
                cell.border = border_cell

                if c_idx in [1, 5, 6]:
                    cell.alignment = Alignment(horizontal="right", vertical="center")
                else:
                    cell.alignment = Alignment(horizontal="center", vertical="center")

                if c_idx == 4:
                    if cell.value == 'Correct':
                        cell.fill = correct_fill
                        cell.font = correct_font
                    else:
                        cell.fill = missed_fill
                        cell.font = missed_font

        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col[:55])
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 15)

    wb.save(output_excel)
    total_time = time.time() - t_start
    print(f"\n Master Workbook Successfully Created: '{output_excel}' in {total_time:.1f} seconds!")
    print(f"Production Models Saved to: '{model_dir}/'")

if __name__ == '__main__':
    main()
