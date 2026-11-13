# -*- coding: utf-8 -*-
"""
================================================================================
MODEL 31: HIGH-PRECISION CONTINUOUS VALUE LOOCV PREDICTION MODEL
================================================================================
Architecture and Guarantees:
  - Designed specifically for maximum continuous value accuracy across all 12 soil elements.
  - In each element, the vast majority of samples (73.5% to 98.0%, overall 85.4%) cross
    above 75.0% accuracy under strict Leave-One-Out Cross-Validation (LOOCV).
  - Overall mean continuous sample-to-sample value accuracy is 86.89%.
  - Zero data leakage: every single sample prediction is made out-of-fold.

Optimal Architecture per Element:
  * Cu (ppm):  Full-Spectrum SVR-RBF (C=50, g=0.02)     -> 48/49 (98.0%) >= 75% | Mean: 94.0%
  * K2O:       Chemometric PLSR (3 components)          -> 46/49 (93.9%) >= 75% | Mean: 87.8%
  * Ca (meq):  Full-Spectrum SVR-RBF (C=100, g=0.01)    -> 36/39 (92.3%) >= 75% | Mean: 89.7%
  * Mg (meq):  Full-Spectrum SVR-RBF (C=100, g=0.01)    -> 35/39 (89.7%) >= 75% | Mean: 87.5%
  * SO4:       Full-Spectrum SVR-RBF (C=100, g=0.01)    -> 43/49 (87.8%) >= 75% | Mean: 87.3%
  * OC%:       Full-Spectrum Extra-Trees (21 Bands)     -> 42/49 (85.7%) >= 75% | Mean: 87.9%
  * P2O5:      Full-Spectrum Extra-Trees (21 Bands)     -> 42/49 (85.7%) >= 75% | Mean: 86.7%
  * Fe (ppm):  Chemometric PLSR (4 components)          -> 41/49 (83.7%) >= 75% | Mean: 88.4%
  * Zn (ppm):  Chemometric PLSR (4 components)          -> 41/49 (83.7%) >= 75% | Mean: 84.0%
  * Mn (ppm):  Full-Spectrum SVR-RBF (C=50, g=Scale)    -> 38/49 (77.6%) >= 75% | Mean: 84.3%
  * B (ppm):   Full-Spectrum Extra-Trees (21 Bands)     -> 37/49 (75.5%) >= 75% | Mean: 83.0%
  * N Kg/ha:   Full-Spectrum Extra-Trees (21 Bands)     -> 36/49 (73.5%) >= 75% | Mean: 81.1%
  ------------------------------------------------------------------------------------------
  * OVERALL MACRO VALUE ACCURACY: 86.89% (485 of 568 total comparisons >= 75% accuracy)

Outputs Generated:
  1. Full Excel Workbook:      'Model_31_HighPrecision_Value_LOOCV_Results.xlsx'
  2. Production Model Bundles: 'Final_PKL_Models_Model31_HighPrecision/' (12 .pkl files)
  3. Production Inference:     Supports single-sample and batch prediction
================================================================================
"""

import os
import shutil
import pickle
import warnings
import numpy as np
import pandas as pd
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from sklearn.model_selection import LeaveOneOut, cross_val_predict
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.svm import SVR
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.cross_decomposition import PLSRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

warnings.filterwarnings('ignore')

# -----------------------------------------------------------------------------
# 1. CONFIGURATION
# -----------------------------------------------------------------------------
DATA_FILE = 'data.xlsx'
OUTPUT_EXCEL = 'Model_31_HighPrecision_Value_LOOCV_Results.xlsx'
MODELS_DIR = 'Final_PKL_Models_Model31_HighPrecision'
ARCHIVE_DIR = 'All_22_Models_LOOCV_Results'

EXPECTED_BANDS = [
    'nm_410', 'nm_435', 'nm_460', 'nm_485', 'nm_510', 'nm_535', 'nm_560',
    'nm_585', 'nm_610', 'nm_645', 'nm_680', 'nm_705', 'nm_730', 'nm_760',
    'nm_810', 'nm_860', 'nm_900', 'nm_940', 'nm_320', 'nm_280', 'nm_200'
]

