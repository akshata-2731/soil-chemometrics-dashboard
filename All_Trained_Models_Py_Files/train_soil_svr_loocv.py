"""
Soil Spectral Analysis & Nutrient Prediction using Support Vector Regression (SVR-RBF)
======================================================================================
This script:
1. Loads soil reflectance spectra (21 wavelengths) and 12 nutrient targets from data.xlsx.
2. Performs Leave-One-Out Cross-Validation (LOOCV) for rigorous unseen sample validation.
3. Trains and saves calibrated production models (.joblib) into a 'models/' folder.
4. Generates a beautifully styled Excel report: 'Actual_vs_Pred_LOOCV_Results.xlsx'.
5. Provides a ready-to-use function to predict nutrients for new unseen spectral data.
"""

import os
import pandas as pd
import numpy as np
import joblib
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import LeaveOneOut, cross_val_predict
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

def train_and_evaluate_loocv(data_file='data.xlsx', models_dir='models', output_excel='Actual_vs_Pred_LOOCV_Results.xlsx'):
    # 1. Ensure models directory exists
    os.makedirs(models_dir, exist_ok=True)
    print(f"[1/5] Ensuring models directory '{models_dir}/' is ready...")
    
    # 2. Load dataset
    print(f"[2/5] Reading data from '{data_file}'...")
    df = pd.read_excel(data_file)
    spec_cols = [c for c in df.columns if c.startswith('nm_')]
    soil_cols = [c for c in df.columns if not c.startswith('nm_')]
    n_samples = len(df)
    
    print(f"      Total samples: {n_samples}")
    print(f"      Spectral features ({len(spec_cols)} bands): {spec_cols[:4]} ... {spec_cols[-3:]}")
    print(f"      Target soil nutrients ({len(soil_cols)}): {soil_cols}")
    
    # 3. Optimized Hyperparameters for SVR-RBF
    # Tailored per target to balance LOOCV generalizability and accuracy
    target_hyperparams = {
        'OC%':      {'C': 50,  'gamma': 'scale', 'epsilon': 0.05},
        'Ca (meq)': {'C': 20,  'gamma': 0.05,    'epsilon': 0.10},
        'Mg (meq)': {'C': 20,  'gamma': 0.05,    'epsilon': 0.10},
        'N Kg/ha':  {'C': 50,  'gamma': 'scale', 'epsilon': 0.10},
        'P2O5':     {'C': 20,  'gamma': 'scale', 'epsilon': 0.05},
        'K2O':      {'C': 20,  'gamma': 'scale', 'epsilon': 0.10},
        'SO4':      {'C': 20,  'gamma': 'scale', 'epsilon': 0.10},
        'Fe (ppm)': {'C': 30,  'gamma': 0.05,    'epsilon': 0.10},
        'Mn (ppm)': {'C': 30,  'gamma': 0.05,    'epsilon': 0.10},
        'Cu (ppm)': {'C': 30,  'gamma': 0.05,    'epsilon': 0.05},
        'Zn (ppm)': {'C': 30,  'gamma': 0.05,    'epsilon': 0.05},
        'B (ppm)':  {'C': 30,  'gamma': 0.05,    'epsilon': 0.10},
    }
    
    # Prepare storage structures
    summary_metrics = []
    comparison_data = {'Sample_ID': [f"Sample_{i+1}" for i in range(n_samples)]}
    
    print("\n[3/5] Performing Leave-One-Out Cross-Validation (LOOCV) & Training Models...")
    print("-" * 95)
    print(f"{'Target':<12} | {'Samples':<7} | {'LOOCV Acc':<12} | {'LOOCV R2':<10} | {'LOOCV RMSE':<12} | {'Model File'}")
    print("-" * 95)
    
    for target in soil_cols:
        sub = df.dropna(subset=[target]).copy()
        valid_idx = sub.index
        X = sub[spec_cols].values
        y = sub[target].values
        n_valid = len(y)
        
        params = target_hyperparams.get(target, {'C': 30, 'gamma': 'scale', 'epsilon': 0.05})
        
        # Build scikit-learn Pipeline with StandardScaler & SVR(kernel='rbf')
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('svr', SVR(kernel='rbf', C=params['C'], gamma=params['gamma'], epsilon=params['epsilon']))
        ])
        
        # --- A. LOOCV (Leave-One-Out Cross-Validation) ---
        loo = LeaveOneOut()
        y_loocv_pred = cross_val_predict(pipeline, X, y, cv=loo)
        y_loocv_pred = np.maximum(0, y_loocv_pred) # Non-negative soil concentrations
        
        # Evaluate LOOCV metrics
        rmse_loocv = np.sqrt(mean_squared_error(y, y_loocv_pred))
        mae_loocv = mean_absolute_error(y, y_loocv_pred)
        r2_loocv = r2_score(y, y_loocv_pred)
        val_range = y.max() - y.min()
        acc_loocv = (1.0 - (rmse_loocv / (val_range if val_range > 0 else 1.0))) * 100.0
        
        # --- B. Train Full Production Model & Save to disk ---
        pipeline.fit(X, y)
        clean_name = target.replace('/', '_').replace(' ', '_').replace('%', 'Pct').replace('(', '').replace(')', '')
        model_filename = f"{clean_name}_svr_rbf.joblib"
        model_filepath = os.path.join(models_dir, model_filename)
        joblib.dump(pipeline, model_filepath)
        
        summary_metrics.append({
            'Target Parameter': target,
            'Total Samples': n_valid,
            'LOOCV Accuracy (%)': round(acc_loocv, 2),
            'LOOCV R² (%)': round(r2_loocv * 100.0, 2),
            'LOOCV RMSE': round(rmse_loocv, 4),
            'LOOCV MAE': round(mae_loocv, 4),
            'SVR C': params['C'],
            'SVR gamma': str(params['gamma']),
            'SVR epsilon': params['epsilon'],
            'Saved Model File': model_filepath
        })
        
        # Record sample-by-sample predictions for the 49 samples
        act_col = np.full(n_samples, np.nan)
        pred_col = np.full(n_samples, np.nan)
        diff_col = np.full(n_samples, np.nan)
        
        act_col[valid_idx] = np.round(y, 4)
        pred_col[valid_idx] = np.round(y_loocv_pred, 4)
        diff_col[valid_idx] = np.round(np.abs(y - y_loocv_pred), 4)
        
        comparison_data[f'{clean_name}_Actual'] = act_col
        comparison_data[f'{clean_name}_LOOCV_Pred'] = pred_col
        comparison_data[f'{clean_name}_AbsError'] = diff_col
        
        print(f"{target:<12} | {n_valid:<7} | {acc_loocv:6.2f}%    | {r2_loocv*100:6.2f}%   | {rmse_loocv:10.4f}   | {model_filepath}")
        
    print("-" * 95)
    print("All 12 production models successfully trained and saved in 'models/' folder!")
    
    # 4. Generate Excel Workbook
    print(f"\n[4/5] Writing Excel results report to '{output_excel}'...")
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        # Sheet 1: LOOCV Performance Summary
        pd.DataFrame(summary_metrics).to_excel(writer, sheet_name='LOOCV_Performance_Summary', index=False)
        
        # Sheet 2: All Nutrients Actual vs LOOCV Predicted
        pd.DataFrame(comparison_data).to_excel(writer, sheet_name='All_Actual_vs_LOOCV_Pred', index=False)
        
        # Sheet 3: Micronutrients (Zn, Cu, Fe, Mn, B)
        micro_cols = ['Sample_ID']
        for t in ['Zn_ppm', 'Cu_ppm', 'Fe_ppm', 'Mn_ppm', 'B_ppm']:
            for s in ['_Actual', '_LOOCV_Pred', '_AbsError']:
                if f'{t}{s}' in comparison_data:
                    micro_cols.append(f'{t}{s}')
        pd.DataFrame({c: comparison_data[c] for c in micro_cols}).to_excel(writer, sheet_name='Micronutrients_Zn_Cu_Fe_Mn_B', index=False)
        
        # Sheet 4: Macronutrients & Organic Matter (OC, N, P, K, Ca, Mg, SO4)
        macro_cols = ['Sample_ID']
        for t in ['OCPct', 'N_Kg_ha', 'P2O5', 'K2O', 'Ca_meq', 'Mg_meq', 'SO4']:
            for s in ['_Actual', '_LOOCV_Pred', '_AbsError']:
                if f'{t}{s}' in comparison_data:
                    macro_cols.append(f'{t}{s}')
        pd.DataFrame({c: comparison_data[c] for c in macro_cols}).to_excel(writer, sheet_name='Macronutrients_OC_NPK_CaMg', index=False)

    # 5. Styling with Openpyxl
    print(f"[5/5] Applying styling and visual formatting to '{output_excel}'...")
    wb = openpyxl.load_workbook(output_excel)
    header_fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    act_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")  # light green
    pred_fill = PatternFill(start_color="DDEBF7", end_color="DDEBF7", fill_type="solid") # light blue
    err_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")  # light yellow
    border_thin = Border(
        left=Side(style='thin', color='E0E0E0'),
        right=Side(style='thin', color='E0E0E0'),
        top=Side(style='thin', color='E0E0E0'),
        bottom=Side(style='thin', color='E0E0E0')
    )
    
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        ws.views.sheetView[0].showGridLines = True
        
        # Format header
        for col in range(1, ws.max_column + 1):
            cell = ws.cell(row=1, column=col)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            ws.row_dimensions[1].height = 28
            
            # Format data cells
            col_name = str(cell.value or '')
            for r in range(2, ws.max_row + 1):
                c = ws.cell(row=r, column=col)
                c.border = border_thin
                if 'Actual' in col_name:
                    c.fill = act_fill
                elif 'Pred' in col_name:
                    c.fill = pred_fill
                elif 'AbsError' in col_name or 'Error' in col_name:
                    c.fill = err_fill
                    
                if isinstance(c.value, (int, float)):
                    c.alignment = Alignment(horizontal="right", vertical="center")
                else:
                    c.alignment = Alignment(horizontal="center", vertical="center")
                    
            max_len = max(len(str(ws.cell(row=r, column=col).value or '')) for r in range(1, min(ws.max_row + 1, 55)))
            ws.column_dimensions[get_column_letter(col)].width = max(max_len + 4, 13)
            
    wb.save(output_excel)
    print(f"\nDone! Excel report successfully saved: '{output_excel}'")
    print(f"All models saved in: '{models_dir}/'")

def predict_soil(spectrum_21_bands, models_dir='models'):
    """
    Utility function to predict all 12 soil nutrients for a new spectrum.
    :param spectrum_21_bands: array-like of 21 wavelength reflectance values
    :return: dictionary of predicted nutrient values
    """
    spectrum = np.array(spectrum_21_bands).reshape(1, -1)
    predictions = {}
    
    for file in os.listdir(models_dir):
        if file.endswith('.joblib'):
            target_name = file.replace('_svr_rbf.joblib', '')
            model_path = os.path.join(models_dir, file)
            model = joblib.load(model_path)
            pred = float(model.predict(spectrum)[0])
            predictions[target_name] = round(max(0.0, pred), 4)
            
    return predictions

if __name__ == '__main__':
    train_and_evaluate_loocv()
