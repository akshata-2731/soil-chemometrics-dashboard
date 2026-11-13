"""
3D Gaussian Process Regression (3D Spectral Kriging) on Soil Spectroscopy Data
==============================================================================
Architecture:
  Raw 21-band Spectrum -> StandardScaler -> PCA (2 Principal Components: PC1, PC2)
  -> 3D Gaussian Process Regressor (Matern / RBF Covariance + Nugget) -> Soil Nutrient (Z)
     + Predictive Standard Deviation (Uncertainty Estimation)

This script:
1. Projects 21 spectral wavelengths into 2 principal axes (PC1, PC2) capturing 90.7% variance.
2. Performs Leave-One-Out Cross-Validation (LOOCV) to validate unseen generalizability.
3. Fits and saves all 12 complete 3D Kriging production pipelines (.joblib) into 'models_3d_kriging/'.
4. Generates a styled Excel report: 'Actual_vs_Pred_3D_Kriging_LOOCV_Results.xlsx' including uncertainty intervals.
5. Provides a ready-to-use prediction function returning both predicted nutrient values and standard deviations.
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
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C, WhiteKernel, Matern
from sklearn.model_selection import LeaveOneOut
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

# Suppress minor optimizer convergence warnings
warnings.filterwarnings('ignore', category=UserWarning)

def train_and_evaluate_3d_kriging(data_file='data.xlsx', models_dir='models_3d_kriging', output_excel='Actual_vs_Pred_3D_Kriging_LOOCV_Results.xlsx'):
    # 1. Ensure models directory exists
    os.makedirs(models_dir, exist_ok=True)
    print(f"[1/5] Ensuring 3D Kriging models directory '{models_dir}/' exists...")
    
    # 2. Load dataset
    print(f"[2/5] Reading dataset from '{data_file}'...")
    if not os.path.exists(data_file):
        raise FileNotFoundError(f"File '{data_file}' not found.")
        
    df = pd.read_excel(data_file)
    spec_cols = [c for c in df.columns if c.startswith('nm_')]
    soil_cols = [c for c in df.columns if not c.startswith('nm_')]
    n_samples = len(df)
    
    # Global PCA coordinates for 3D mapping
    scaler_global = StandardScaler()
    X_scaled_all = scaler_global.fit_transform(df[spec_cols].values)
    pca_global = PCA(n_components=2)
    X_pca_all = pca_global.fit_transform(X_scaled_all)
    var_exp = pca_global.explained_variance_ratio_
    
    print(f"      Samples: {n_samples} | Spectral Bands: {len(spec_cols)}")
    print(f"      3D Kriging Coordinates: PC1={var_exp[0]*100:.2f}%, PC2={var_exp[1]*100:.2f}%")
    print(f"      Total Spectral Variance Captured: {sum(var_exp)*100:.2f}%\n")
    
    summary_metrics = []
    comparison_data = {
        'Sample_ID': [f"Sample_{i+1}" for i in range(n_samples)],
        'PC1_Axis_X': np.round(X_pca_all[:, 0], 4),
        'PC2_Axis_Y': np.round(X_pca_all[:, 1], 4)
    }
    
    print("[3/5] Performing 3D Gaussian Process (Spectral Kriging) LOOCV...")
    print("-" * 115)
    print(f"{'Target':<12} | {'Samples':<7} | {'Kriging Acc':<12} | {'Ratio Acc':<11} | {'LOOCV R²':<10} | {'RMSE':<10} | {'Saved Model File'}")
    print("-" * 115)
    
    loo = LeaveOneOut()
    
    for target in soil_cols:
        sub = df.dropna(subset=[target]).copy()
        valid_idx = sub.index
        X = sub[spec_cols].values
        y = sub[target].values
        n_valid = len(y)
        
        # Geostatistical / Kriging Kernel: Covariance (signal variance) * Spatial correlation (Matern 3/2) + Nugget (noise)
        kernel = C(1.0, (1e-2, 1e4)) * Matern(length_scale=[1.0, 1.0], length_scale_bounds=(0.1, 50.0), nu=1.5) + WhiteKernel(noise_level=0.05, noise_level_bounds=(1e-3, 5.0))
        
        # Build 3D Kriging Pipeline
        pipeline_kriging = Pipeline([
            ('scaler', StandardScaler()),
            ('pca', PCA(n_components=2)),
            ('gpr', GaussianProcessRegressor(kernel=kernel, alpha=1e-3, n_restarts_optimizer=1, random_state=42))
        ])
        
        # Perform LOOCV sample-by-sample
        y_pred_loocv = np.zeros(n_valid)
        y_std_loocv = np.zeros(n_valid)
        
        for train_idx, test_idx in loo.split(X):
            X_train, X_test = X[train_idx], X[test_idx]
            y_train = y[train_idx]
            
            pipeline_kriging.fit(X_train, y_train)
            
            # Predict mean and standard deviation (uncertainty)
            # Access GPR model inside pipeline for uncertainty calculation
            scaler_fold = pipeline_kriging.named_steps['scaler']
            pca_fold = pipeline_kriging.named_steps['pca']
            gpr_fold = pipeline_kriging.named_steps['gpr']
            
            X_test_trans = pca_fold.transform(scaler_fold.transform(X_test))
            p_mean, p_std = gpr_fold.predict(X_test_trans, return_std=True)
            y_pred_loocv[test_idx[0]] = max(0.0, float(p_mean[0]))
            y_std_loocv[test_idx[0]] = float(p_std[0])
            
        # Metrics
        rmse = np.sqrt(mean_squared_error(y, y_pred_loocv))
        mae = mean_absolute_error(y, y_pred_loocv)
        r2 = r2_score(y, y_pred_loocv)
        val_range = y.max() - y.min()
        range_acc = (1.0 - (rmse / (val_range if val_range > 0 else 1.0))) * 100.0
        
        ratio_accs = [
            (min(a, pr) / max(a, pr)) * 100.0 if max(a, pr) > 0 else (100.0 if a == 0 and pr == 0 else 0.0)
            for a, pr in zip(y, y_pred_loocv)
        ]
        avg_ratio_acc = np.mean(ratio_accs)
        
        # Train full production Kriging model and save
        pipeline_kriging.fit(X, y)
        clean_name = target.replace('/', '_').replace(' ', '_').replace('%', 'Pct').replace('(', '').replace(')', '')
        model_filename = f"{clean_name}_3d_kriging.joblib"
        model_path = os.path.join(models_dir, model_filename)
        joblib.dump(pipeline_kriging, model_path)
        
        summary_metrics.append({
            'Target Parameter': target,
            'Total Samples': n_valid,
            '3D Kriging Accuracy (%)': round(range_acc, 2),
            'Ratio Match Accuracy (%)': round(avg_ratio_acc, 2),
            'LOOCV R² (%)': round(r2 * 100.0, 2),
            'LOOCV RMSE': round(rmse, 4),
            'LOOCV MAE': round(mae, 4),
            'Mean Uncertainty (Std Dev)': round(float(np.mean(y_std_loocv)), 4),
            'Saved Model File': model_path
        })
        
        # Store aligned sample data
        act_col = np.full(n_samples, np.nan)
        pred_col = np.full(n_samples, np.nan)
        std_col = np.full(n_samples, np.nan)
        diff_col = np.full(n_samples, np.nan)
        ratio_acc_col = np.full(n_samples, np.nan)
        
        act_col[valid_idx] = np.round(y, 4)
        pred_col[valid_idx] = np.round(y_pred_loocv, 4)
        std_col[valid_idx] = np.round(y_std_loocv, 4)
        diff_col[valid_idx] = np.round(np.abs(y - y_pred_loocv), 4)
        ratio_acc_col[valid_idx] = np.round(ratio_accs, 2)
        
        comparison_data[f'{clean_name}_Actual'] = act_col
        comparison_data[f'{clean_name}_Kriging_Pred'] = pred_col
        comparison_data[f'{clean_name}_AbsError'] = diff_col
        comparison_data[f'{clean_name}_StdDev_Uncertainty'] = std_col
        comparison_data[f'{clean_name}_Accuracy%'] = ratio_acc_col
        
        print(f"{target:<12} | {n_valid:<7} | {range_acc:6.2f}%      | {avg_ratio_acc:6.2f}%    | {r2*100:6.2f}%   | {rmse:8.4f} | {model_path}")
        
    print("-" * 115)
    print(f"All 12 3D Kriging models successfully trained and saved in '{models_dir}/' folder!\n")
    
    # 4. Generate Multi-Sheet Excel Report
    print(f"[4/5] Writing Excel workbook to '{output_excel}'...")
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        pd.DataFrame(summary_metrics).to_excel(writer, sheet_name='3D_Kriging_Summary', index=False)
        pd.DataFrame(comparison_data).to_excel(writer, sheet_name='All_Actual_vs_Kriging_LOOCV', index=False)
        
        # Micronutrients Tab
        micro_cols = ['Sample_ID', 'PC1_Axis_X', 'PC2_Axis_Y']
        for t in ['Zn_ppm', 'Cu_ppm', 'Fe_ppm', 'Mn_ppm', 'B_ppm']:
            for s in ['_Actual', '_Kriging_Pred', '_AbsError', '_StdDev_Uncertainty', '_Accuracy%']:
                if f'{t}{s}' in comparison_data:
                    micro_cols.append(f'{t}{s}')
        pd.DataFrame({c: comparison_data[c] for c in micro_cols}).to_excel(writer, sheet_name='3D_Kriging_Micronutrients', index=False)
        
        # Macronutrients Tab
        macro_cols = ['Sample_ID', 'PC1_Axis_X', 'PC2_Axis_Y']
        for t in ['OCPct', 'N_Kg_ha', 'P2O5', 'K2O', 'Ca_meq', 'Mg_meq', 'SO4']:
            for s in ['_Actual', '_Kriging_Pred', '_AbsError', '_StdDev_Uncertainty', '_Accuracy%']:
                if f'{t}{s}' in comparison_data:
                    macro_cols.append(f'{t}{s}')
        pd.DataFrame({c: comparison_data[c] for c in macro_cols}).to_excel(writer, sheet_name='3D_Kriging_Macronutrients', index=False)
        
    # 5. Styling with openpyxl
    print(f"[5/5] Applying openpyxl visual formatting to '{output_excel}'...")
    wb = openpyxl.load_workbook(output_excel)
    header_fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    coord_fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
    act_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")  # light green
    pred_fill = PatternFill(start_color="DDEBF7", end_color="DDEBF7", fill_type="solid") # light blue
    err_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")  # light yellow
    std_fill = PatternFill(start_color="EAEAEA", end_color="EAEAEA", fill_type="solid")  # light gray
    border_thin = Border(left=Side(style='thin', color='E0E0E0'), right=Side(style='thin', color='E0E0E0'),
                         top=Side(style='thin', color='E0E0E0'), bottom=Side(style='thin', color='E0E0E0'))
    
    for ws in wb.worksheets:
        ws.views.sheetView[0].showGridLines = True
        for col in range(1, ws.max_column + 1):
            cell = ws.cell(row=1, column=col)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            ws.row_dimensions[1].height = 28
            
            col_name = str(cell.value or '')
            for r in range(2, ws.max_row + 1):
                c = ws.cell(row=r, column=col)
                c.border = border_thin
                if 'Axis' in col_name or 'PC' in col_name:
                    c.fill = coord_fill
                elif 'Actual' in col_name:
                    c.fill = act_fill
                elif 'Kriging_Pred' in col_name:
                    c.fill = pred_fill
                elif 'AbsError' in col_name or 'Accuracy' in col_name:
                    c.fill = err_fill
                elif 'Uncertainty' in col_name or 'StdDev' in col_name:
                    c.fill = std_fill
                    
                if isinstance(c.value, (int, float)):
                    c.alignment = Alignment(horizontal="right", vertical="center")
                else:
                    c.alignment = Alignment(horizontal="center", vertical="center")
                    
            max_len = max(len(str(ws.cell(row=r, column=col).value or '')) for r in range(1, min(ws.max_row + 1, 55)))
            ws.column_dimensions[get_column_letter(col)].width = max(max_len + 4, 13)
            
    wb.save(output_excel)
    print(f"\n3D Kriging Training Pipeline complete!")
    print(f"Results Excel saved: '{output_excel}'")
    print(f"Models directory: '{models_dir}/'")

def predict_soil_3d_kriging(spectrum_21_bands, models_dir='models_3d_kriging'):
    """
    Predicts soil nutrients and uncertainty standard deviations for a new 21-band spectrum.
    :return: dict of {nutrient: {'prediction': float, 'uncertainty_std': float}}
    """
    spectrum = np.array(spectrum_21_bands, dtype=float).reshape(1, -1)
    results = {}
    
    for file in sorted(os.listdir(models_dir)):
        if file.endswith('.joblib'):
            nutrient = file.replace('_3d_kriging.joblib', '')
            model_path = os.path.join(models_dir, file)
            pipeline = joblib.load(model_path)
            
            scaler = pipeline.named_steps['scaler']
            pca = pipeline.named_steps['pca']
            gpr = pipeline.named_steps['gpr']
            
            X_2d = pca.transform(scaler.transform(spectrum))
            p_mean, p_std = gpr.predict(X_2d, return_std=True)
            
            results[nutrient] = {
                'prediction': round(max(0.0, float(p_mean[0])), 4),
                'uncertainty_std': round(float(p_std[0]), 4),
                '95%_confidence_interval': [
                    round(max(0.0, float(p_mean[0] - 1.96 * p_std[0])), 4),
                    round(float(p_mean[0] + 1.96 * p_std[0]), 4)
                ]
            }
    return results

if __name__ == '__main__':
    train_and_evaluate_3d_kriging()
