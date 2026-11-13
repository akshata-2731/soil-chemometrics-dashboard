# -*- coding: utf-8 -*-
"""
Master LOOCV Training and Excel Compilation Script for Soil Nutrients
Models Evaluated:
  1. 3D Extra-Trees Regressor (1_3D_ExtraTrees)
  2. 3D Random Forest Regressor (2_3D_RandomForest)
  3. 3D Kernel Ridge Regression (3_3D_KernelRidge)
  4. 2D Spectral Ratio + NDI SVR (4_2D_SpectralRatio)
  5. 3D Gaussian Process Regression / Kriging (5_3D_SpectralKriging)
  6. 3D Support Vector Regression (6_3D_SVR_RBF)

Workbook Structure:
  - Sheet 1: Performance_Summary (Master benchmark across all 6 models & 12 nutrients)
  - Sheets 2-7: Dedicated sheets for each model, structured with:
      * SECTION 1: Dedicated Module Performance Summary table (top)
      * SECTION 2: Sample-by-Sample Actual vs. LOOCV Predicted (Samples 1 to 49)
      * SECTION 3: One-line Model Explanation Banner (bottom)
"""

import os
import warnings
import pandas as pd
import numpy as np
import joblib
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor
from sklearn.kernel_ridge import KernelRidge
from sklearn.svm import SVR
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel as C, WhiteKernel, Matern
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.model_selection import LeaveOneOut, cross_val_predict
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

warnings.filterwarnings('ignore', category=UserWarning)

# Custom Transformer for Model 4: 2D Spectral Ratio & NDI
class SpectralRatioTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, band1_idx=10, band2_idx=0): # nm_680 & nm_410
        self.band1_idx = band1_idx
        self.band2_idx = band2_idx
    def fit(self, X, y=None):
        return self
    def transform(self, X):
        X = np.asarray(X)
        b1, b2 = X[:, self.band1_idx], X[:, self.band2_idx]
        ratio = b1 / (b2 + 1e-6)
        ndi = (b1 - b2) / (b1 + b2 + 1e-6)
        return np.column_stack([ratio, ndi])

# Model descriptions for bottom banners
EXPLANATIONS = {
    '1_3D_ExtraTrees': 'MODEL EXPLANATION: 3D Extra-Trees Regressor projects 21 spectral bands into 2 orthogonal Principal Components (PC1, PC2) capturing 90.7% variance, using 100 randomized decision trees to model nutrient levels with high-precision local terraces under LOOCV.',
    '2_3D_RandomForest': 'MODEL EXPLANATION: 3D Random Forest Regressor fits 100 bootstrapped decision tree surfaces across the (PC1, PC2) spectral plane, averaging predictions to prevent variance blowups and naturally bound nutrient estimations under LOOCV.',
    '3_3D_KernelRidge': 'MODEL EXPLANATION: 3D Kernel Ridge Regression (KRR-RBF) combines L2-regularization with an infinite-dimensional Radial Basis Function kernel to create a smooth, continuous, and curvature-regularized 3D nutrient response surface under LOOCV.',
    '4_2D_SpectralRatio': 'MODEL EXPLANATION: 2D Spectral Ratio Index uses physical absorption ratios (Bivariate Ratio 680nm/410nm and NDI) to represent real chemical absorption contrasts directly mapped via SVR-RBF under LOOCV.',
    '5_3D_SpectralKriging': 'MODEL EXPLANATION: 3D Gaussian Process Regression (Spectral Kriging) uses spatial-spectral covariance kernels (Matern 3/2 + Nugget) on the (PC1, PC2) plane to interpolate continuous nutrient surfaces while providing exact predictive uncertainty intervals (+/- standard deviation) under LOOCV.',
    '6_3D_SVR_RBF': 'MODEL EXPLANATION: 3D Support Vector Regression (SVR-RBF) fits a maximum-margin non-linear surface over the 2D principal component space, filtering sensor noise via an epsilon-insensitive tube under LOOCV.'
}

