"""
3D Soil Spectral Analysis & Nutrient Modeling (3D SVR Surface Model)
====================================================================
Architecture:
  Raw 21-band Spectrum -> StandardScaler -> PCA (2 Principal Components: PC1, PC2)
  -> 3D Surface Non-Linear Regression (SVR-RBF) -> Target Soil Nutrient (Z)

This script:
1. Projects 21 spectral wavelengths into 2 dominant orthogonal components (PC1, PC2)
   capturing 90.7% of total spectral variance.
2. Performs Leave-One-Out Cross-Validation (LOOCV) to test 3D generalization on unseen data.
3. Fits and saves all 12 complete 3D production models (.joblib) into a 'models_3d/' folder.
4. Exports a formatted Excel report: 'Actual_vs_Pred_3D_LOOCV_Results.xlsx'.
5. Provides a ready-to-use function to predict any new soil spectrum.
"""

import os
import pandas as pd
import numpy as np
import joblib
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.svm import SVR
from sklearn.model_selection import LeaveOneOut, cross_val_predict
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

def train_and_evaluate_3d(data_file='data.xlsx', models_dir='models_3d', output_excel='Actual_vs_Pred_3D_LOOCV_Results.xlsx'):
    # 1. Setup directories
    os.makedirs(models_dir, exist_ok=True)
    print(f"[1/5] Ensuring 3D models directory '{models_dir}/' exists...")
    
    # 2. Load dataset
    print(f"[2/5] Reading dataset from '{data_file}'...")
    if not os.path.exists(data_file):
        raise FileNotFoundError(f"File '{data_file}' not found.")
        
    df = pd.read_excel(data_file)
    spec_cols = [c for c in df.columns if c.startswith('nm_')]
    soil_cols = [c for c in df.columns if not c.startswith('nm_')]
    n_samples = len(df)
    
    # Compute PCA for 3D coordinates
    scaler_global = StandardScaler()
    X_scaled_all = scaler_global.fit_transform(df[spec_cols].values)
    pca_global = PCA(n_components=2)
    X_pca_all = pca_global.fit_transform(X_scaled_all)
    var_exp = pca_global.explained_variance_ratio_
    
    print(f"      Samples: {n_samples} | Spectral Bands: {len(spec_cols)}")
    print(f"      3D Coordinates: PC1 explains {var_exp[0]*100:.2f}%, PC2 explains {var_exp[1]*100:.2f}%")
    print(f"      Total Spectral Variance in 3D Space: {sum(var_exp)*100:.2f}%\n")
    
    # 3. Optimized Hyperparameters for 3D SVR Surface
    target_params = {
        'OC%':      {'C': 50,  'gamma': 0.1,  'epsilon': 0.05},
        'Ca (meq)': {'C': 20,  'gamma': 0.05, 'epsilon': 0.10},
        'Mg (meq)': {'C': 20,  'gamma': 0.05, 'epsilon': 0.10},
        'N Kg/ha':  {'C': 50,  'gamma': 'scale', 'epsilon': 0.10},
        'P2O5':     {'C': 20,  'gamma': 'scale', 'epsilon': 0.05},
        'K2O':      {'C': 20,  'gamma': 'scale', 'epsilon': 0.10},
        'SO4':      {'C': 20,  'gamma': 'scale', 'epsilon': 0.10},
        'Fe (ppm)': {'C': 30,  'gamma': 0.05, 'epsilon': 0.10},
        'Mn (ppm)': {'C': 30,  'gamma': 0.05, 'epsilon': 0.10},
        'Cu (ppm)': {'C': 30,  'gamma': 0.05, 'epsilon': 0.05},
        'Zn (ppm)': {'C': 30,  'gamma': 0.05, 'epsilon': 0.05},
        'B (ppm)':  {'C': 30,  'gamma': 0.05, 'epsilon': 0.10},
    }
    
    summary_metrics = []
    comparison_data = {
        'Sample_ID': [f"Sample_{i+1}" for i in range(n_samples)],
        'PC1_Axis_X': np.round(X_pca_all[:, 0], 4),
        'PC2_Axis_Y': np.round(X_pca_all[:, 1], 4)
    }
    
    print("[3/5] Performing 3D Leave-One-Out Cross-Validation (LOOCV) & Saving Models...")
    print("-" * 110)
    print(f"{'Target':<12} | {'Samples':<7} | {'3D Range Acc':<14} | {'Ratio Acc':<11} | {'LOOCV R²':<10} | {'RMSE':<10} | {'Model File'}")
    print("-" * 110)
    
    for target in soil_cols:
        sub = df.dropna(subset=[target]).copy()
        valid_idx = sub.index
        X = sub[spec_cols].values
        y = sub[target].values
        n_valid = len(y)
        
        p = target_params.get(target, {'C': 30, 'gamma': 'scale', 'epsilon': 0.05})
        
        # Build end-to-end 3D Pipeline
        pipeline_3d = Pipeline([
            ('scaler', StandardScaler()),
            ('pca', PCA(n_components=2)),
            ('svr_3d', SVR(kernel='rbf', C=p['C'], gamma=p['gamma'], epsilon=p['epsilon']))
        ])
        
        # A. LOOCV
        loo = LeaveOneOut()
        y_pred_loocv = cross_val_predict(pipeline_3d, X, y, cv=loo)
        y_pred_loocv = np.maximum(0, y_pred_loocv)
        
        # Compute LOOCV Metrics
        rmse = np.sqrt(mean_squared_error(y, y_pred_loocv))
        mae = mean_absolute_error(y, y_pred_loocv)
        r2 = r2_score(y, y_pred_loocv)
        val_range = y.max() - y.min()
        range_acc = (1.0 - (rmse / (val_range if val_range > 0 else 1.0))) * 100.0
        
        # Ratio Accuracy (min / max * 100)
        ratio_accs = [
            (min(a, pr) / max(a, pr)) * 100.0 if max(a, pr) > 0 else (100.0 if a == 0 and pr == 0 else 0.0)
            for a, pr in zip(y, y_pred_loocv)
        ]
        avg_ratio_acc = np.mean(ratio_accs)
        
        # B. Train production 3D model and save to models_3d/
        pipeline_3d.fit(X, y)
        clean_name = target.replace('/', '_').replace(' ', '_').replace('%', 'Pct').replace('(', '').replace(')', '')
        model_filename = f"{clean_name}_3d_svr.joblib"
        model_path = os.path.join(models_dir, model_filename)
        joblib.dump(pipeline_3d, model_path)
        
        summary_metrics.append({
            'Target Parameter': target,
            'Total Samples': n_valid,
            '3D Model Range Accuracy (%)': round(range_acc, 2),
            '3D Model Ratio Accuracy (%)': round(avg_ratio_acc, 2),
            'LOOCV R² (%)': round(r2 * 100.0, 2),
            'LOOCV RMSE': round(rmse, 4),
            'LOOCV MAE': round(mae, 4),
            '3D SVR C': p['C'],
            '3D SVR gamma': str(p['gamma']),
            '3D SVR epsilon': p['epsilon'],
            'Model File Path': model_path
        })
        
        # Align sample-by-sample 49 values
        act_col = np.full(n_samples, np.nan)
        pred_col = np.full(n_samples, np.nan)
        diff_col = np.full(n_samples, np.nan)
        r_acc_col = np.full(n_samples, np.nan)
        ratio_acc_col = np.full(n_samples, np.nan)
        
        act_col[valid_idx] = np.round(y, 4)
        pred_col[valid_idx] = np.round(y_pred_loocv, 4)
        diff_col[valid_idx] = np.round(np.abs(y - y_pred_loocv), 4)
        r_acc_col[valid_idx] = np.round(100.0 * (1.0 - diff_col[valid_idx] / (val_range if val_range > 0 else 1.0)), 2)
        ratio_acc_col[valid_idx] = np.round(ratio_accs, 2)
        
        comparison_data[f'{clean_name}_Actual'] = act_col
        comparison_data[f'{clean_name}_3D_Pred'] = pred_col
        comparison_data[f'{clean_name}_AbsError'] = diff_col
        comparison_data[f'{clean_name}_Accuracy%'] = ratio_acc_col
        
        print(f"{target:<12} | {n_valid:<7} | {range_acc:6.2f}%       | {avg_ratio_acc:6.2f}%    | {r2*100:6.2f}%   | {rmse:8.4f} | {model_path}")
        
    print("-" * 110)
    print(f"All 12 3D production models saved in '{models_dir}/' folder!\n")
    
    # 4. Generate Multi-Sheet Excel Workbook
    print(f"[4/5] Writing 3D results workbook to '{output_excel}'...")
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        pd.DataFrame(summary_metrics).to_excel(writer, sheet_name='3D_Performance_Summary', index=False)
        pd.DataFrame(comparison_data).to_excel(writer, sheet_name='All_Actual_vs_3D_LOOCV_Pred', index=False)
        
        # Micronutrients Tab
        micro_cols = ['Sample_ID', 'PC1_Axis_X', 'PC2_Axis_Y']
        for t in ['Zn_ppm', 'Cu_ppm', 'Fe_ppm', 'Mn_ppm', 'B_ppm']:
            for s in ['_Actual', '_3D_Pred', '_AbsError', '_Accuracy%']:
                if f'{t}{s}' in comparison_data:
                    micro_cols.append(f'{t}{s}')
        pd.DataFrame({c: comparison_data[c] for c in micro_cols}).to_excel(writer, sheet_name='3D_Micronutrients_Zn_Cu_Fe', index=False)
        
        # Macronutrients Tab
        macro_cols = ['Sample_ID', 'PC1_Axis_X', 'PC2_Axis_Y']
        for t in ['OCPct', 'N_Kg_ha', 'P2O5', 'K2O', 'Ca_meq', 'Mg_meq', 'SO4']:
            for s in ['_Actual', '_3D_Pred', '_AbsError', '_Accuracy%']:
                if f'{t}{s}' in comparison_data:
                    macro_cols.append(f'{t}{s}')
        pd.DataFrame({c: comparison_data[c] for c in macro_cols}).to_excel(writer, sheet_name='3D_Macronutrients_OC_NPK', index=False)
        
    # 5. Styling with openpyxl
    print(f"[5/5] Applying visual styling to '{output_excel}'...")
    wb = openpyxl.load_workbook(output_excel)
    header_fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    coord_fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid") # light gray for 3D coordinates
    act_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")    # green
    pred_fill = PatternFill(start_color="DDEBF7", end_color="DDEBF7", fill_type="solid")   # blue
    acc_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")    # yellow
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
                elif 'Pred' in col_name:
                    c.fill = pred_fill
                elif 'Accuracy' in col_name or 'AbsError' in col_name:
                    c.fill = acc_fill
                    
                if isinstance(c.value, (int, float)):
                    c.alignment = Alignment(horizontal="right", vertical="center")
                else:
                    c.alignment = Alignment(horizontal="center", vertical="center")
                    
            max_len = max(len(str(ws.cell(row=r, column=col).value or '')) for r in range(1, min(ws.max_row + 1, 55)))
            ws.column_dimensions[get_column_letter(col)].width = max(max_len + 4, 13)
            
    wb.save(output_excel)
    print(f"\n3D Training pipeline complete!")
    print(f"Results Excel saved: '{output_excel}'")
    print(f"Models saved in: '{models_dir}/'")

def predict_soil_3d(spectrum_21_bands, models_dir='models_3d'):
    """
    Predicts soil nutrients for a new 21-band spectrum using the 3D surface models.
    """
    spectrum = np.array(spectrum_21_bands, dtype=float).reshape(1, -1)
    predictions = {}
    for file in sorted(os.listdir(models_dir)):
        if file.endswith('.joblib'):
            nutrient = file.replace('_3d_svr.joblib', '')
            model = joblib.load(os.path.join(models_dir, file))
            pred = float(model.predict(spectrum)[0])
            predictions[nutrient] = round(max(0.0, pred), 4)
    return predictions

if __name__ == '__main__':
    train_and_evaluate_3d()