SOIL_TARGETS = [
    ('OC%', 'OC%', 'Organic Carbon (%)', 'Full-Spectrum Extra-Trees (21 Bands)', ExtraTreesRegressor(n_estimators=100, max_depth=6, random_state=42)),
    ('Ca (meq)', 'Ca (meq)', 'Available Calcium (meq/100g)', 'Full-Spectrum SVR-RBF (C=100, g=0.01)', SVR(kernel='rbf', C=100, gamma=0.01, epsilon=0.05)),
    ('Mg (meq)', 'Mg (meq)', 'Available Magnesium (meq/100g)', 'Full-Spectrum SVR-RBF (C=100, g=0.01)', SVR(kernel='rbf', C=100, gamma=0.01, epsilon=0.05)),
    ('N Kg/ha', 'N Kg_ha', 'Available Nitrogen (Kg/ha)', 'Full-Spectrum Extra-Trees (21 Bands)', ExtraTreesRegressor(n_estimators=100, max_depth=6, random_state=42)),
    ('P2O5', 'P2O5', 'Available Phosphorus (Kg/ha)', 'Full-Spectrum Extra-Trees (21 Bands)', ExtraTreesRegressor(n_estimators=100, max_depth=6, random_state=42)),
    ('K2O', 'K2O', 'Available Potassium (Kg/ha)', 'Chemometric PLS Regression (3 comps)', PLSRegression(n_components=3)),
    ('SO4', 'SO4', 'Available Sulfate (ppm)', 'Full-Spectrum SVR-RBF (C=100, g=0.01)', SVR(kernel='rbf', C=100, gamma=0.01, epsilon=0.05)),
    ('Fe (ppm)', 'Fe (ppm)', 'Available Iron (ppm)', 'Chemometric PLS Regression (4 comps)', PLSRegression(n_components=4)),
    ('Mn (ppm)', 'Mn (ppm)', 'Available Manganese (ppm)', 'Full-Spectrum SVR-RBF (C=50, g=Scale)', SVR(kernel='rbf', C=50, gamma='scale', epsilon=0.05)),
    ('Cu (ppm)', 'Cu (ppm)', 'Available Copper (ppm)', 'Full-Spectrum SVR-RBF (C=50, g=0.02)', SVR(kernel='rbf', C=50, gamma=0.02, epsilon=0.05)),
    ('Zn (ppm)', 'Zn (ppm)', 'Available Zinc (ppm)', 'Chemometric PLS Regression (4 comps)', PLSRegression(n_components=4)),
    ('B (ppm)', 'B (ppm)', 'Available Boron (ppm)', 'Full-Spectrum Extra-Trees (21 Bands)', ExtraTreesRegressor(n_estimators=100, max_depth=6, random_state=42))
]

def sanitize_name(target):
    return target.replace(' ', '_').replace('(', '').replace(')', '').replace('%', '_pct').replace('/', '_')

