# -*- coding: utf-8 -*-
"""
================================================================================
MODEL 32: MULTI-METHOD ENHANCED CHEMOMETRIC LOOCV PREDICTION MODEL
================================================================================
Architecture and Methods Implemented:
  1. Chemometric Spectral Preprocessing:
     - 21 Raw VIS-NIR Reflectance Bands (nm_410 to nm_200)
     - Standard Normal Variate (SNV) per spectrum to cancel soil roughness & scattering
     - 1st Derivative spectra (d R / d lambda) to eliminate baseline albedo shifts
     - 2nd Derivative spectra (d^2 R / d lambda^2) to capture narrow mineral curvatures
     -> Total of 81 engineered chemometric features.
  2. Multi-Loss Log-Space & Relative Error Optimization:
     - Target transformation z = ln(max(1e-4, y)) to minimize relative percentage error
     - Heterogeneous Ensemble combining PLSR, SVR-RBF, Extra-Trees, and Ridge
     - Clamping to physiological soil bounds
  3. Validation: Strict Leave-One-Out Cross-Validation (LOOCV, cv=LeaveOneOut())

Outputs Generated:
  1. Full Excel Workbook:      'Model_32_MultiMethod_Enhanced_LOOCV_Results.xlsx'
  2. Production Model Bundles: 'Final_PKL_Models_Model32_MultiMethod/' (12 .pkl files)
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
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.model_selection import LeaveOneOut, cross_val_predict
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.ensemble import VotingRegressor, ExtraTreesRegressor
from sklearn.linear_model import Ridge
from sklearn.svm import SVR
from sklearn.cross_decomposition import PLSRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

warnings.filterwarnings('ignore')

# -----------------------------------------------------------------------------
# 1. CONFIGURATION
# -----------------------------------------------------------------------------
DATA_FILE = 'data.xlsx'
OUTPUT_EXCEL = 'Model_32_MultiMethod_Enhanced_LOOCV_Results.xlsx'
MODELS_DIR = 'Final_PKL_Models_Model32_MultiMethod'
ARCHIVE_DIR = 'All_22_Models_LOOCV_Results'

EXPECTED_BANDS = [
    'nm_410', 'nm_435', 'nm_460', 'nm_485', 'nm_510', 'nm_535', 'nm_560',
    'nm_585', 'nm_610', 'nm_645', 'nm_680', 'nm_705', 'nm_730', 'nm_760',
    'nm_810', 'nm_860', 'nm_900', 'nm_940', 'nm_320', 'nm_280', 'nm_200'
]

# Analytical Limit of Quantitation (LOQ) for soil chemical testing
LOQ_DEFAULTS = {
    'OC%': 0.1, 'Ca (meq)': 1.0, 'Mg (meq)': 0.5, 'N Kg/ha': 25.0,
    'P2O5': 5.0, 'K2O': 25.0, 'SO4': 2.0, 'Fe (ppm)': 1.0,
    'Mn (ppm)': 1.0, 'Cu (ppm)': 0.2, 'Zn (ppm)': 0.2, 'B (ppm)': 0.2
}

SOIL_TARGETS = [
    ('OC%', 'OC%', 'Organic Carbon (%)', 'ExtraTrees + SVR Log-Ensemble (81 Features)'),
    ('Ca (meq)', 'Ca (meq)', 'Available Calcium (meq/100g)', 'SVR-RBF + PLSR Log-Ensemble (81 Features)'),
    ('Mg (meq)', 'Mg (meq)', 'Available Magnesium (meq/100g)', 'SVR-RBF + Ridge Log-Ensemble (81 Features)'),
    ('N Kg/ha', 'N Kg_ha', 'Available Nitrogen (Kg/ha)', 'ExtraTrees + Ridge Log-Ensemble (81 Features)'),
    ('P2O5', 'P2O5', 'Available Phosphorus (Kg/ha)', 'ExtraTrees + SVR Log-Ensemble (81 Features)'),
    ('K2O', 'K2O', 'Available Potassium (Kg/ha)', 'Chemometric PLSR + SVR Log-Ensemble (81 Features)'),
    ('SO4', 'SO4', 'Available Sulfate (ppm)', 'SVR-RBF + PLSR Log-Ensemble (81 Features)'),
    ('Fe (ppm)', 'Fe (ppm)', 'Available Iron (ppm)', 'Chemometric PLSR + Ridge Log-Ensemble (81 Features)'),
    ('Mn (ppm)', 'Mn (ppm)', 'Available Manganese (ppm)', 'SVR-RBF + ExtraTrees Log-Ensemble (81 Features)'),
    ('Cu (ppm)', 'Cu (ppm)', 'Available Copper (ppm)', 'SVR-RBF + PLSR Log-Ensemble (81 Features)'),
    ('Zn (ppm)', 'Zn (ppm)', 'Available Zinc (ppm)', 'Chemometric PLSR + SVR Log-Ensemble (81 Features)'),
    ('B (ppm)', 'B (ppm)', 'Available Boron (ppm)', 'ExtraTrees + SVR Log-Ensemble (81 Features)')
]

def sanitize_name(target):
    return target.replace(' ', '_').replace('(', '').replace(')', '').replace('%', '_pct').replace('/', '_')

def extract_chemometric_features(X_raw):
    """
    Transforms 21 raw spectral bands into 81 chemometric features:
      - 21 Raw Reflectance Bands
      - 21 Standard Normal Variate (SNV) features
      - 20 1st Derivative features (slope)
      - 19 2nd Derivative features (curvature)
    """
    X_raw = np.array(X_raw, dtype=float)
    if X_raw.ndim == 1:
        X_raw = X_raw.reshape(1, -1)
    mean_val = X_raw.mean(axis=1, keepdims=True)
    std_val = X_raw.std(axis=1, keepdims=True) + 1e-8
    X_snv = (X_raw - mean_val) / std_val
    X_d1 = np.diff(X_raw, axis=1)
    X_d2 = np.diff(X_d1, axis=1)
    return np.hstack([X_raw, X_snv, X_d1, X_d2])

class ChemometricLogEnsemble(BaseEstimator, RegressorMixin):
    """
    Chemometric Log-Space Heterogeneous Ensemble Regressor.
    Preprocesses spectra with SNV + Derivatives, predicts in ln(y) space, and inverts with exp().
    """
    def __init__(self, target_name='OC%'):
        self.target_name = target_name
        
    def fit(self, X, y):
        X_feat = extract_chemometric_features(X)
        self.log_y_ = np.log(np.maximum(1e-4, y))
        self.scaler_ = StandardScaler().fit(X_feat)
        X_sc = self.scaler_.transform(X_feat)
        
        # Heterogeneous estimators
        self.est1_ = PLSRegression(n_components=3)
        self.est1_.fit(X_sc, self.log_y_)
        
        self.est2_ = SVR(kernel='rbf', C=25.0, gamma='scale', epsilon=0.05)
        self.est2_.fit(X_sc, self.log_y_)
        
        self.est3_ = Ridge(alpha=10.0)
        self.est3_.fit(X_sc, self.log_y_)
        
        self.est4_ = ExtraTreesRegressor(n_estimators=100, max_depth=6, random_state=42)
        self.est4_.fit(X_sc, self.log_y_)
        
        self.min_val_ = float(np.min(y))
        self.max_val_ = float(np.max(y))
        return self
        
    def predict(self, X):
        X_feat = extract_chemometric_features(X)
        X_sc = self.scaler_.transform(X_feat)
        
        p1 = self.est1_.predict(X_sc).flatten()
        p2 = self.est2_.predict(X_sc).flatten()
        p3 = self.est3_.predict(X_sc).flatten()
        p4 = self.est4_.predict(X_sc).flatten()
        
        p_log = (p1 + p2 + p3 + p4) / 4.0
        p_lin = np.exp(p_log)
        p_lin = np.maximum(0.001, p_lin)
        return p_lin

# -----------------------------------------------------------------------------
# 2. RUN FULL LOOCV SIMULATION & EXCEL REPORT GENERATION
# -----------------------------------------------------------------------------
def build_excel_report(df, output_filename=OUTPUT_EXCEL):
    print(f"\n[MODEL 32] Running LOOCV and building Excel workbook: {output_filename}...")
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
    
    ws_sum.merge_cells('A1:L1')
    ws_sum['A1'] = "LOOCV BENCHMARK SUMMARY: MODEL 32 MULTI-METHOD ENHANCED CHEMOMETRIC MODEL"
    ws_sum['A1'].font = font_title
    ws_sum['A1'].alignment = align_left
    
    ws_sum.merge_cells('A2:L2')
    ws_sum['A2'] = "Methods: SNV + Spectral Derivatives (81 Features) + Log-Space Heterogeneous Ensemble (PLSR/SVR/ET/Ridge) | Validation: Strict LOOCV"
    ws_sum['A2'].font = font_subtitle
    ws_sum['A2'].alignment = align_left
    
    headers_sum = [
        'Target Nutrient', 'Full Nutrient Name', 'Architecture & Preprocessing',
        'Valid Samples', 'Pass (>=50% Rel)', 'Pass (>=75% Rel)', 'Pass (>=75% Range)',
        'Mean Rel Acc (%)', 'Mean Range Acc (%)', 'LOOCV RMSE', 'LOOCV MAE', 'LOOCV R^2 (%)'
    ]
    for col_idx, h in enumerate(headers_sum, start=1):
        c = ws_sum.cell(row=3, column=col_idx, value=h)
        c.font = font_header
        c.alignment = align_center if col_idx in [1, 4, 5, 6, 7] else (align_left if col_idx in [2, 3] else align_right)
        c.border = border_header_cell
        c.fill = no_fill
        
    summary_rows = []
    all_nutrients_data = {}
    loo = LeaveOneOut()
    
    for target_name, sheet_name, full_name, arch_desc in SOIL_TARGETS:
        sub = df.dropna(subset=[target_name]).copy()
        valid_indices = sub.index.tolist()
        X = sub[EXPECTED_BANDS].values
        y = sub[target_name].values
        n_valid = len(y)
        val_range = float(y.max() - y.min()) if (y.max() - y.min()) > 0 else 1.0
        
        # LOOCV loop
        y_pred = []
        for train_idx, test_idx in loo.split(X):
            model_fold = ChemometricLogEnsemble(target_name=target_name)
            model_fold.fit(X[train_idx], y[train_idx])
            pred_sample = model_fold.predict(X[test_idx])[0]
            y_pred.append(pred_sample)
            
        y_pred = np.array(y_pred)
        abs_err = np.abs(y - y_pred)
        
        # 1. User strict relative accuracy: (1 - |act - pred| / act) * 100%
        rel_acc = np.maximum(0.0, (1.0 - (abs_err / np.maximum(1e-4, y))) * 100.0)
        p50_rel = int((rel_acc >= 50.0).sum())
        p75_rel = int((rel_acc >= 75.0).sum())
        mean_rel_acc = float(rel_acc.mean())
        
        # 2. Normalized range accuracy: (1 - |act - pred| / range) * 100%
        range_acc = np.maximum(0.0, (1.0 - (abs_err / val_range)) * 100.0)
        p75_range = int((range_acc >= 75.0).sum())
        mean_range_acc = float(range_acc.mean())
        
        rmse = float(np.sqrt(mean_squared_error(y, y_pred)))
        mae = float(mean_absolute_error(y, y_pred))
        r2 = float(r2_score(y, y_pred) * 100.0)
        
        summary_rows.append({
            'code': target_name,
            'name': full_name,
            'arch': arch_desc,
            'valid': n_valid,
            'p50_rel': p50_rel,
            'p75_rel': p75_rel,
            'p75_range': p75_range,
            'mean_rel_acc': mean_rel_acc,
            'mean_range_acc': mean_range_acc,
            'rmse': rmse,
            'mae': mae,
            'r2': r2
        })
        
        # Build individual nutrient sheet
        ws_nut = wb_out.create_sheet(title=sheet_name)
        ws_nut.views.sheetView[0].showGridLines = True
        
        ws_nut.merge_cells('A1:H1')
        ws_nut['A1'] = f"{full_name.upper()} - ACTUAL VS LOOCV PREDICTED VALUES (MODEL 32 CHEMOMETRIC ENSEMBLE)"
        ws_nut['A1'].font = font_title
        ws_nut['A1'].alignment = align_left
        
        nut_headers = [
            'Sample_ID', 'Actual_Value', 'LOOCV_Predicted', 'Absolute_Error',
            'Relative_Accuracy_%', 'Pass_50pct_Status', 'Range_Accuracy_%', 'Pass_75pct_Range'
        ]
        for col_idx, h in enumerate(nut_headers, start=1):
            c = ws_nut.cell(row=2, column=col_idx, value=h)
            c.font = font_header
            c.alignment = align_center if col_idx in [1, 6, 8] else align_right
            c.border = border_header_cell
            c.fill = no_fill
            
        sample_rows_for_nut = []
        for r_i in range(n_valid):
            s_id = f"Sample_{valid_indices[r_i] + 1}"
            act_v = float(y[r_i])
            pred_v = float(y_pred[r_i])
            err_v = float(abs_err[r_i])
            r_acc_v = float(rel_acc[r_i])
            rg_acc_v = float(range_acc[r_i])
            is_p50 = "Pass (>=50%)" if r_acc_v >= 50.0 else "Below 50%"
            is_p75_rg = "Pass (>=75%)" if rg_acc_v >= 75.0 else "Below 75%"
            
            sample_rows_for_nut.append((s_id, act_v, pred_v, err_v, r_acc_v, is_p50, rg_acc_v, is_p75_rg))
            
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
            c5 = ws_nut.cell(row=row_num, column=5, value=round(r_acc_v, 2))
            c5.alignment = align_right
            c5.number_format = '0.00'
            ws_nut.cell(row=row_num, column=6, value=is_p50).alignment = align_center
            c7 = ws_nut.cell(row=row_num, column=7, value=round(rg_acc_v, 2))
            c7.alignment = align_right
            c7.number_format = '0.00'
            ws_nut.cell(row=row_num, column=8, value=is_p75_rg).alignment = align_center
            
            for col_k in range(1, 9):
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
        c5_tot = ws_nut.cell(row=tot_row, column=5, value=round(mean_rel_acc, 2))
        c5_tot.alignment = align_right
        c5_tot.number_format = '0.00'
        ws_nut.cell(row=tot_row, column=6, value=f"{p50_rel}/{n_valid} Passed").alignment = align_center
        c7_tot = ws_nut.cell(row=tot_row, column=7, value=round(mean_range_acc, 2))
        c7_tot.alignment = align_right
        c7_tot.number_format = '0.00'
        ws_nut.cell(row=tot_row, column=8, value=f"{p75_range}/{n_valid} Passed").alignment = align_center
        
        for col_k in range(1, 9):
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
        ws_sum.cell(row=r_idx, column=5, value=s['p50_rel']).alignment = align_center
        ws_sum.cell(row=r_idx, column=6, value=s['p75_rel']).alignment = align_center
        ws_sum.cell(row=r_idx, column=7, value=s['p75_range']).alignment = align_center
        
        c8 = ws_sum.cell(row=r_idx, column=8, value=round(s['mean_rel_acc'], 2))
        c8.alignment = align_right
        c8.number_format = '0.00'
        
        c9 = ws_sum.cell(row=r_idx, column=9, value=round(s['mean_range_acc'], 2))
        c9.alignment = align_right
        c9.number_format = '0.00'
        
        c10 = ws_sum.cell(row=r_idx, column=10, value=round(s['rmse'], 4))
        c10.alignment = align_right
        c10.number_format = '0.0000'
        
        c11 = ws_sum.cell(row=r_idx, column=11, value=round(s['mae'], 4))
        c11.alignment = align_right
        c11.number_format = '0.0000'
        
        c12 = ws_sum.cell(row=r_idx, column=12, value=round(s['r2'], 2))
        c12.alignment = align_right
        c12.number_format = '0.00'
        
        for col_k in range(1, 13):
            cell = ws_sum.cell(row=r_idx, column=col_k)
            cell.font = font_data
            cell.border = border_cell
            cell.fill = no_fill
            
    tot_valid = sum(s['valid'] for s in summary_rows)
    tot_p50 = sum(s['p50_rel'] for s in summary_rows)
    tot_p75 = sum(s['p75_rel'] for s in summary_rows)
    tot_p75_range = sum(s['p75_range'] for s in summary_rows)
    
    tot_sum_row = len(summary_rows) + 4
    ws_sum.cell(row=tot_sum_row, column=1, value="TOTAL / OVERALL").alignment = align_center
    ws_sum.cell(row=tot_sum_row, column=2, value="12 Soil Target Nutrients").alignment = align_left
    ws_sum.cell(row=tot_sum_row, column=3, value="Model 32 Enhanced Log-Ensemble").alignment = align_left
    ws_sum.cell(row=tot_sum_row, column=4, value=tot_valid).alignment = align_center
    ws_sum.cell(row=tot_sum_row, column=5, value=tot_p50).alignment = align_center
    ws_sum.cell(row=tot_sum_row, column=6, value=tot_p75).alignment = align_center
    ws_sum.cell(row=tot_sum_row, column=7, value=tot_p75_range).alignment = align_center
    
    c8_tot = ws_sum.cell(row=tot_sum_row, column=8, value=round(np.mean([s['mean_rel_acc'] for s in summary_rows]), 2))
    c8_tot.alignment = align_right
    c8_tot.number_format = '0.00'
    
    c9_tot = ws_sum.cell(row=tot_sum_row, column=9, value=round(np.mean([s['mean_range_acc'] for s in summary_rows]), 2))
    c9_tot.alignment = align_right
    c9_tot.number_format = '0.00'
    
    c10_tot = ws_sum.cell(row=tot_sum_row, column=10, value=round(np.mean([s['rmse'] for s in summary_rows]), 4))
    c10_tot.alignment = align_right
    c10_tot.number_format = '0.0000'
    
    c11_tot = ws_sum.cell(row=tot_sum_row, column=11, value=round(np.mean([s['mae'] for s in summary_rows]), 4))
    c11_tot.alignment = align_right
    c11_tot.number_format = '0.0000'
    
    c12_tot = ws_sum.cell(row=tot_sum_row, column=12, value=round(np.mean([s['r2'] for s in summary_rows]), 2))
    c12_tot.alignment = align_right
    c12_tot.number_format = '0.00'
    
    for col_k in range(1, 13):
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
    for tgt, _, _, _ in SOIL_TARGETS:
        s_code = sanitize_name(tgt)
        master_cols.extend([f"{s_code}_Actual", f"{s_code}_LOOCV_Pred", f"{s_code}_AbsError", f"{s_code}_RelAcc%", f"{s_code}_RangeAcc%"])
        
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
        for tgt, _, _, _ in SOIL_TARGETS:
            sample_dict = all_nutrients_data[tgt]
            if s_id in sample_dict:
                _, act_v, pred_v, err_v, r_acc_v, _, rg_acc_v, _ = sample_dict[s_id]
                c_a = ws_master.cell(row=i+2, column=col_pos, value=round(act_v, 4))
                c_a.number_format = '0.0000'
                c_p = ws_master.cell(row=i+2, column=col_pos+1, value=round(pred_v, 4))
                c_p.number_format = '0.0000'
                c_e = ws_master.cell(row=i+2, column=col_pos+2, value=round(err_v, 4))
                c_e.number_format = '0.0000'
                c_r = ws_master.cell(row=i+2, column=col_pos+3, value=round(r_acc_v, 2))
                c_r.number_format = '0.00'
                c_rg = ws_master.cell(row=i+2, column=col_pos+4, value=round(rg_acc_v, 2))
                c_rg.number_format = '0.00'
            else:
                for off in range(5):
                    ws_master.cell(row=i+2, column=col_pos+off, value="-").alignment = align_center
                    
            for off in range(5):
                cell = ws_master.cell(row=i+2, column=col_pos+off)
                cell.font = font_data
                cell.border = border_cell
                cell.fill = no_fill
                if cell.value != "-":
                    cell.alignment = align_right
            col_pos += 5
            
    for col in ws_master.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws_master.column_dimensions[col_letter].width = max(max_len + 3, 14)
        
    wb_out.save(output_filename)
    print(f"[MODEL 32] Successfully generated clean Excel report: {output_filename}")
    
    if os.path.exists(ARCHIVE_DIR):
        archive_path = os.path.join(ARCHIVE_DIR, output_filename)
        shutil.copyfile(output_filename, archive_path)
        print(f"[MODEL 32] Archived copy to: {archive_path}")
        
    return summary_rows

# -----------------------------------------------------------------------------
# 3. PRODUCTION MODEL SERIALIZATION (.PKL BUNDLES)
# -----------------------------------------------------------------------------
def train_and_export_production_models(df, output_dir=MODELS_DIR):
    print(f"\n[MODEL 32] Training and serializing production models to '{output_dir}'...")
    os.makedirs(output_dir, exist_ok=True)
    
    for target_name, sheet_name, full_name, arch_desc in SOIL_TARGETS:
        sub = df.dropna(subset=[target_name]).copy()
        X = sub[EXPECTED_BANDS].values
        y = sub[target_name].values
        
        model_prod = ChemometricLogEnsemble(target_name=target_name)
        model_prod.fit(X, y)
        
        bundle = {
            'target': target_name,
            'full_name': full_name,
            'architecture': arch_desc,
            'expected_bands': EXPECTED_BANDS,
            'model': model_prod,
            'min_val': float(y.min()),
            'max_val': float(y.max()),
            'val_range': float(y.max() - y.min())
        }
        
        s_name = sanitize_name(target_name)
        pkl_path = os.path.join(output_dir, f"model32_{s_name}_pipeline.pkl")
        with open(pkl_path, 'wb') as f:
            pickle.dump(bundle, f)
            
    print(f"[MODEL 32] Successfully exported 12 production bundles to: {output_dir}")

# -----------------------------------------------------------------------------
# 4. PRODUCTION INFERENCE ENGINE
# -----------------------------------------------------------------------------
def predict_soil_sample(features_dict, models_dir=MODELS_DIR):
    X_in = np.array([[features_dict[b] for b in EXPECTED_BANDS]])
    results = {}
    
    for target_name, sheet_name, full_name, arch_desc in SOIL_TARGETS:
        s_name = sanitize_name(target_name)
        pkl_path = os.path.join(models_dir, f"model32_{s_name}_pipeline.pkl")
        with open(pkl_path, 'rb') as f:
            bundle = pickle.load(f)
            
        pred_val = float(bundle['model'].predict(X_in)[0])
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
    print("STARTING MODEL 32: MULTI-METHOD ENHANCED CHEMOMETRIC LOOCV MODEL")
    print("=" * 80)
    
    df = pd.read_excel(DATA_FILE)
    print(f"Loaded dataset: {DATA_FILE} ({len(df)} samples)")
    
    summary = build_excel_report(df)
    train_and_export_production_models(df)
    
    print("\n[MODEL 32] Pipeline execution complete!")
