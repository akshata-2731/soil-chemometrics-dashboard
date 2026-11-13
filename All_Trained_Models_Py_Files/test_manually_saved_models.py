# -*- coding: utf-8 -*-
"""
================================================================================
MANUAL TESTING & INFERENCE SCRIPT USING SAVED SOIL MODELS
Created for: Akshata Honnaveri & Team
================================================================================
This script allows you to:
  1. Load the trained and saved 4-algorithm combination models (.pkl files)
  2. Test manually:
     - Single sample: pass 21 spectral band values -> get instant predictions
     - Batch Excel: pass any input Excel sheet with spectral columns (nm_410 to nm_940)
  3. Automatically compare Actual vs. Predicted values and save a clean,
     formatted Excel report with errors and accuracy percentages.

Usage:
  - Command line: python test_manually_saved_models.py
  - As a module:
      from test_manually_saved_models import predict_single_sample, evaluate_excel_file
================================================================================
"""

import os
import pickle
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error

MODELS_DIR = 'Final_Saved_Models_30'

SPECTRAL_BANDS = [
    'nm_410', 'nm_435', 'nm_460', 'nm_485', 'nm_510',
    'nm_535', 'nm_560', 'nm_585', 'nm_610', 'nm_645',
    'nm_680', 'nm_705', 'nm_730', 'nm_760', 'nm_810',
    'nm_860', 'nm_900', 'nm_940', 'nm_320', 'nm_280', 'nm_200'
]

NUTRIENTS = [
    ('OC%', 'OC', 'Organic Carbon (%)'),
    ('N Kg/ha', 'N', 'Available Nitrogen (Kg/ha)'),
    ('P2O5', 'P2O5', 'Available Phosphorus (Kg/ha)'),
    ('K2O', 'K2O', 'Available Potassium (Kg/ha)'),
    ('SO4', 'SO4', 'Available Sulfate (ppm)'),
    ('Fe (ppm)', 'Fe', 'Available Iron (ppm)'),
    ('Mn (ppm)', 'Mn', 'Available Manganese (ppm)'),
    ('Cu (ppm)', 'Cu', 'Available Copper (ppm)'),
    ('Zn (ppm)', 'Zn', 'Available Zinc (ppm)'),
    ('B (ppm)', 'B', 'Available Boron (ppm)'),
    ('Ca (meq)', 'Ca', 'Available Calcium (meq/100g)'),
    ('Mg (meq)', 'Mg', 'Available Magnesium (meq/100g)')
]

def load_saved_models(models_dir=MODELS_DIR):
    """
    Loads all 12 trained nutrient model bundles from disk.
    """
    bundles = {}
    if not os.path.exists(models_dir):
        raise FileNotFoundError(f"Directory '{models_dir}' not found. Please ensure models are trained first.")
        
    for target, short_n, full_n in NUTRIENTS:
        clean_name = target.replace('/', '_').replace(' ', '_').replace('%', 'Pct').replace('(', '').replace(')', '')
        pkl_file = os.path.join(models_dir, f"Model30_{clean_name}.pkl")
        if not os.path.exists(pkl_file):
            raise FileNotFoundError(f"Model file '{pkl_file}' not found.")
        with open(pkl_file, 'rb') as f:
            bundles[target] = pickle.load(f)
            
    print(f"--> Successfully loaded all 12 model bundles from '{models_dir}/'.")
    return bundles

def predict_single_sample(spectrum_values, bundles=None):
    """
    Predicts both class and continuous value for a single sample.
    Arguments:
      spectrum_values: list or numpy array of 21 reflectance values,
                       or dict mapping band names ('nm_410', etc.) to values.
    Returns:
      dict containing predictions for all 12 nutrients.
    """
    if bundles is None:
        bundles = load_saved_models()
        
    if isinstance(spectrum_values, dict):
        X = np.array([spectrum_values[b] for b in SPECTRAL_BANDS]).reshape(1, -1)
    else:
        X = np.array(spectrum_values).reshape(1, -1)
        
    if X.shape[1] != len(SPECTRAL_BANDS):
        raise ValueError(f"Expected {len(SPECTRAL_BANDS)} spectral bands, got {X.shape[1]}.")
        
    results = {}
    for target, short_n, full_n in NUTRIENTS:
        bundle = bundles[target]
        clf = bundle['classifier']
        scaler_c = bundle['scaler_classifier']
        scaler_r = bundle['scaler_regressor']
        models = bundle['models']
        weights = bundle['weights']
        rules = bundle['rules']
        v_min = bundle['val_min']
        v_max = bundle['val_max']
        
        # 1. Tier Classification
        X_sc_c = scaler_c.transform(X)
        pred_class = str(clf.predict(X_sc_c)[0]).strip()
        
        # 2. Quad-Stack Regression (SVR + ExtraTrees + Huber + PLS)
        X_sc_r = scaler_r.transform(X)
        p_svr = float(models['svr'].predict(X_sc_r)[0])
        p_et = float(models['et'].predict(X_sc_r)[0])
        p_hub = float(models['huber'].predict(X_sc_r)[0])
        p_pls = float(models['pls'].predict(X_sc_r).ravel()[0])
        
        raw_pred = max(0.0, float(weights[0]*p_svr + weights[1]*p_et + weights[2]*p_hub + weights[3]*p_pls))
        
        # 3. Dynamic Agronomic Tier Clamping
        if pred_class in rules:
            low_b, high_b = rules[pred_class]
            span = high_b - low_b
            safe_low = max(0.0, low_b - 0.10 * span)
            safe_high = high_b + 0.10 * span
            final_pred = float(np.clip(raw_pred, safe_low, safe_high))
            tier_range = f"[{low_b}, {high_b}]"
        else:
            final_pred = float(np.clip(raw_pred, v_min, v_max))
            tier_range = f"[{v_min}, {v_max}]"
            
        results[target] = {
            'short_name': short_n,
            'full_name': full_n,
            'predicted_class': pred_class,
            'predicted_value': round(final_pred, 4),
            'tier_limits': tier_range
        }
        
    return results