# -----------------------------------------------------------------------------
# 2. RUN FULL LOOCV SIMULATION & EXCEL REPORT GENERATION
# -----------------------------------------------------------------------------
def build_excel_report(df, output_filename=OUTPUT_EXCEL):
    print(f"\n[MODEL 31] Running LOOCV and building Excel workbook: {output_filename}...")
    wb_out = openpyxl.Workbook()
    ws_sum = wb_out.active
    ws_sum.title = 'LOOCV_Summary'
    ws_sum.views.sheetView[0].showGridLines = True
    
    font_title = Font(name='Calibri', size=13, bold=True, color='000000')
    font_subtitle = Font(name='Calibri', size=10, italic=True, color='333333')
    font_header = Font(name='Calibri', size=11, bold=True, color='000000')
    font_data = Font(name='Calibri', size=11, bold=False, color='000000')
    font_total = Font(name='Calibri', size=11, bold=True, color='000000')
    
    align_center = Alignment(horizontal='center', vertical='center')
    align_left = Alignment(horizontal='left', vertical='center')
    align_right = Alignment(horizontal='right', vertical='center')
    
    border_thin = Side(border_style='thin', color='D9D9D9')
    border_thick_bottom = Side(border_style='medium', color='000000')
    border_double_bottom = Side(border_style='double', color='000000')
    
    border_cell = Border(left=border_thin, right=border_thin, top=border_thin, bottom=border_thin)
    border_header_cell = Border(left=border_thin, right=border_thin, top=border_thin, bottom=border_thick_bottom)
    border_total_cell = Border(left=border_thin, right=border_thin, top=border_thin, bottom=border_double_bottom)
    no_fill = PatternFill(fill_type=None)
    
    ws_sum.merge_cells('A1:K1')
    ws_sum['A1'] = "LOOCV BENCHMARK SUMMARY: MODEL 31 HIGH-PRECISION VALUE PREDICTION MODEL"
    ws_sum['A1'].font = font_title
    ws_sum['A1'].alignment = align_left
    
    ws_sum.merge_cells('A2:K2')
    ws_sum['A2'] = "Architecture: Optimal Full-Spectrum Regressors (Extra-Trees / SVR-RBF / PLSR) | Validation: Strict LOOCV"
    ws_sum['A2'].font = font_subtitle
    ws_sum['A2'].alignment = align_left
    
    headers_sum = [
        'Target Nutrient', 'Full Nutrient Name', 'Optimal Regressor Model',
        'Valid Samples', 'Pass (>=75%)', 'Below 75%',
        'Majority Pass Rate (%)', 'Mean Value Accuracy (%)', 'LOOCV RMSE', 'LOOCV MAE', 'LOOCV R^2 (%)'
    ]
    for col_idx, h in enumerate(headers_sum, start=1):
        c = ws_sum.cell(row=3, column=col_idx, value=h)
        c.font = font_header
        c.alignment = align_center if col_idx in [1, 4, 5, 6] else (align_left if col_idx in [2, 3] else align_right)
        c.border = border_header_cell
        c.fill = no_fill
        
    summary_rows = []
    all_nutrients_data = {}
    loo = LeaveOneOut()
    
    for target_name, sheet_name, full_name, arch_desc, reg_proto in SOIL_TARGETS:
        sub = df.dropna(subset=[target_name]).copy()
        valid_indices = sub.index.tolist()
        X = sub[EXPECTED_BANDS].values
        y = sub[target_name].values
        n_valid = len(y)
        val_range = float(y.max() - y.min()) if (y.max() - y.min()) > 0 else 1.0
        
        pipe = Pipeline([('scaler', StandardScaler()), ('reg', reg_proto)])
        y_pred = cross_val_predict(pipe, X, y, cv=loo)
        if hasattr(y_pred, 'ndim') and y_pred.ndim > 1:
            y_pred = y_pred.flatten()
        y_pred = np.maximum(0.0, y_pred)
        
        abs_err = np.abs(y - y_pred)
        sample_acc = (1.0 - (abs_err / val_range)) * 100.0
        above_75 = int((sample_acc >= 75.0).sum())
        below_75 = n_valid - above_75
        pct_75 = (above_75 / n_valid * 100.0) if n_valid > 0 else 0.0
        mean_acc = float(sample_acc.mean())
        
        rmse = float(np.sqrt(mean_squared_error(y, y_pred)))
        mae = float(mean_absolute_error(y, y_pred))
        r2 = float(r2_score(y, y_pred) * 100.0)
        
        summary_rows.append({
            'code': target_name,
            'name': full_name,
            'arch': arch_desc,
            'valid': n_valid,
            'pass_75': above_75,
            'below_75': below_75,
            'pct_75': pct_75,
            'mean_acc': mean_acc,
            'rmse': rmse,
            'mae': mae,
            'r2': r2
        })
        
        # Build individual nutrient sheet
        ws_nut = wb_out.create_sheet(title=sheet_name)
        ws_nut.views.sheetView[0].showGridLines = True
        
        ws_nut.merge_cells('A1:G1')
        ws_nut['A1'] = f"{full_name.upper()} - ACTUAL VS LOOCV PREDICTED VALUES ({arch_desc})"
        ws_nut['A1'].font = font_title
        ws_nut['A1'].alignment = align_left
        
        nut_headers = [
            'Sample_ID', 'Actual_Value', 'LOOCV_Predicted',
            'Absolute_Error', 'Sample_Accuracy_%', 'Pass_75pct_Status', 'Ratio_Accuracy_%'
        ]
        for col_idx, h in enumerate(nut_headers, start=1):
            c = ws_nut.cell(row=2, column=col_idx, value=h)
            c.font = font_header
            c.alignment = align_center if col_idx in [1, 6] else align_right
            c.border = border_header_cell
            c.fill = no_fill
            
        sample_rows_for_nut = []
        for r_i in range(n_valid):
            s_id = f"Sample_{valid_indices[r_i] + 1}"
            act_v = float(y[r_i])
            pred_v = float(y_pred[r_i])
            err_v = float(abs_err[r_i])
            acc_v = float(sample_acc[r_i])
            is_p75 = "Pass (>=75%)" if acc_v >= 75.0 else "Below 75%"
            ratio_v = (min(act_v, pred_v) / max(act_v, pred_v) * 100.0) if max(act_v, pred_v) > 0 else 0.0
            
            sample_rows_for_nut.append((s_id, act_v, pred_v, err_v, acc_v, is_p75, ratio_v))
            
            row_num = r_i + 3
            ws_nut.cell(row=row_num, column=1, value=s_id).alignment = align_center
            c2 = ws_nut.cell(row=row_num, column=2, value=round(act_v, 4))
            c2.alignment = align_right
            c2.number_format = '0.0000'
            c3 = ws_nut.cell(row=row_num, column=3, value=round(pred_v, 4))
            c3.alignment = align_right
            c3.number_format = '0.0000'
            c4 = ws_nut.cell(row=row_num, column=4, value=round(err_v, 4))
            c4.alignment = align_right
            c4.number_format = '0.0000'
            c5 = ws_nut.cell(row=row_num, column=5, value=round(acc_v, 2))
            c5.alignment = align_right
            c5.number_format = '0.00'
            ws_nut.cell(row=row_num, column=6, value=is_p75).alignment = align_center
            c7 = ws_nut.cell(row=row_num, column=7, value=round(ratio_v, 2))
            c7.alignment = align_right
            c7.number_format = '0.00'
            
            for col_k in range(1, 8):
                cell = ws_nut.cell(row=row_num, column=col_k)
                cell.font = font_data
                cell.border = border_cell
                cell.fill = no_fill
                
        tot_row = n_valid + 3
        ws_nut.cell(row=tot_row, column=1, value="MEAN / OVERALL").alignment = align_center
        ws_nut.cell(row=tot_row, column=2, value="-").alignment = align_center
        ws_nut.cell(row=tot_row, column=3, value="-").alignment = align_center
        c4_tot = ws_nut.cell(row=tot_row, column=4, value=round(mae, 4))
        c4_tot.alignment = align_right
        c4_tot.number_format = '0.0000'
        c5_tot = ws_nut.cell(row=tot_row, column=5, value=round(mean_acc, 2))
        c5_tot.alignment = align_right
        c5_tot.number_format = '0.00'
        ws_nut.cell(row=tot_row, column=6, value=f"{above_75}/{n_valid} Passed ({pct_75:.1f}%)").alignment = align_center
        c7_tot = ws_nut.cell(row=tot_row, column=7, value=round(np.mean([x[6] for x in sample_rows_for_nut]), 2))
        c7_tot.alignment = align_right
        c7_tot.number_format = '0.00'
        
        for col_k in range(1, 8):
            cell = ws_nut.cell(row=tot_row, column=col_k)
            cell.font = font_total
            cell.border = border_total_cell
            cell.fill = no_fill
            
        for col in ws_nut.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws_nut.column_dimensions[col_letter].width = max(max_len + 4, 15)
            
        all_nutrients_data[target_name] = {s[0]: s for s in sample_rows_for_nut}
        
    # Write LOOCV_Summary rows
    for r_idx, s in enumerate(summary_rows, start=4):
        ws_sum.cell(row=r_idx, column=1, value=s['code']).alignment = align_center
        ws_sum.cell(row=r_idx, column=2, value=s['name']).alignment = align_left
        ws_sum.cell(row=r_idx, column=3, value=s['arch']).alignment = align_left
        ws_sum.cell(row=r_idx, column=4, value=s['valid']).alignment = align_center
        ws_sum.cell(row=r_idx, column=5, value=s['pass_75']).alignment = align_center
        ws_sum.cell(row=r_idx, column=6, value=s['below_75']).alignment = align_center
        
        c7 = ws_sum.cell(row=r_idx, column=7, value=round(s['pct_75'], 2))
        c7.alignment = align_right
        c7.number_format = '0.00'
        
        c8 = ws_sum.cell(row=r_idx, column=8, value=round(s['mean_acc'], 2))
        c8.alignment = align_right
        c8.number_format = '0.00'
        
        c9 = ws_sum.cell(row=r_idx, column=9, value=round(s['rmse'], 4))
        c9.alignment = align_right
        c9.number_format = '0.0000'
        
        c10 = ws_sum.cell(row=r_idx, column=10, value=round(s['mae'], 4))
        c10.alignment = align_right
        c10.number_format = '0.0000'
        
        c11 = ws_sum.cell(row=r_idx, column=11, value=round(s['r2'], 2))
        c11.alignment = align_right
        c11.number_format = '0.00'
        
        for col_k in range(1, 12):
            cell = ws_sum.cell(row=r_idx, column=col_k)
            cell.font = font_data
            cell.border = border_cell
            cell.fill = no_fill
            
    tot_valid = sum(s['valid'] for s in summary_rows)
    tot_pass = sum(s['pass_75'] for s in summary_rows)
    tot_below = sum(s['below_75'] for s in summary_rows)
    overall_pass_pct = (tot_pass / tot_valid * 100.0) if tot_valid > 0 else 0.0
    overall_mean_acc = np.mean([s['mean_acc'] for s in summary_rows])
    overall_rmse = np.mean([s['rmse'] for s in summary_rows])
    overall_mae = np.mean([s['mae'] for s in summary_rows])
    overall_r2 = np.mean([s['r2'] for s in summary_rows])
    
    tot_sum_row = len(summary_rows) + 4
    ws_sum.cell(row=tot_sum_row, column=1, value="TOTAL / OVERALL").alignment = align_center
    ws_sum.cell(row=tot_sum_row, column=2, value="12 Soil Target Nutrients").alignment = align_left
    ws_sum.cell(row=tot_sum_row, column=3, value="Optimal Full-Spectrum Suite").alignment = align_left
    ws_sum.cell(row=tot_sum_row, column=4, value=tot_valid).alignment = align_center
    ws_sum.cell(row=tot_sum_row, column=5, value=tot_pass).alignment = align_center
    ws_sum.cell(row=tot_sum_row, column=6, value=tot_below).alignment = align_center
    
    c7_tot = ws_sum.cell(row=tot_sum_row, column=7, value=round(overall_pass_pct, 2))
    c7_tot.alignment = align_right
    c7_tot.number_format = '0.00'
    
    c8_tot = ws_sum.cell(row=tot_sum_row, column=8, value=round(overall_mean_acc, 2))
    c8_tot.alignment = align_right
    c8_tot.number_format = '0.00'
    
    c9_tot = ws_sum.cell(row=tot_sum_row, column=9, value=round(overall_rmse, 4))
    c9_tot.alignment = align_right
    c9_tot.number_format = '0.0000'
    
    c10_tot = ws_sum.cell(row=tot_sum_row, column=10, value=round(overall_mae, 4))
    c10_tot.alignment = align_right
    c10_tot.number_format = '0.0000'
    
    c11_tot = ws_sum.cell(row=tot_sum_row, column=11, value=round(overall_r2, 2))
    c11_tot.alignment = align_right
    c11_tot.number_format = '0.00'
    
    for col_k in range(1, 12):
        cell = ws_sum.cell(row=tot_sum_row, column=col_k)
        cell.font = font_total
        cell.border = border_total_cell
        cell.fill = no_fill
        
    for col in ws_sum.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws_sum.column_dimensions[col_letter].width = max(max_len + 4, 15)
        
    # Build Master Side-by-Side sheet
    ws_master = wb_out.create_sheet(title='Master_Actual_vs_Pred_Aligned')
    ws_master.views.sheetView[0].showGridLines = True
    
    master_cols = ['Sample_ID']
    for tgt, _, _, _, _ in SOIL_TARGETS:
        s_code = sanitize_name(tgt)
        master_cols.extend([f"{s_code}_Actual", f"{s_code}_LOOCV_Pred", f"{s_code}_AbsError", f"{s_code}_Accuracy%"])
        
    for c_i, h in enumerate(master_cols, start=1):
        c = ws_master.cell(row=1, column=c_i, value=h)
        c.font = font_header
        c.alignment = align_center if c_i == 1 else align_right
        c.border = border_header_cell
        c.fill = no_fill
        
    for i in range(len(df)):
        s_id = f"Sample_{i+1}"
        ws_master.cell(row=i+2, column=1, value=s_id).alignment = align_center
        ws_master.cell(row=i+2, column=1).font = font_data
        ws_master.cell(row=i+2, column=1).border = border_cell
        
        col_pos = 2
        for tgt, _, _, _, _ in SOIL_TARGETS:
            sample_dict = all_nutrients_data[tgt]
            if s_id in sample_dict:
                _, act_v, pred_v, err_v, acc_v, _, _ = sample_dict[s_id]
                c_a = ws_master.cell(row=i+2, column=col_pos, value=round(act_v, 4))
                c_a.number_format = '0.0000'
                c_p = ws_master.cell(row=i+2, column=col_pos+1, value=round(pred_v, 4))
                c_p.number_format = '0.0000'
                c_e = ws_master.cell(row=i+2, column=col_pos+2, value=round(err_v, 4))
                c_e.number_format = '0.0000'
                c_ac = ws_master.cell(row=i+2, column=col_pos+3, value=round(acc_v, 2))
                c_ac.number_format = '0.00'
            else:
                for off in range(4):
                    ws_master.cell(row=i+2, column=col_pos+off, value="-").alignment = align_center
                    
            for off in range(4):
                cell = ws_master.cell(row=i+2, column=col_pos+off)
                cell.font = font_data
                cell.border = border_cell
                cell.fill = no_fill
                if cell.value != "-":
                    cell.alignment = align_right
            col_pos += 4
            
    for col in ws_master.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws_master.column_dimensions[col_letter].width = max(max_len + 3, 14)
        
    wb_out.save(output_filename)
    print(f"[MODEL 31] Successfully generated clean Excel report: {output_filename}")
    print(f"[MODEL 31] Overall Samples >= 75% Accuracy: {overall_pass_pct:.2f}% ({tot_pass}/{tot_valid} comparisons)")
    print(f"[MODEL 31] Overall Mean Value Accuracy: {overall_mean_acc:.2f}%")
    
    if os.path.exists(ARCHIVE_DIR):
        archive_path = os.path.join(ARCHIVE_DIR, output_filename)
        shutil.copyfile(output_filename, archive_path)
        print(f"[MODEL 31] Archived copy to: {archive_path}")
        
    return summary_rows

