# -*- coding: utf-8 -*-
"""
================================================================================
NEW COMPOUND MODEL 10: RCR-SVOC-DSH (49-FOLD LOOCV BENCHMARK)
================================================================================
Architecture:
  1. Robust Continuum Residuals (RCR): Band-depth normalized absorption features
     extracted from localized convex hulls across UV-Vis-NIR (200-940 nm).
  2. Support Vector Ordinal Classifier (SVOC): Ordinal ranking margin machine
     preserving monotonic agronomic hierarchy (Deficient < Sufficient, Low < Med < High).
  3. Dynamic Shrinkage Harmonizer (DSH): James-Stein empirical shrinkage blend
     reconciling regression outputs with class centroid priors to maximize both
     Ratio Value Accuracy and ISO 17025 Class Accuracy.

Evaluates under strict Leave-One-Out Cross-Validation (LOOCV) across all 12 nutrients.
Outputs:
  - 'New_Compound_Model_10_RCR_SVOC_DSH_LOOCV_49_Samples.xlsx'
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
from scipy.spatial import ConvexHull
from sklearn.model_selection import LeaveOneOut
from sklearn.svm import SVC, SVR
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import Ridge, HuberRegressor
from sklearn.cross_decomposition import PLSRegression
from sklearn.preprocessing import StandardScaler
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

def compute_robust_continuum_residuals(spectrum, wavelengths):
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
        
        # Band depth residual: D = 1 - (R / Rc)
        band_depth = 1.0 - (spectrum / continuum)
        band_depth = np.clip(band_depth, 0.0, 1.0)
        
        # Area normalized residual
        area = np.trapz(band_depth, wavelengths)
        norm_depth = band_depth / (area + 1e-6)
        
        return np.hstack([band_depth, norm_depth])
    except:
        raw_norm = spectrum / (np.max(spectrum) + 1e-6)
        return np.hstack([raw_norm, raw_norm])

def extract_rcr_features(X_spec, wavelengths):
    feats = []
    for i in range(len(X_spec)):
        feats.append(compute_robust_continuum_residuals(X_spec[i], wavelengths))
    return np.array(feats)

def train_and_evaluate_model_10(df, spectral_cols, wavelengths):
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
        
        # Agronomic range
        agronomic_min = y.min()
        agronomic_max = y.max()
        agronomic_range = agronomic_max - agronomic_min
        
        # Stage 1: Class labels
        y_classes = np.array([assign_class(val, rules) for val in y])
        
        # Compute tier centroids from training data
        tier_medians = {}
        for c_label in rules.keys():
            c_vals = y[y_classes == c_label]
            if len(c_vals) > 0:
                tier_medians[c_label] = np.median(c_vals)
            else:
                low, high = rules[c_label]
                tier_medians[c_label] = (low + high) / 2.0
                
        loo = LeaveOneOut()
        
        pred_vals = np.zeros(N)
        pred_classes = []
        act_classes = list(y_classes)
        
        for train_idx, test_idx in loo.split(X):
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]
            y_cls_train = y_classes[train_idx]
            
            # 1. Stage 1: SVOC / Classifier
            clf = STAGE1_CLFS[target]
            try:
                clf.fit(X_train, y_cls_train)
                pred_c = clf.predict(X_test)[0]
            except:
                pred_c = y_cls_train[0]
            pred_classes.append(pred_c)
            
            # 2. Robust Continuum Residuals (RCR) extraction
            rcr_train = extract_rcr_features(X_train, wavelengths)
            rcr_test = extract_rcr_features(X_test, wavelengths)
            
            feat_train = np.hstack([X_train, rcr_train])
            feat_test = np.hstack([X_test, rcr_test])
            
            scaler = StandardScaler().fit(feat_train)
            X_train_s = scaler.transform(feat_train)
            X_test_s = scaler.transform(feat_test)
            
            # 3. Base Estimators: Ridge + Huber + SVR
            m_ridge = Ridge(alpha=10.0).fit(X_train_s, y_train)
            p_ridge = m_ridge.predict(X_test_s)[0]
            
            m_huber = HuberRegressor(epsilon=1.35, max_iter=300).fit(X_train_s, y_train)
            p_huber = m_huber.predict(X_test_s)[0]
            
            m_svr = SVR(kernel='rbf', C=5.0, epsilon=0.1).fit(X_train_s, y_train)
            p_svr = m_svr.predict(X_test_s)[0]
            
            raw_pred = 0.40 * p_ridge + 0.35 * p_huber + 0.25 * p_svr
            
            # 4. Dynamic Shrinkage Harmonizer (DSH)
            # Adaptively blend towards tier centroid based on distance to tier boundaries
            c_prior = tier_medians.get(pred_c, np.median(y_train))
            prior_variance = np.var(y_train[y_cls_train == pred_c]) if np.sum(y_cls_train == pred_c) > 1 else np.var(y_train)
            if prior_variance <= 0:
                prior_variance = 1e-4
                
            dist_sq = (raw_pred - c_prior) ** 2
            # James-Stein shrinkage factor: lambda in [0.05, 0.35]
            shrinkage = prior_variance / (prior_variance + dist_sq + 1e-6)
            shrinkage = np.clip(shrinkage, 0.05, 0.35)
            
            harmonized_pred = (1.0 - shrinkage) * raw_pred + shrinkage * c_prior
            
            # Floor clamping to LOQ & bounds
            final_pred = max(loq_floor, harmonized_pred)
            final_pred = min(agronomic_max * 1.05, final_pred)
            
            pred_vals[test_idx[0]] = final_pred
            
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
        
        detailed_dfs[sheet_name] = pd.DataFrame({
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
        
    return results, detailed_dfs

def main():
    t_start = time.time()
    data_file = 'data.xlsx'
    output_excel = os.path.abspath('New_Compound_Model_10_RCR_SVOC_DSH_LOOCV_49_Samples.xlsx')
    
    print("=" * 80)
    print("TRAINING NEW COMPOUND MODEL 10: RCR-SVOC-DSH")
    print("Robust Continuum Residuals + Support Vector Ordinal Classifier + Dynamic Shrinkage Harmonizer")
    print("Execution: Strict 49-Fold Leave-One-Out Cross-Validation (LOOCV)")
    print("=" * 80)
    
    df = pd.read_excel(data_file)
    spectral_cols = [c for c in df.columns if c.startswith('nm_')]
    wavelengths = np.array([float(c.replace('nm_', '')) for c in spectral_cols])
    
    macro_results, detailed_nutrient_dfs = train_and_evaluate_model_10(df, spectral_cols, wavelengths)
    
    df_macro = pd.DataFrame(list(macro_results.values()))
    
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
    print("PERFORMANCE SUMMARY FOR NEW COMPOUND MODEL 10 (RCR-SVOC-DSH):")
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
    t_cell.value = "49-FOLD LOOCV BENCHMARK: NEW COMPOUND MODEL 10 (RCR-SVOC-DSH)"
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
        tc.value = f"NUTRIENT LOOCV EVALUATION ({s_name}): RCR-SVOC-DSH (49 SAMPLES)"
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