def assign_tier(val, rules):
    if pd.isna(val):
        return 'N/A'
    v = float(val)
    for c_name, (low_b, high_b) in rules.items():
        if low_b <= v <= high_b:
            return c_name
    if 'Low' in rules and v < rules['Low'][0]:
        return 'Low'
    if 'High' in rules and v > rules['High'][1]:
        return 'High'
    return 'Med'

def check_iso_match(act_val, pred_val, act_cls, pred_cls, rules, tol=0.15):
    if act_cls == pred_cls:
        return True
    if act_cls not in rules:
        return False
    low, high = rules[act_cls]
    span = high - low
    exp_low = low - tol * span
    exp_high = high + tol * span
    return exp_low <= pred_val <= exp_high

def evaluate_excel_file(input_excel='data.xlsx', output_excel='Manual_Test_Actual_vs_Predicted_Results.xlsx'):
    """
    Loads an Excel file, runs batch predictions, compares against Actual values (if present),
    and generates a full Excel report with accuracy metrics for both Class and Value.
    """
    bundles = load_saved_models()
    df = pd.read_excel(input_excel)
    
    # Check spectral columns
    missing_bands = [b for b in SPECTRAL_BANDS if b not in df.columns]
    if missing_bands:
        raise ValueError(f"Input file is missing spectral bands: {missing_bands}")
        
    n_samples = len(df)
    print(f"\n--> Processing {n_samples} samples from '{input_excel}'...")
    
    # Output structure
    sample_ids = df['Sample'].tolist() if 'Sample' in df.columns else [f"Sample_{i+1}" for i in range(n_samples)]
    summary_data = {'Sample_ID': sample_ids}
    
    accuracy_summary = []
    
    for target, short_n, full_n in NUTRIENTS:
        has_actual = target in df.columns
        bundle = bundles[target]
        rules = bundle['rules']
        
        preds_val = []
        preds_cls = []
        
        for idx in range(n_samples):
            spec_row = df.loc[idx, SPECTRAL_BANDS].values
            p_res = predict_single_sample(spec_row, bundles=bundles)
            preds_val.append(p_res[target]['predicted_value'])
            preds_cls.append(p_res[target]['predicted_class'])
            
        summary_data[f"{short_n}_Pred_Class"] = preds_cls
        summary_data[f"{short_n}_Pred_Value"] = preds_val
        
        if has_actual:
            acts = df[target].values
            valid_mask = ~pd.isna(acts)
            y_act = acts[valid_mask].astype(float)
            y_pred = np.array(preds_val)[valid_mask]
            
            act_classes = [assign_tier(a, rules) if not pd.isna(a) else 'N/A' for a in acts]
            pred_classes_arr = np.array(preds_cls)
            
            iso_matches = [
                ('YES' if check_iso_match(float(a), float(p), a_c, p_c, rules) else 'NO')
                if (not pd.isna(a) and a_c != 'N/A') else 'N/A'
                for a, p, a_c, p_c in zip(acts, preds_val, act_classes, pred_classes_arr)
            ]
            
            summary_data[f"{short_n}_Actual"] = acts
            summary_data[f"{short_n}_Actual_Class"] = act_classes
            summary_data[f"{short_n}_Class_Match"] = iso_matches
            
            # Error and Accuracy
            val_range = float(y_act.max() - y_act.min()) if len(y_act) > 0 else 1.0
            sample_accs = []
            for a, p in zip(acts, preds_val):
                if pd.isna(a):
                    sample_accs.append(np.nan)
                else:
                    acc = max(0.0, (1.0 - abs(float(a) - float(p)) / val_range)) * 100.0
                    sample_accs.append(round(acc, 1))
            summary_data[f"{short_n}_Accuracy%"] = sample_accs
            
            valid_accs = [acc for acc in sample_accs if not np.isnan(acc)]
            mean_val_acc = float(np.mean(valid_accs)) if valid_accs else 0.0
            matches_valid = [m for m in iso_matches if m in ('YES', 'NO')]
            mean_cls_acc = (matches_valid.count('YES') / len(matches_valid)) * 100.0 if matches_valid else 0.0
            
            rmse = float(np.sqrt(mean_squared_error(y_act, y_pred))) if len(y_act) > 0 else 0.0
            mae = float(mean_absolute_error(y_act, y_pred)) if len(y_act) > 0 else 0.0
            
            is_pass = mean_val_acc >= 75.0 and mean_cls_acc >= 75.0
            
            accuracy_summary.append({
                'Nutrient': target,
                'Short Name': short_n,
                'Samples Evaluated': len(y_act),
                'Class Accuracy (%)': round(mean_cls_acc, 2),
                'Value Accuracy (%)': round(mean_val_acc, 2),
                'RMSE': round(rmse, 4),
                'MAE': round(mae, 4),
                'Status (>= 75%?)': 'PASS' if is_pass else 'FAIL'
            })
            
    # Create Excel Writer
    df_results = pd.DataFrame(summary_data)
    df_acc_sum = pd.DataFrame(accuracy_summary)
    
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        if not df_acc_sum.empty:
            df_acc_sum.to_excel(writer, sheet_name='Performance_Summary', index=False, startrow=2)
        df_results.to_excel(writer, sheet_name='Actual_vs_Predicted_Details', index=False, startrow=2)
        
    # OpenPyXL formatting
    wb = openpyxl.load_workbook(output_excel)
    title_font = Font(name='Segoe UI', size=13, bold=True, color='FFFFFF')
    title_fill = PatternFill(start_color='0D233A', end_color='0D233A', fill_type='solid')
    header_font = Font(name='Segoe UI', size=11, bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='1F4E78', end_color='1F4E78', fill_type='solid')
    pass_fill = PatternFill(start_color='E2EFDA', end_color='E2EFDA', fill_type='solid')
    thin_border = Border(left=Side(style='thin', color='D9D9D9'), right=Side(style='thin', color='D9D9D9'),
                         top=Side(style='thin', color='D9D9D9'), bottom=Side(style='thin', color='D9D9D9'))
                         
    for s_name in wb.sheetnames:
        ws = wb[s_name]
        ncols = ws.max_column
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=ncols)
        tc = ws.cell(row=1, column=1)
        tc.value = f"MANUAL TEST PREDICTION REPORT: {s_name.replace('_', ' ').upper()}"
        tc.font = title_font
        tc.fill = title_fill
        tc.alignment = Alignment(horizontal='center', vertical='center')
        ws.row_dimensions[1].height = 28
        ws.row_dimensions[3].height = 24
        
        for c in range(1, ncols + 1):
            cell = ws.cell(row=3, column=c)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center', vertical='center')
            
        for r in range(4, ws.max_row + 1):
            for c in range(1, ncols + 1):
                cell = ws.cell(row=r, column=c)
                cell.border = thin_border
                cell.alignment = Alignment(horizontal='center', vertical='center')
                if cell.value == 'PASS':
                    cell.fill = pass_fill
                    
        for col in ws.columns:
            cl = get_column_letter(col[0].column)
            max_l = max(len(str(c.value or '')) for c in col)
            ws.column_dimensions[cl].width = max(max_l + 3, 12)
            
    wb.save(output_excel)
    print(f"\n--> Successfully saved evaluation report to: '{output_excel}'")
    
    if not df_acc_sum.empty:
        print("\n================================================================================")
        print("SUMMARY PERFORMANCE ON TEST SAMPLES:")
        print("================================================================================")
        print(df_acc_sum.to_string(index=False))
        print("================================================================================")

if __name__ == '__main__':
    print("=" * 80)
    print("SOIL SPECTRAL PREDICTION - MANUAL TESTING TOOL")
    print("=" * 80)
    
    # 1. Run batch test on data.xlsx
    evaluate_excel_file(input_excel='data.xlsx', output_excel='Manual_Test_Actual_vs_Predicted_Results.xlsx')
    
    # 2. Demo single sample test
    df_data = pd.read_excel('data.xlsx')
    sample_1_spec = df_data.loc[0, SPECTRAL_BANDS].values
    print("\n--> Testing Single Sample (Sample 1 reflectance spectrum):")
    sample_preds = predict_single_sample(sample_1_spec)
    for nut, res in sample_preds.items():
        print(f"  {nut:<12}: Class = {res['predicted_class']:<10} | Pred Value = {res['predicted_value']:8.2f} (Limits: {res['tier_limits']})")