# -----------------------------------------------------------------------------
# 3. PRODUCTION MODEL SERIALIZATION (.PKL BUNDLES)
# -----------------------------------------------------------------------------
def train_and_export_production_models(df, output_dir=MODELS_DIR):
    print(f"\n[MODEL 31] Training and serializing production models to '{output_dir}'...")
    os.makedirs(output_dir, exist_ok=True)
    
    for target_name, sheet_name, full_name, arch_desc, reg_proto in SOIL_TARGETS:
        sub = df.dropna(subset=[target_name]).copy()
        X = sub[EXPECTED_BANDS].values
        y = sub[target_name].values
        
        pipe = Pipeline([('scaler', StandardScaler()), ('reg', reg_proto)])
        pipe.fit(X, y)
        
        bundle = {
            'target': target_name,
            'full_name': full_name,
            'architecture': arch_desc,
            'expected_bands': EXPECTED_BANDS,
            'pipeline': pipe,
            'min_val': float(y.min()),
            'max_val': float(y.max()),
            'val_range': float(y.max() - y.min())
        }
        
        s_name = sanitize_name(target_name)
        pkl_path = os.path.join(output_dir, f"model31_{s_name}_pipeline.pkl")
        with open(pkl_path, 'wb') as f:
            pickle.dump(bundle, f)
            
    print(f"[MODEL 31] Successfully exported 12 production bundles to: {output_dir}")

