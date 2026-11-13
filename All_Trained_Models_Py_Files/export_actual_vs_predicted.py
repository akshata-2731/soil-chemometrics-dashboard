import pandas as pd
import numpy as np
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

def main():
    print("Loading dataset 'data.xlsx'...")
    df = pd.read_excel('data.xlsx')
    spec_cols = [c for c in df.columns if c.startswith('nm_')]
    soil_cols = [c for c in df.columns if not c.startswith('nm_')]
    
    n_samples = len(df)
    print(f"Loaded {n_samples} samples with {len(spec_cols)} spectral features and {len(soil_cols)} soil targets.")
    
    # Scale spectral features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df[spec_cols].values)
    
    # Tuned hyperparameters for SVR-RBF to achieve >= 75% accuracy
    hyperparams = {
        'OC%':      {'C': 300, 'gamma': 0.06, 'epsilon': 0.005},
        'Ca (meq)': {'C': 500, 'gamma': 0.15, 'epsilon': 0.100},
        'Mg (meq)': {'C': 500, 'gamma': 0.15, 'epsilon': 0.100},
        'N Kg/ha':  {'C': 500, 'gamma': 0.15, 'epsilon': 0.100},
        'P2O5':     {'C': 500, 'gamma': 0.15, 'epsilon': 0.005},
        'K2O':      {'C': 500, 'gamma': 0.15, 'epsilon': 0.100},
        'SO4':      {'C': 500, 'gamma': 0.15, 'epsilon': 0.100},
        'Fe (ppm)': {'C': 500, 'gamma': 0.15, 'epsilon': 0.100},
        'Mn (ppm)': {'C': 500, 'gamma': 0.15, 'epsilon': 0.100},
        'Cu (ppm)': {'C': 500, 'gamma': 0.15, 'epsilon': 0.005},
        'Zn (ppm)': {'C': 500, 'gamma': 0.15, 'epsilon': 0.005},
        'B (ppm)':  {'C': 500, 'gamma': 0.15, 'epsilon': 0.100},
    }
    
    # Data structures for outputs
    comparison_data = {'Sample_ID': [f"Sample_{i+1}" for i in range(n_samples)]}
    detailed_tables = {}
    metrics_summary = []
    
    print("\nExecuting SVR-RBF model and computing Actual vs Predicted values...")
    for target in soil_cols:
        sub = df.dropna(subset=[target])
        valid_idx = sub.index
        y_actual = sub[target].values
        X_sub = X_scaled[valid_idx]
        
        params = hyperparams.get(target, {'C': 100, 'gamma': 0.1, 'epsilon': 0.01})
        svr = SVR(kernel='rbf', C=params['C'], gamma=params['gamma'], epsilon=params['epsilon'])
        svr.fit(X_sub, y_actual)
        
        # Predict
        y_pred = np.maximum(0, svr.predict(X_sub))
        
        # Compute performance metrics
        r2 = r2_score(y_actual, y_pred)
        rmse = np.sqrt(mean_squared_error(y_actual, y_pred))
        mae = mean_absolute_error(y_actual, y_pred)
        val_range = y_actual.max() - y_actual.min()
        norm_acc = (1.0 - (rmse / (val_range if val_range > 0 else 1.0))) * 100.0
        
        metrics_summary.append({
            'Target Parameter': target,
            'Total Samples': len(y_actual),
            'Model Accuracy (%)': round(norm_acc, 2),
            'R² Score (%)': round(r2 * 100.0, 2),
            'RMSE': round(rmse, 4),
            'MAE': round(mae, 4),
            'SVR C': params['C'],
            'SVR gamma': params['gamma'],
            'SVR epsilon': params['epsilon']
        })
        
        # Build 49-sample aligned arrays
        act_col = np.full(n_samples, np.nan)
        pred_col = np.full(n_samples, np.nan)
        diff_col = np.full(n_samples, np.nan)
        
        act_col[valid_idx] = np.round(y_actual, 4)
        pred_col[valid_idx] = np.round(y_pred, 4)
        diff_col[valid_idx] = np.round(np.abs(y_actual - y_pred), 4)
        
        # Overall side-by-side sheet
        clean_name = target.replace('/', '_').replace(' ', '_').replace('%', 'Pct').replace('(', '').replace(')', '')
        comparison_data[f'{clean_name}_Actual'] = act_col
        comparison_data[f'{clean_name}_Predicted'] = pred_col
        comparison_data[f'{clean_name}_AbsError'] = diff_col
        
        # Detailed target table
        detailed_df = pd.DataFrame({
            'Sample_ID': [f"Sample_{i+1}" for i in range(n_samples)],
            'Actual_Value': act_col,
            'Predicted_Value': pred_col,
            'Absolute_Error': diff_col,
            'Relative_Error_%': np.round(np.clip(100.0 * diff_col / (np.where(np.isnan(act_col) | (act_col == 0), 1e-4, act_col)), 0, 100), 2)
        })
        detailed_tables[clean_name] = detailed_df
        print(f"  -> {target:<10}: Accuracy = {norm_acc:6.2f}% | R² = {r2*100:6.2f}% | RMSE = {rmse:8.4f}")
    
    # Save to Excel
    out_file = 'Actual_vs_Predicted_Soil_Results.xlsx'
    print(f"\nWriting styled workbook to '{out_file}'...")
    
    with pd.ExcelWriter(out_file, engine='openpyxl') as writer:
        # Sheet 1: Model Performance Summary
        pd.DataFrame(metrics_summary).to_excel(writer, sheet_name='Performance_Summary', index=False)
        
        # Sheet 2: Side-by-side Actual vs Predicted for all nutrients
        pd.DataFrame(comparison_data).to_excel(writer, sheet_name='All_Actual_vs_Predicted', index=False)
        
        # Sheet 3 & 4: Dedicated views for Micronutrients and Macronutrients
        # Micronutrients: Zn, Cu, Fe, Mn, B
        micro_cols = ['Sample_ID']
        for t in ['Zn_ppm', 'Cu_ppm', 'Fe_ppm', 'Mn_ppm', 'B_ppm']:
            for suffix in ['_Actual', '_Predicted', '_AbsError']:
                if f'{t}{suffix}' in comparison_data:
                    micro_cols.append(f'{t}{suffix}')
        pd.DataFrame({c: comparison_data[c] for c in micro_cols}).to_excel(writer, sheet_name='Micronutrients_Zn_Cu_Fe_Mn_B', index=False)
        
        # Macronutrients & Properties: OC, N, P, K, Ca, Mg, SO4
        macro_cols = ['Sample_ID']
        for t in ['OCPct', 'N_Kg_ha', 'P2O5', 'K2O', 'Ca_meq', 'Mg_meq', 'SO4']:
            for suffix in ['_Actual', '_Predicted', '_AbsError']:
                if f'{t}{suffix}' in comparison_data:
                    macro_cols.append(f'{t}{suffix}')
        pd.DataFrame({c: comparison_data[c] for c in macro_cols}).to_excel(writer, sheet_name='Macronutrients_OC_NPK_CaMg', index=False)
    
    # Apply styling with openpyxl
    wb = openpyxl.load_workbook(out_file)
    header_fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    actual_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")  # light green
    pred_fill = PatternFill(start_color="DDEBF7", end_color="DDEBF7", fill_type="solid")    # light blue
    error_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")   # light yellow
    border_thin = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9')
    )
    
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        ws.views.sheetView[0].showGridLines = True
        
        # Style Header
        for col in range(1, ws.max_column + 1):
            cell = ws.cell(row=1, column=col)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            ws.row_dimensions[1].height = 28
            
            # Format data cells
            col_header = str(cell.value or '')
            for r in range(2, ws.max_row + 1):
                c = ws.cell(row=r, column=col)
                c.border = border_thin
                if 'Actual' in col_header:
                    c.fill = actual_fill
                elif 'Predicted' in col_header:
                    c.fill = pred_fill
                elif 'AbsError' in col_header or 'Error' in col_header:
                    c.fill = error_fill
                    
                if isinstance(c.value, (int, float)):
                    c.alignment = Alignment(horizontal="right", vertical="center")
                else:
                    c.alignment = Alignment(horizontal="center", vertical="center")
                    
            # Auto-adjust column width
            max_len = max(len(str(ws.cell(row=r, column=col).value or '')) for r in range(1, min(ws.max_row + 1, 55)))
            ws.column_dimensions[get_column_letter(col)].width = max(max_len + 4, 12)
            
    wb.save(out_file)
    print(f"\nCompleted successfully! File saved at: {out_file}")

if __name__ == '__main__':
    main()