def run_master_pipeline():
    data_file = 'data.xlsx'
    master_excel = 'All_5_Models_LOOCV_Master_Results.xlsx'
    base_models_dir = 'all_trained_models'
    
    print("=" * 80)
    print("STARTING MASTER LOOCV PIPELINE FOR ALL SOIL MODELS")
    print("=" * 80)
    
    df = pd.read_excel(data_file)
    n_samples = len(df)
    
    spectral_cols = [c for c in df.columns if c.startswith('nm_')]
    target_cols = ['OC%', 'Ca (meq)', 'Mg (meq)', 'N Kg/ha', 'P2O5', 'K2O', 'SO4', 'Fe (ppm)', 'Mn (ppm)', 'Cu (ppm)', 'Zn (ppm)', 'B (ppm)']
    
    # 2D PCA representation for 3D modeling
    scaler_pca = StandardScaler()
    X_scaled = scaler_pca.fit_transform(df[spectral_cols].values)
    pca_2d = PCA(n_components=2)
    coords_pca = pca_2d.fit_transform(X_scaled)
    pc1 = coords_pca[:, 0]
    pc2 = coords_pca[:, 1]
    
    # Spectral ratio features for Model 4
    b_680 = df['nm_680'].values
    b_410 = df['nm_410'].values
    ratio_680_410 = b_680 / (b_410 + 1e-6)
    ndi_680_410 = (b_680 - b_410) / (b_680 + b_410 + 1e-6)
    
    models_config = [
        ('1_3D_ExtraTrees', 'ExtraTrees', os.path.join(base_models_dir, '1_3D_ExtraTrees')),
        ('2_3D_RandomForest', 'RandomForest', os.path.join(base_models_dir, '2_3D_RandomForest')),
        ('3_3D_KernelRidge', 'KernelRidge', os.path.join(base_models_dir, '3_3D_KernelRidge')),
        ('4_2D_SpectralRatio', 'SpectralRatio', os.path.join(base_models_dir, '4_2D_SpectralRatio')),
        ('5_3D_SpectralKriging', 'SpectralKriging', os.path.join(base_models_dir, '5_3D_SpectralKriging')),
        ('6_3D_SVR_RBF', 'SVR_RBF', os.path.join(base_models_dir, '6_3D_SVR_RBF'))
    ]
    
    all_summary_rows = []
    module_data = {}
    
    for sheet_tag, method_type, model_dir in models_config:
        os.makedirs(model_dir, exist_ok=True)
        print(f"\n---> Training and Evaluating [{sheet_tag}] under LOOCV...")
        
        # Coordinate columns for sample tracking
        c_data = {'Sample_ID': [f'Sample_{i+1}' for i in range(n_samples)]}
        if method_type == 'SpectralRatio':
            c_data['Ratio_680_410_X'] = np.round(ratio_680_410, 4)
            c_data['NDI_680_410_Y'] = np.round(ndi_680_410, 4)
        else:
            c_data['PC1_Axis_X'] = np.round(pc1, 4)
            c_data['PC2_Axis_Y'] = np.round(pc2, 4)
            
        mod_summary_rows = []
        
        for target in target_cols:
            valid_mask = ~df[target].isna()
            valid_idx = np.where(valid_mask)[0]
            n_valid = len(valid_idx)
            
            X = df.loc[valid_mask, spectral_cols].values
            y = df.loc[valid_mask, target].values
            val_range = y.max() - y.min()
            
            loo = LeaveOneOut()
            
            # Setup model pipeline
            if method_type == 'ExtraTrees':
                pipe = Pipeline([('scaler', StandardScaler()), ('pca', PCA(n_components=2)), ('reg', ExtraTreesRegressor(n_estimators=100, max_depth=8, random_state=42))])
            elif method_type == 'RandomForest':
                pipe = Pipeline([('scaler', StandardScaler()), ('pca', PCA(n_components=2)), ('reg', RandomForestRegressor(n_estimators=100, max_depth=8, random_state=42))])
            elif method_type == 'KernelRidge':
                pipe = Pipeline([('scaler', StandardScaler()), ('pca', PCA(n_components=2)), ('reg', KernelRidge(alpha=0.5, kernel='rbf', gamma=0.1))])
            elif method_type == 'SpectralRatio':
                pipe = Pipeline([('ratio', SpectralRatioTransformer(10, 0)), ('scaler', StandardScaler()), ('reg', SVR(kernel='rbf', C=30, gamma='scale', epsilon=0.05))])
            elif method_type == 'SpectralKriging':
                k = C(1.0, (1e-2, 1e4)) * Matern(length_scale=[1.0, 1.0], length_scale_bounds=(0.1, 50.0), nu=1.5) + WhiteKernel(noise_level=0.05, noise_level_bounds=(1e-3, 5.0))
                pipe = Pipeline([('scaler', StandardScaler()), ('pca', PCA(n_components=2)), ('gpr', GaussianProcessRegressor(kernel=k, alpha=1e-3, n_restarts_optimizer=1, random_state=42))])
            elif method_type == 'SVR_RBF':
                pipe = Pipeline([('scaler', StandardScaler()), ('pca', PCA(n_components=2)), ('svr', SVR(kernel='rbf', C=30, gamma='scale', epsilon=0.05))])
                
            # LOOCV Out-of-fold predictions
            if method_type == 'SpectralKriging':
                y_loocv_pred = np.zeros(n_valid)
                y_loocv_std = np.zeros(n_valid)
                for tr_idx, te_idx in loo.split(X):
                    pipe.fit(X[tr_idx], y[tr_idx])
                    sc_f = pipe.named_steps['scaler']
                    pca_f = pipe.named_steps['pca']
                    gpr_f = pipe.named_steps['gpr']
                    X_te_2d = pca_f.transform(sc_f.transform(X[te_idx]))
                    pm, ps = gpr_f.predict(X_te_2d, return_std=True)
                    y_loocv_pred[te_idx[0]] = max(0.0, float(pm[0]))
                    y_loocv_std[te_idx[0]] = float(ps[0])
            else:
                y_loocv_pred = np.maximum(0, cross_val_predict(pipe, X, y, cv=loo))
                
            # Train and persist production model
            pipe.fit(X, y)
            clean_name = target.replace('/', '_').replace(' ', '_').replace('%', 'Pct').replace('(', '').replace(')', '')
            model_file = os.path.join(model_dir, f"{clean_name}_{method_type}.joblib")
            joblib.dump(pipe, model_file)
            
            # Metrics
            rmse = np.sqrt(mean_squared_error(y, y_loocv_pred))
            mae = mean_absolute_error(y, y_loocv_pred)
            r2 = r2_score(y, y_loocv_pred)
            range_acc = (1.0 - (rmse / (val_range if val_range > 0 else 1.0))) * 100.0
            
            ratio_accs = [
                (min(a, pr) / max(a, pr)) * 100.0 if max(a, pr) > 0 else (100.0 if a == 0 and pr == 0 else 0.0)
                for a, pr in zip(y, y_loocv_pred)
            ]
            avg_ratio_acc = np.mean(ratio_accs)
            
            row_dict = {
                'Model Method': sheet_tag,
                'Target Nutrient': target,
                'Valid Samples': n_valid,
                'LOOCV Range Accuracy (%)': round(range_acc, 2),
                'LOOCV Ratio Accuracy (%)': round(avg_ratio_acc, 2),
                'LOOCV R^2 Score (%)': round(r2 * 100.0, 2),
                'LOOCV RMSE': round(rmse, 4),
                'LOOCV MAE': round(mae, 4),
                'Model Path': model_file
            }
            all_summary_rows.append(row_dict)
            mod_summary_rows.append(row_dict)
            
            # Populate 49 sample arrays
            act_col = np.full(n_samples, np.nan)
            pred_col = np.full(n_samples, np.nan)
            diff_col = np.full(n_samples, np.nan)
            r_acc_col = np.full(n_samples, np.nan)
            
            act_col[valid_idx] = np.round(y, 4)
            pred_col[valid_idx] = np.round(y_loocv_pred, 4)
            diff_col[valid_idx] = np.round(np.abs(y - y_loocv_pred), 4)
            r_acc_col[valid_idx] = np.round(ratio_accs, 2)
            
            c_data[f'{clean_name}_Actual'] = act_col
            c_data[f'{clean_name}_LOOCV_Pred'] = pred_col
            c_data[f'{clean_name}_AbsError'] = diff_col
            if method_type == 'SpectralKriging':
                std_col = np.full(n_samples, np.nan)
                std_col[valid_idx] = np.round(y_loocv_std, 4)
                c_data[f'{clean_name}_Uncertainty_Std'] = std_col
            c_data[f'{clean_name}_Accuracy%'] = r_acc_col
            
            print(f"  {target:<12}: Range Acc={range_acc:6.2f}% | Ratio Acc={avg_ratio_acc:6.2f}% | RMSE={rmse:8.4f}")
            
        module_data[sheet_tag] = {
            'samples_df': pd.DataFrame(c_data),
            'metrics': mod_summary_rows,
            'avg': {
                'Model Method': sheet_tag,
                'Target Nutrient': 'AVERAGE (All 12 Nutrients)',
                'Valid Samples': 49,
                'LOOCV Range Accuracy (%)': round(np.mean([m['LOOCV Range Accuracy (%)'] for m in mod_summary_rows]), 2),
                'LOOCV Ratio Accuracy (%)': round(np.mean([m['LOOCV Ratio Accuracy (%)'] for m in mod_summary_rows]), 2),
                'LOOCV R^2 Score (%)': round(np.mean([m['LOOCV R^2 Score (%)'] for m in mod_summary_rows]), 2),
                'LOOCV RMSE': round(np.mean([m['LOOCV RMSE'] for m in mod_summary_rows]), 4),
                'LOOCV MAE': round(np.mean([m['LOOCV MAE'] for m in mod_summary_rows]), 4),
                'Model Path': '-'
            }
        }
        
    # Build Master Styled Excel Workbook
    print(f"\nConstructing master styled workbook: '{master_excel}'...")
    wb = openpyxl.Workbook()
    wb.remove(wb.active) # Remove default sheet
    
    # Styling definitions
    title_fill = PatternFill(start_color="002060", end_color="002060", fill_type="solid") # dark navy
    title_font = Font(name="Calibri", size=13, bold=True, color="FFFFFF")

    section_fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid") # navy
    section_font = Font(name="Calibri", size=12, bold=True, color="FFFFFF")

    header_fill = PatternFill(start_color="2F5597", end_color="2F5597", fill_type="solid") # medium navy
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")

    sub_header_fill = PatternFill(start_color="305496", end_color="305496", fill_type="solid")
    sub_header_font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")

    coord_fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
    act_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")  # light green
    pred_fill = PatternFill(start_color="DDEBF7", end_color="DDEBF7", fill_type="solid") # light blue
    err_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")  # light yellow
    summary_row_fill = PatternFill(start_color="F9FBFD", end_color="F9FBFD", fill_type="solid")
    avg_row_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid") # soft blue accent
    avg_font = Font(name="Calibri", size=11, bold=True, color="000000")

    note_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
    note_font = Font(name="Calibri", size=11, bold=True, color="7F6000", italic=True)

    border_thin = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9')
    )
    border_box = Border(
        left=Side(style='medium', color='D6B656'),
        right=Side(style='medium', color='D6B656'),
        top=Side(style='medium', color='D6B656'),
        bottom=Side(style='medium', color='D6B656')
    )
    
    # -------------------------------------------------------------
    # 1. SHEET 1: Master Performance_Summary Sheet
    # -------------------------------------------------------------
    ws_master = wb.create_sheet(title='Performance_Summary')
    ws_master.views.sheetView[0].showGridLines = True
    
    ws_master.merge_cells(start_row=1, start_column=1, end_row=1, end_column=9)
    c_t = ws_master.cell(row=1, column=1)
    c_t.value = "OVERALL PERFORMANCE SUMMARY (ALL MODELS & NUTRIENTS - LOOCV VALIDATED)"
    c_t.font = title_font
    c_t.fill = title_fill
    c_t.alignment = Alignment(horizontal="center", vertical="center")
    ws_master.row_dimensions[1].height = 32
    
    master_headers = ['Model Method', 'Target Nutrient', 'Valid Samples', 'LOOCV Range Accuracy (%)', 'LOOCV Ratio Accuracy (%)', 'LOOCV R^2 Score (%)', 'LOOCV RMSE', 'LOOCV MAE', 'Model Path']
    for c_idx, h in enumerate(master_headers, 1):
        c = ws_master.cell(row=2, column=c_idx)
        c.value = h
        c.font = header_font
        c.fill = header_fill
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws_master.row_dimensions[2].height = 28
    
    cur_r = 3
    for r_data in all_summary_rows:
        for c_idx, h in enumerate(master_headers, 1):
            c = ws_master.cell(row=cur_r, column=c_idx)
            val = r_data[h]
            c.value = val
            c.border = border_thin
            if isinstance(val, (int, float)):
                c.alignment = Alignment(horizontal="right", vertical="center")
            else:
                c.alignment = Alignment(horizontal="center", vertical="center")
        cur_r += 1
        
    cur_r += 1
    ws_master.merge_cells(start_row=cur_r, start_column=1, end_row=cur_r, end_column=9)
    n_c = ws_master.cell(row=cur_r, column=1)
    n_c.value = "PERFORMANCE EXPLANATION: This master table benchmarks out-of-fold Leave-One-Out Cross-Validation (LOOCV) accuracy across all modeling architectures, where each sample was held out and predicted blindly by a model trained strictly on the other 48 samples."
    n_c.font = note_font
    n_c.fill = note_fill
    n_c.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    ws_master.row_dimensions[cur_r].height = 32
    for c in range(1, 10):
        ws_master.cell(row=cur_r, column=c).border = border_box
        ws_master.cell(row=cur_r, column=c).fill = note_fill
        
    for c in range(1, 10):
        max_len = max(len(str(ws_master.cell(row=r, column=c).value or '')) for r in range(2, min(ws_master.max_row, 80)))
        ws_master.column_dimensions[get_column_letter(c)].width = max(max_len + 4, 15)
        
    # -------------------------------------------------------------
    # 2. SHEETS 2-7: Individual Modules with Dedicated Summaries at Top
    # -------------------------------------------------------------
    summary_headers = ['Target Nutrient', 'Valid Samples', 'LOOCV Range Accuracy (%)', 'LOOCV Ratio Accuracy (%)', 'LOOCV R^2 Score (%)', 'LOOCV RMSE', 'LOOCV MAE']
    
    for sheet_tag, _, _ in models_config:
        ws = wb.create_sheet(title=sheet_tag)
        ws.views.sheetView[0].showGridLines = True
        
        mod_info = module_data[sheet_tag]
        mod_df = mod_info['samples_df']
        mod_metrics = mod_info['metrics']
        mod_avg = mod_info['avg']
        num_cols = len(mod_df.columns)
        
        # SECTION 1: DEDICATED MODULE PERFORMANCE SUMMARY (AT TOP)
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=7)
        sec1 = ws.cell(row=1, column=1)
        sec1.value = f"SECTION 1: {sheet_tag} - PERFORMANCE SUMMARY (LOOCV VALIDATED)"
        sec1.font = title_font
        sec1.fill = title_fill
        sec1.alignment = Alignment(horizontal="left", vertical="center")
        ws.row_dimensions[1].height = 30
        
        for c_idx, h in enumerate(summary_headers, 1):
            c = ws.cell(row=2, column=c_idx)
            c.value = h
            c.font = header_font
            c.fill = header_fill
            c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.row_dimensions[2].height = 26
        
        r_idx = 3
        for m in mod_metrics:
            for c_idx, h in enumerate(summary_headers, 1):
                c = ws.cell(row=r_idx, column=c_idx)
                val = m[h]
                c.value = val
                c.border = border_thin
                c.fill = summary_row_fill
                if isinstance(val, (int, float)):
                    c.alignment = Alignment(horizontal="right", vertical="center")
                else:
                    c.alignment = Alignment(horizontal="center", vertical="center")
            r_idx += 1
            
        # Module Average Row
        for c_idx, h in enumerate(summary_headers, 1):
            c = ws.cell(row=r_idx, column=c_idx)
            val = mod_avg[h]
            c.value = val
            c.font = avg_font
            c.fill = avg_row_fill
            c.border = border_thin
            if isinstance(val, (int, float)):
                c.alignment = Alignment(horizontal="right", vertical="center")
            else:
                c.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[r_idx].height = 24
        r_idx += 1
        
        # Blank separator row
        r_idx += 1
        
        # SECTION 2: SAMPLE-BY-SAMPLE ACTUAL VS PREDICTED (SAMPLES 1 TO 49)
        ws.merge_cells(start_row=r_idx, start_column=1, end_row=r_idx, end_column=min(num_cols, 8))
        sec2 = ws.cell(row=r_idx, column=1)
        sec2.value = f"SECTION 2: {sheet_tag} - SAMPLE-BY-SAMPLE ACTUAL VS LOOCV PREDICTED (SAMPLES 1 TO 49)"
        sec2.font = section_font
        sec2.fill = section_fill
        sec2.alignment = Alignment(horizontal="left", vertical="center")
        ws.row_dimensions[r_idx].height = 28
        r_idx += 1
        
        # Sub-headers for Sample Data
        for col_idx, col_name in enumerate(mod_df.columns, 1):
            cell = ws.cell(row=r_idx, column=col_idx)
            cell.value = col_name
            cell.font = sub_header_font
            cell.fill = sub_header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.row_dimensions[r_idx].height = 28
        r_idx += 1
        
        # Sample rows (1 to 49)
        for row_num in range(len(mod_df)):
            for col_idx, col_name in enumerate(mod_df.columns, 1):
                val = mod_df.loc[row_num, col_name]
                c = ws.cell(row=r_idx, column=col_idx)
                c.value = val if pd.notna(val) else ""
                c.border = border_thin
                
                if 'Axis' in col_name or 'PC' in col_name or 'Ratio' in col_name or 'NDI' in col_name:
                    c.fill = coord_fill
                elif 'Actual' in col_name:
                    c.fill = act_fill
                elif 'Pred' in col_name:
                    c.fill = pred_fill
                elif 'Error' in col_name or 'Accuracy' in col_name:
                    c.fill = err_fill
                    
                if isinstance(val, (int, float)):
                    c.alignment = Alignment(horizontal="right", vertical="center")
                else:
                    c.alignment = Alignment(horizontal="center", vertical="center")
            r_idx += 1
            
        # SECTION 3: ONE-LINE EXPLANATION BANNER (AT BOTTOM)
        r_idx += 1
        ws.merge_cells(start_row=r_idx, start_column=1, end_row=r_idx, end_column=min(num_cols, 8))
        note_cell = ws.cell(row=r_idx, column=1)
        note_cell.value = EXPLANATIONS.get(sheet_tag, "MODEL EXPLANATION: LOOCV evaluated model.")
        note_cell.font = note_font
        note_cell.fill = note_fill
        note_cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        ws.row_dimensions[r_idx].height = 32
        for c in range(1, min(num_cols, 8) + 1):
            ws.cell(row=r_idx, column=c).border = border_box
            ws.cell(row=r_idx, column=c).fill = note_fill
            
        # Column dimensions
        for c in range(1, num_cols + 1):
            max_len = max(len(str(ws.cell(row=r, column=c).value or '')) for r in range(2, min(ws.max_row, 75)))
            ws.column_dimensions[get_column_letter(c)].width = max(max_len + 4, 14)
            
    try:
        wb.save(master_excel)
        print(f"\nMaster Excel workbook successfully created: '{master_excel}'!")
    except PermissionError:
        fallback_excel = 'All_5_Models_LOOCV_Master_Results_Updated.xlsx'
        wb.save(fallback_excel)
        print(f"\nNotice: '{master_excel}' is currently open in Excel and write-locked.")
        print(f"Successfully saved updated master workbook to: '{fallback_excel}'!")

if __name__ == '__main__':
    run_master_pipeline()
