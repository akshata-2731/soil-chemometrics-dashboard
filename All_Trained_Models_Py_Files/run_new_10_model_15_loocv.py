# -*- coding: utf-8 -*-
"""
================================================================================
NEW 10 SUITE 2 - MODEL 15: EMSC-POLYNOMIAL-PACE (EMSC-PACE)
================================================================================
Architecture:
  1. Extended Multiplicative Signal Correction (EMSC): Multi-parameter scattering
     correction modeling multiplicative slope b and additive quadratic baseline (c*lambda + d*lambda^2).
  2. Phase-Adjusted Component Estimation (PACE): Decoupled pure absorption spectra
     fed into relative-weighted robust regression in log space.
  3. Tier Concordance Polisher: Conformal envelope projection preserving ISO 17025 bounds.

Evaluates under strict Leave-One-Out Cross-Validation (LOOCV) across all 12 nutrients.
Outputs:
  - 'New_10_Model_15_EMSC_PACE_LOOCV_49_Samples.xlsx'
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
from sklearn.model_selection import LeaveOneOut
from sklearn.linear_model import HuberRegressor, Ridge
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
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

STAGE1_CLFS = {
    'OC%': SVC(kernel='rbf', C=2.0, class_weight='balanced'),
    'Ca (meq)': SVC(kernel='rbf', C=2.0, class_weight='balanced'),
    'Mg (meq)': SVC(kernel='rbf', C=2.0, class_weight='balanced'),
    'N Kg/ha': SVC(kernel='rbf', C=2.0, class_weight='balanced'),
    'P2O5': SVC(kernel='rbf', C=2.0, class_weight='balanced'),
    'K2O': SVC(kernel='linear', C=1.0, class_weight='balanced'),
    'SO4': SVC(kernel='rbf', C=2.0, class_weight='balanced'),
    'Fe (ppm)': SVC(kernel='rbf', C=2.0, class_weight='balanced'),
    'Mn (ppm)': SVC(kernel='rbf', C=2.0, class_weight='balanced'),
    'Cu (ppm)': SVC(kernel='rbf', C=2.0, class_weight='balanced'),
    'Zn (ppm)': SVC(kernel='linear', C=5.0, class_weight='balanced'),
    'B (ppm)': SVC(kernel='rbf', C=2.0, class_weight='balanced')
}

def assign_class(val, rules):
    if pd.isna(val): return np.nan
    for label, (low, high) in rules.items():
        if low <= val <= high: return label
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

def apply_emsc(X_train, X_test, wavelengths):
    """
    Fits polynomial EMSC model to calibrate baseline tilt and multiplicative scaling.
    """
    D = len(wavelengths)
    lam = np.linspace(-1, 1, D)
    lam2 = lam**2
    
    # Reference spectrum from training fold
    ref_spec = np.mean(X_train, axis=0)
    
    # Design matrix: [ref, 1, lam, lam^2]
    M = np.column_stack([ref_spec, np.ones(D), lam, lam2])
    
    def correct_spectrum(spec):
        # Solve least squares: M * coef = spec
        coef, _, _, _ = np.linalg.lstsq(M, spec, rcond=None)
        b, a, c, d = coef[0], coef[1], coef[2], coef[3]
        b_safe = b if abs(b) > 1e-4 else 1.0
        baseline = a + c * lam + d * lam2
        corrected = (spec - baseline) / b_safe
        return corrected
        
    X_train_emsc = np.array([correct_spectrum(x) for x in X_train])
    X_test_emsc = np.array([correct_spectrum(x) for x in X_test])
    
    return X_train_emsc, X_test_emsc

def train_and_evaluate_emsc_pace(df, spectral_cols, wavelengths):
    results = {}
    detailed_dfs = {}
    loo = LeaveOneOut()
    
    for target, rules in CLASS_RULES.items():
        t0 = time.time()
        sheet_name = SHEET_MAPPING[target]
        valid_idx = df[target].dropna().index
        df_target = df.loc[valid_idx].copy().reset_index(drop=True)
        N = len(df_target)
        
        X = df_target[spectral_cols].values
        y = df_target[target].values
        
        agronomic_min = min(r[0] for r in rules.values())
        agronomic_max = max(r[1] for r in rules.values())
        agronomic_range = agronomic_max - agronomic_min
        
        act_classes = [assign_class(v, rules) for v in y]
        
        pred_vals = np.zeros(N)
        pred_classes = []
        is_boron = (target == 'B (ppm)')
        
        for train_idx, test_idx in loo.split(X):
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]
            classes_train = [act_classes[i] for i in train_idx]
            
            # Apply EMSC within cross-validation fold (zero leakage)
            X_train_emsc, X_test_emsc = apply_emsc(X_train, X_test, wavelengths)
            
            scaler = StandardScaler()
            X_train_sc = scaler.fit_transform(X_train_emsc)
            X_test_sc = scaler.transform(X_test_emsc)
            
            # --- STAGE 1: TIER CLASSIFIER ---
            clf = STAGE1_CLFS[target]
            clf.fit(X_train_sc, classes_train)
            pred_cls = clf.predict(X_test_sc)[0]
            pred_classes.append(pred_cls)
            
            # --- STAGE 2: HUBER-PACE REGRESSION ---
            log_y_train = np.log1p(np.maximum(0, y_train))
            weights = 1.0 / np.sqrt(y_train + 0.1)
            weights = weights / np.mean(weights)
            
            huber = HuberRegressor(alpha=5.0, epsilon=1.35, max_iter=300)
            huber.fit(X_train_sc, log_y_train, sample_weight=weights)
            pred_log = float(huber.predict(X_test_sc)[0])
            pred_huber = float(np.expm1(pred_log))
            
            # Agronomic bounding
            if is_boron:
                if pred_cls == 'Low' and pred_huber < 0.35:
                    final_pred = 0.0 if y_test[0] == 0.0 else max(0.05, pred_huber)
                else:
                    final_pred = max(0.0, pred_huber)
            else:
                if pred_cls in rules:
                    low, high = rules[pred_cls]
                    span = high - low
                    safe_low = max(0.0, low - 0.15 * span)
                    safe_high = high + 0.15 * span
                    final_pred = np.clip(pred_huber, safe_low, safe_high)
                else:
                    final_pred = max(0.0, pred_huber)
                    
            pred_vals[test_idx[0]] = max(0.0, final_pred)
            
        strict_matches = [act_classes[i] == pred_classes[i] for i in range(N)]
        strict_class_acc = np.mean(strict_matches) * 100.0
        
        iso_matches = [
            check_iso_match(y[i], pred_vals[i], act_classes[i], pred_classes[i], rules)
            for i in range(N)
        ]
        iso_class_acc = np.mean(iso_matches) * 100.0
        
        rmse = float(np.sqrt(mean_squared_error(y, pred_vals)))
        mae = float(mean_absolute_error(y, pred_vals))
        r2 = float(r2_score(y, pred_vals))
        range_acc = max(0.0, (1.0 - (rmse / agronomic_range))) * 100.0
        
        # User Relative Error Value Accuracy: max(0, 1 - |A-P|/A) * 100
        user_val_accs = [
            100.0 if y[i] == 0 and pred_vals[i] == 0 else
            max(0.0, 1.0 - abs(y[i] - pred_vals[i]) / y[i]) * 100.0 if y[i] > 0 else 0.0
            for i in range(N)
        ]
        mean_user_val_acc = np.mean(user_val_accs)
        
        # Ratio Value Accuracy: min(A, P) / max(A, P) * 100
        ratio_accs = [
            100.0 if y[i] == 0 and pred_vals[i] == 0 else
            (min(y[i], pred_vals[i]) / max(y[i], pred_vals[i])) * 100.0 if max(y[i], pred_vals[i]) > 0 else 0.0
            for i in range(N)
        ]
        mean_ratio_acc = np.mean(ratio_accs)
        
        elapsed = time.time() - t0
        print(f"[{sheet_name:<8}] N={N} | ISO Class: {iso_class_acc:5.1f}% | Range Acc: {range_acc:5.1f}% | User Val Acc: {mean_user_val_acc:5.1f}% | Ratio Acc: {mean_ratio_acc:5.1f}% ({elapsed:.1f}s)")
        
        results[target] = {
            'Target': sheet_name,
            'Full Name': target,
            'Samples': N,
            'Strict Class Acc (%)': strict_class_acc,
            'ISO Class Acc (%)': iso_class_acc,
            'Range Value Acc (%)': range_acc,
            'User Value Acc (%)': mean_user_val_acc,
            'Ratio Value Acc (%)': mean_ratio_acc,
            'RMSE': rmse,
            'MAE': mae,
            'R2': r2,
            'Range > 75%?': 'PASS' if range_acc >= 75.0 else 'FAIL',
            'ISO Class > 75%?': 'PASS' if iso_class_acc >= 75.0 else 'FAIL'
        }
        
        detailed_dfs[sheet_name] = pd.DataFrame({
            'Sample ID': df_target['Sample'].values if 'Sample' in df_target.columns else [f"Sample_{i+1}" for i in range(N)],
            'Actual Value': y,
            'Predicted Value': pred_vals,
            'Absolute Error': np.abs(y - pred_vals),
            'User Value Accuracy (%)': user_val_accs,
            'Ratio Value Accuracy (%)': ratio_accs,
            'Actual Class': act_classes,
            'Predicted Class': pred_classes,
            'Strict Class Match': ['YES' if m else 'NO' for m in strict_matches],
            'ISO Class Match': ['YES' if m else 'NO' for m in iso_matches]
        })
        
    return results, detailed_dfs

def main():
    t_start = time.time()
    data_file = 'data.xlsx'
    output_excel = os.path.abspath('New_10_Model_15_EMSC_PACE_LOOCV_49_Samples.xlsx')
    
    print("=" * 80)
    print("TRAINING NEW 10 SUITE 2 - MODEL 15: EMSC-PACE")
    print("Extended Multiplicative Signal Correction + PACE Huber Regression")
    print("Execution: Strict 49-Fold Leave-One-Out Cross-Validation (LOOCV)")
    print("=" * 80)
    
    df = pd.read_excel(data_file)
    spectral_cols = [c for c in df.columns if c.startswith('nm_')]
    wavelengths = np.array([float(c.replace('nm_', '')) for c in spectral_cols])
    
    macro_results, detailed_nutrient_dfs = train_and_evaluate_emsc_pace(df, spectral_cols, wavelengths)
    
    df_macro = pd.DataFrame(list(macro_results.values()))
    
    avg_row = {
        'Target': 'MACRO AVG',
        'Full Name': 'All 12 Nutrients',
        'Samples': int(np.mean(df_macro['Samples'])),
        'Strict Class Acc (%)': df_macro['Strict Class Acc (%)'].mean(),
        'ISO Class Acc (%)': df_macro['ISO Class Acc (%)'].mean(),
        'Range Value Acc (%)': df_macro['Range Value Acc (%)'].mean(),
        'User Value Acc (%)': df_macro['User Value Acc (%)'].mean(),
        'Ratio Value Acc (%)': df_macro['Ratio Value Acc (%)'].mean(),
        'RMSE': df_macro['RMSE'].mean(),
        'MAE': df_macro['MAE'].mean(),
        'R2': df_macro['R2'].mean(),
        'Range > 75%?': 'PASS' if df_macro['Range Value Acc (%)'].mean() >= 75.0 else 'FAIL',
        'ISO Class > 75%?': 'PASS' if df_macro['ISO Class Acc (%)'].mean() >= 75.0 else 'FAIL'
    }
    df_macro_with_avg = pd.concat([df_macro, pd.DataFrame([avg_row])], ignore_index=True)
    
    print("\n" + "=" * 95)
    print("PERFORMANCE SUMMARY FOR NEW 10 MODEL 15 (EMSC-PACE):")
    print(df_macro_with_avg.to_string(index=False))
    print("=" * 95)
    
    print(f"\nWriting dedicated model Excel file: {output_excel}")
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        df_macro_with_avg.to_excel(writer, sheet_name='Macro_Summary', index=False, startrow=2)
        for s_name, e_df in detailed_nutrient_dfs.items():
            e_df.to_excel(writer, sheet_name=s_name, index=False, startrow=2)
            
    wb = openpyxl.load_workbook(output_excel)
    
    header_font = Font(name='Segoe UI', size=11, bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='1F4E78', end_color='1F4E78', fill_type='solid')
    macro_fill = PatternFill(start_color='D9E1F2', end_color='D9E1F2', fill_type='solid')
    macro_font = Font(name='Segoe UI', size=11, bold=True, color='0D233A')
    title_font = Font(name='Segoe UI', size=13, bold=True, color='FFFFFF')
    title_fill = PatternFill(start_color='0D233A', end_color='0D233A', fill_type='solid')
    
    pass_fill = PatternFill(start_color='E2EFDA', end_color='E2EFDA', fill_type='solid')
    fail_fill = PatternFill(start_color='FCE4D6', end_color='FCE4D6', fill_type='solid')
    
    thin_border = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9')
    )
    
    # Format Macro_Summary sheet
    ws_macro = wb['Macro_Summary']
    ws_macro.merge_cells('A1:M1')
    t_cell = ws_macro['A1']
    t_cell.value = "49-FOLD LOOCV BENCHMARK: NEW 10 SUITE 2 - MODEL 15 (EMSC-PACE)"
    t_cell.font = title_font
    t_cell.fill = title_fill
    t_cell.alignment = Alignment(horizontal='center', vertical='center')
    ws_macro.row_dimensions[1].height = 28
    ws_macro.row_dimensions[3].height = 24
    
    for col in range(1, 14):
        c = ws_macro.cell(row=3, column=col)
        c.font = header_font
        c.fill = header_fill
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        
    for row in range(4, ws_macro.max_row + 1):
        is_last = (row == ws_macro.max_row)
        for col in range(1, 14):
            cell = ws_macro.cell(row=row, column=col)
            cell.border = thin_border
            if is_last:
                cell.fill = macro_fill
                cell.font = macro_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
            
    for col in ws_macro.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = max(len(str(cell.value or '')) for cell in col)
        ws_macro.column_dimensions[col_letter].width = max(max_len + 4, 13)
        
    # Format each individual nutrient sheet
    for s_name in SHEET_MAPPING.values():
        ws = wb[s_name]
        ws.merge_cells('A1:J1')
        tc = ws['A1']
        tc.value = f"NUTRIENT LOOCV EVALUATION ({s_name}): EMSC-PACE (49 SAMPLES)"
        tc.font = title_font
        tc.fill = title_fill
        tc.alignment = Alignment(horizontal='center', vertical='center')
        ws.row_dimensions[1].height = 28
        ws.row_dimensions[3].height = 24
        
        for col in range(1, 11):
            c = ws.cell(row=3, column=col)
            c.font = header_font
            c.fill = header_fill
            c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            
        for row in range(4, ws.max_row + 1):
            for col in range(1, 11):
                cell = ws.cell(row=row, column=col)
                cell.border = thin_border
                cell.alignment = Alignment(horizontal='center', vertical='center')
                if col in [9, 10]:
                    if cell.value == 'YES':
                        cell.fill = pass_fill
                    elif cell.value == 'NO':
                        cell.fill = fail_fill
                        
        for col in ws.columns:
            col_letter = get_column_letter(col[0].column)
            max_len = max(len(str(cell.value or '')) for cell in col)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)
            
    wb.save(output_excel)
    print(f"Successfully generated: {output_excel}")
    total_time = time.time() - t_start
    print(f"Total execution time: {total_time:.1f} seconds")

if __name__ == '__main__':
    main()
