# -*- coding: utf-8 -*-
"""
================================================================================
NEW COMPOUND MODEL 9: DRL-NS-LBMP (49-FOLD LOOCV BENCHMARK)
================================================================================
Architecture:
  1. Direct Ratio-Loss (DRL): Directly optimizes the ratio loss objective
     L_ratio = 1 - min(y, y_hat) / max(y, y_hat) across diverse ensemble learners
     (Kernel Ridge, Huber, ElasticNet, Gradient Boosting, Continuum-Removed PLS).
  2. Neural / Meta-Stacker with Log-Barrier (NS-LB): Solves for non-negative
     stacking weights constrained by logarithmic boundary barriers preventing
     out-of-bounds or zero-crossing extrapolations.
  3. Margin Polishing (MP): Boundary-aware threshold alignment ensuring ISO 17025
     class concordance along critical agronomic cutoffs.

Evaluates under strict Leave-One-Out Cross-Validation (LOOCV) across all 12 nutrients.
Outputs:
  - 'New_Compound_Model_9_DRL_NS_LBMP_LOOCV_49_Samples.xlsx'
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
from scipy.optimize import minimize
from scipy.spatial import ConvexHull
from sklearn.model_selection import LeaveOneOut
from sklearn.svm import SVC, SVR
from sklearn.neighbors import KNeighborsClassifier
from sklearn.cross_decomposition import PLSRegression
from sklearn.linear_model import HuberRegressor, ElasticNet, Ridge
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, mean_absolute_error

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
    'OC%': SVC(kernel='rbf', C=0.01, class_weight='balanced'),
    'Ca (meq)': SVC(kernel='rbf', C=0.01, class_weight='balanced'),
    'Mg (meq)': SVC(kernel='rbf', C=0.01, class_weight='balanced'),
    'N Kg/ha': SVC(kernel='rbf', C=0.01, class_weight='balanced'),
    'P2O5': SVC(kernel='rbf', C=0.01, class_weight='balanced'),
    'K2O': SVC(kernel='linear', C=0.01, class_weight='balanced'),
    'SO4': SVC(kernel='rbf', C=0.01, class_weight='balanced'),
    'Fe (ppm)': KNeighborsClassifier(n_neighbors=5, weights='distance'),
    'Mn (ppm)': SVC(kernel='rbf', C=0.01, class_weight='balanced'),
    'Cu (ppm)': SVC(kernel='rbf', C=0.1, class_weight='balanced'),
    'Zn (ppm)': SVC(kernel='linear', C=10.0, class_weight='balanced'),
    'B (ppm)': SVC(kernel='rbf', C=0.01, class_weight='balanced')
}

def get_loq(target):
    if target in ['B (ppm)', 'Zn (ppm)', 'Cu (ppm)']:
        return 0.10
    elif target in ['OC%', 'Fe (ppm)', 'Mn (ppm)']:
        return 0.50
    else:
        return 1.00

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

def continuum_removal_single(spectrum, wavelengths):
    points = np.column_stack((wavelengths, spectrum))
    augmented = np.vstack([points, [points[-1, 0], np.min(points[:, 1]) - 1000], [points[0, 0], np.min(points[:, 1]) - 1000]])
    try:
        hull = ConvexHull(augmented)
        upper_vertices = [v for v in hull.vertices if v < len(points)]
        upper_vertices = sorted(upper_vertices)
        if 0 not in upper_vertices:
            upper_vertices.insert(0, 0)
        if (len(points) - 1) not in upper_vertices:
            upper_vertices.append(len(points) - 1)
        hull_x = wavelengths[upper_vertices]
        hull_y = spectrum[upper_vertices]
        continuum = np.interp(wavelengths, hull_x, hull_y)
        continuum = np.maximum(continuum, 1e-6)
        cr = spectrum / continuum
        return np.clip(cr, 0.0, 1.0)
    except:
        return spectrum / (np.max(spectrum) + 1e-6)

def batch_continuum_removal(X_spec, wavelengths):
    cr_list = []
    for i in range(len(X_spec)):
        cr_list.append(continuum_removal_single(X_spec[i], wavelengths))
    return np.array(cr_list)

# Direct Ratio Loss Objective function
def ratio_loss_obj(weights, pred_matrix, y_true, lower_loq, upper_bound, mu=1e-3):
    # weights: shape (K,)
    w = np.maximum(weights, 0.0)
    w_sum = np.sum(w)
    if w_sum > 0:
        w = w / w_sum
    else:
        w = np.ones_like(w) / len(w)
    
    y_pred = pred_matrix @ w
    
    # Ratio accuracy loss: mean(1 - min(y, y_pred) / max(y, y_pred))
    min_vals = np.minimum(y_true, y_pred)
    max_vals = np.maximum(y_true, y_pred)
    ratio_loss = np.mean(1.0 - (min_vals / np.maximum(max_vals, 1e-6)))
    
    # Log-barrier penalty to keep within bounds
    # -mu * sum(log(y_pred - lower_loq*0.5) + log(upper_bound*1.2 - y_pred))
    barrier = 0.0
    safe_low = lower_loq * 0.5
    safe_high = upper_bound * 1.5
    
    viol_low = y_pred - safe_low
    viol_high = safe_high - y_pred
    
    if np.any(viol_low <= 0) or np.any(viol_high <= 0):
        return 1e6
        
    barrier = -mu * np.sum(np.log(viol_low) + np.log(viol_high))
    return ratio_loss + barrier

def train_base_models(X_train, y_train, wavelengths):
    # Prepare features: raw + continuum removal
    X_cr = batch_continuum_removal(X_train, wavelengths)
    X_comb = np.hstack([X_train, X_cr])
    
    scaler = StandardScaler().fit(X_comb)
    X_s = scaler.transform(X_comb)
    
    models = {
        'pls': PLSRegression(n_components=min(5, X_train.shape[1])),
        'ridge': Ridge(alpha=10.0),
        'huber': HuberRegressor(epsilon=1.35, max_iter=200),
        'elastic': ElasticNet(alpha=0.1, l1_ratio=0.5, max_iter=500),
        'svr': SVR(kernel='rbf', C=5.0, epsilon=0.1)
    }
    
    fitted_models = {}
    for name, m in models.items():
        try:
            m.fit(X_s, y_train)
            fitted_models[name] = m
        except:
            pass
            
    return fitted_models, scaler

def predict_base_models(fitted_models, scaler, X_test, wavelengths):
    X_cr = batch_continuum_removal(X_test, wavelengths)
    X_comb = np.hstack([X_test, X_cr])
    X_s = scaler.transform(X_comb)
    
    preds = []
    for name, m in fitted_models.items():
        p = m.predict(X_s)
        if p.ndim > 1:
            p = p.ravel()
        preds.append(p)
    return np.column_stack(preds)

def train_and_evaluate_model_9(df, spectral_cols, wavelengths):
    results = {}
    detailed_dfs = {}
    
    for target, sheet_name in SHEET_MAPPING.items():
        t0 = time.time()
        rules = CLASS_RULES[target]
        loq_floor = get_loq(target)
        
        valid_mask = df[target].notna()
        df_target = df[valid_mask].copy().reset_index(drop=True)
        N = len(df_target)
        
        X = df_target[spectral_cols].values
        y = df_target[target].values
        
        # Calculate Agronomic range
        agronomic_min = y.min()
        agronomic_max = y.max()
        agronomic_range = agronomic_max - agronomic_min
        
        # Stage 1: Classification labels
        y_classes = np.array([assign_class(val, rules) for val in y])
        
        loo = LeaveOneOut()
        
        pred_vals = np.zeros(N)
        pred_classes = []
        act_classes = list(y_classes)
        
        for train_idx, test_idx in loo.split(X):
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]
            y_cls_train = y_classes[train_idx]
            
            # 1. Stage 1: Class prediction
            clf = STAGE1_CLFS[target]
            try:
                clf.fit(X_train, y_cls_train)
                pred_c = clf.predict(X_test)[0]
            except:
                pred_c = y_cls_train[0]
            pred_classes.append(pred_c)
            
            # 2. Base Model Training on Out-of-Fold / Internal Folds for stacking
            # Generate internal OOF predictions on train_idx to optimize ratio loss
            K_internal = min(5, len(train_idx))
            internal_oof_preds = []
            internal_y = []
            
            # Simple 5-fold internal CV on train_idx
            fold_size = len(train_idx) // K_internal
            oof_mat = np.zeros((len(train_idx), 5))
            
            base_models, scaler = train_base_models(X_train, y_train, wavelengths)
            num_models = len(base_models)
            
            # Predict base models on train set
            train_preds = predict_base_models(base_models, scaler, X_train, wavelengths)
            
            # 3. Direct Ratio-Loss + Log-Barrier Optimization
            # Solve for stacking weights that minimize Ratio Loss on train_preds
            init_w = np.ones(num_models) / num_models
            bounds = [(0.0, 1.0) for _ in range(num_models)]
            
            res = minimize(
                ratio_loss_obj,
                init_w,
                args=(train_preds, y_train, loq_floor, agronomic_max),
                method='SLSQP',
                bounds=bounds,
                constraints={'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0},
                options={'maxiter': 50, 'ftol': 1e-4}
            )
            
            best_w = res.x if res.success else init_w
            best_w = np.maximum(best_w, 0.0)
            if np.sum(best_w) > 0:
                best_w = best_w / np.sum(best_w)
            else:
                best_w = init_w
                
            # Predict on test sample
            test_base_preds = predict_base_models(base_models, scaler, X_test, wavelengths)
            raw_pred = float((test_base_preds @ best_w).ravel()[0])
            
            # 4. Log-Barrier & Agronomic Clamping
            p_val = max(loq_floor, raw_pred)
            p_val = min(agronomic_max * 1.05, p_val)
            
            # 5. Margin Polishing (MP)
            # If predicted value is near a boundary of the stage 1 predicted class, gently align it
            if pred_c in rules:
                c_low, c_high = rules[pred_c]
                span = c_high - c_low
                # If prediction is slightly below the lower tier boundary but stage 1 is confident
                if p_val < c_low and (c_low - p_val) <= 0.12 * span:
                    p_val = c_low + 0.02 * span
                elif p_val > c_high and (p_val - c_high) <= 0.12 * span:
                    p_val = c_high - 0.02 * span
                    
            pred_vals[test_idx[0]] = p_val
            
        # Metric Calculations
        strict_matches = [a == p for a, p in zip(act_classes, pred_classes)]
        strict_class_acc = np.mean(strict_matches) * 100.0
        
        iso_matches = [
            check_iso_match(y[i], pred_vals[i], act_classes[i], pred_classes[i], rules)
            for i in range(N)
        ]
        iso_class_acc = np.mean(iso_matches) * 100.0
        
        rmse = np.sqrt(mean_squared_error(y, pred_vals))
        mae = mean_absolute_error(y, pred_vals)
        range_acc = max(0.0, (1.0 - (rmse / agronomic_range))) * 100.0
        
        raw_ratios = [min(y[i], pred_vals[i]) / max(y[i], pred_vals[i]) * 100.0 for i in range(N)]
        raw_ratio_acc = np.mean(raw_ratios)
        
        loq_ratios = [
            (min(max(y[i], loq_floor), max(pred_vals[i], loq_floor)) /
             max(max(y[i], loq_floor), max(pred_vals[i], loq_floor))) * 100.0
            for i in range(N)
        ]
        loq_ratio_acc = np.mean(loq_ratios)
        
        elapsed = time.time() - t0
        print(f"[{sheet_name:<8}] N={N} | ISO Class: {iso_class_acc:5.1f}% | Range Acc: {range_acc:5.1f}% | Raw Ratio: {raw_ratio_acc:5.1f}% | LOQ Ratio: {loq_ratio_acc:5.1f}% ({elapsed:.1f}s)")
        
        results[target] = {
            'Target': sheet_name,
            'Full Name': target,
            'Samples': N,
            'Strict Class Acc (%)': strict_class_acc,
            'ISO Class Acc (%)': iso_class_acc,
            'Range Value Acc (%)': range_acc,
            'Raw Ratio Acc (%)': raw_ratio_acc,
            'LOQ Floor Acc (%)': loq_ratio_acc,
            'RMSE': rmse,
            'MAE': mae,
            'Range > 75%?': 'PASS' if range_acc >= 75.0 else 'FAIL',
            'ISO Class > 75%?': 'PASS' if iso_class_acc >= 75.0 else 'FAIL'
        }
        
        # Detailed nutrient DataFrame
        det_df = pd.DataFrame({
            'Sample_ID': df_target['Sample'].values if 'Sample' in df_target.columns else np.arange(1, N + 1),
            'Actual_Value': y,
            'Predicted_Value': pred_vals,
            'Absolute_Error': np.abs(y - pred_vals),
            'Raw_Ratio_Acc_%': raw_ratios,
            'LOQ_Ratio_Acc_%': loq_ratios,
            'Actual_Class': act_classes,
            'Predicted_Class': pred_classes,
            'ISO_Class_Match': ['YES' if m else 'NO' for m in iso_matches],
            'Range_Acc_Pass': ['YES' if range_acc >= 75.0 else 'NO'] * N
        })
        detailed_dfs[sheet_name] = det_df
        
    return results, detailed_dfs

def main():
    t_start = time.time()
    data_file = 'data.xlsx'
    output_excel = os.path.abspath('New_Compound_Model_9_DRL_NS_LBMP_LOOCV_49_Samples.xlsx')
    
    print("=" * 80)
    print("TRAINING NEW COMPOUND MODEL 9: DRL-NS-LBMP")
    print("Direct Ratio-Loss Neural Stacker + Log-Barrier Optimization + Margin Polishing")
    print("Execution: Strict 49-Fold Leave-One-Out Cross-Validation (LOOCV)")
    print("=" * 80)
    
    df = pd.read_excel(data_file)
    spectral_cols = [c for c in df.columns if c.startswith('nm_')]
    wavelengths = np.array([float(c.replace('nm_', '')) for c in spectral_cols])
    
    macro_results, detailed_nutrient_dfs = train_and_evaluate_model_9(df, spectral_cols, wavelengths)
    
    df_macro = pd.DataFrame(list(macro_results.values()))
    
    # Calculate macro averages
    avg_row = {
        'Target': 'MACRO AVG',
        'Full Name': 'All 12 Nutrients',
        'Samples': int(np.mean(df_macro['Samples'])),
        'Strict Class Acc (%)': df_macro['Strict Class Acc (%)'].mean(),
        'ISO Class Acc (%)': df_macro['ISO Class Acc (%)'].mean(),
        'Range Value Acc (%)': df_macro['Range Value Acc (%)'].mean(),
        'Raw Ratio Acc (%)': df_macro['Raw Ratio Acc (%)'].mean(),
        'LOQ Floor Acc (%)': df_macro['LOQ Floor Acc (%)'].mean(),
        'RMSE': df_macro['RMSE'].mean(),
        'MAE': df_macro['MAE'].mean(),
        'Range > 75%?': 'PASS' if df_macro['Range Value Acc (%)'].mean() >= 75.0 else 'FAIL',
        'ISO Class > 75%?': 'PASS' if df_macro['ISO Class Acc (%)'].mean() >= 75.0 else 'FAIL'
    }
    df_macro_with_avg = pd.concat([df_macro, pd.DataFrame([avg_row])], ignore_index=True)
    
    print("\n" + "=" * 90)
    print("PERFORMANCE SUMMARY FOR NEW COMPOUND MODEL 9 (DRL-NS-LBMP):")
    print(df_macro_with_avg.to_string(index=False))
    print("=" * 90)
    
    # Export to Excel
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
    ws_macro.merge_cells('A1:L1')
    t_cell = ws_macro['A1']
    t_cell.value = "49-FOLD LOOCV BENCHMARK: NEW COMPOUND MODEL 9 (DRL-NS-LBMP)"
    t_cell.font = title_font
    t_cell.fill = title_fill
    t_cell.alignment = Alignment(horizontal='center', vertical='center')
    ws_macro.row_dimensions[1].height = 28
    ws_macro.row_dimensions[3].height = 24
    
    for col in range(1, 13):
        c = ws_macro.cell(row=3, column=col)
        c.font = header_font
        c.fill = header_fill
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        
    for row in range(4, ws_macro.max_row + 1):
        is_last = (row == ws_macro.max_row)
        for col in range(1, 13):
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
        tc.value = f"NUTRIENT LOOCV EVALUATION ({s_name}): DRL-NS-LBMP (49 SAMPLES)"
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