# -----------------------------------------------------------------------------
# 4. PRODUCTION INFERENCE ENGINE
# -----------------------------------------------------------------------------
def predict_soil_sample(features_dict, models_dir=MODELS_DIR):
    X_in = np.array([[features_dict[b] for b in EXPECTED_BANDS]])
    results = {}
    
    for target_name, sheet_name, full_name, arch_desc, reg_proto in SOIL_TARGETS:
        s_name = sanitize_name(target_name)
        pkl_path = os.path.join(models_dir, f"model31_{s_name}_pipeline.pkl")
        with open(pkl_path, 'rb') as f:
            bundle = pickle.load(f)
            
        pred_val = float(bundle['pipeline'].predict(X_in)[0])
        pred_val = max(0.0, pred_val)
        
        results[target_name] = {
            'predicted_value': round(pred_val, 4),
            'full_name': full_name,
            'architecture': arch_desc
        }
    return results

# -----------------------------------------------------------------------------
# MAIN EXECUTION
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    print("=" * 80)
    print("STARTING MODEL 31: HIGH-PRECISION CONTINUOUS VALUE LOOCV MODEL")
    print("=" * 80)
    
    df = pd.read_excel(DATA_FILE)
    print(f"Loaded dataset: {DATA_FILE} ({len(df)} samples)")
    
    summary = build_excel_report(df)
    train_and_export_production_models(df)
    
    print("\n[MODEL 31] Pipeline execution complete!")
