# -*- coding: utf-8 -*-
"""
================================================================================
UPDATE ALL 12 NUTRIENTS TO UNIFIED 'LOW', 'MED', 'HIGH' CLASSIFICATION
Ensures every nutrient in:
  1. 'Master_30_Advanced_Combined_Models_LOOCV_Results.xlsx'
  2. 'Final_Saved_Models_30/' bundles
  3. 'test_manually_saved_models.py'
is classified strictly as 'Low', 'Med', or 'High'.
================================================================================
"""

import os
import pickle
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import pandas as pd
import numpy as np

CLASS_RULES_TERNARY = {
    'OC%': {'Low': (0.1, 0.5), 'Med': (0.5, 0.75), 'High': (0.75, 2.0)},
    'N Kg/ha': {'Low': (50, 280), 'Med': (280, 560), 'High': (560, 1000)},
    'P2O5': {'Low': (2, 22.9), 'Med': (22.9, 56.3), 'High': (56.3, 120)},
    'K2O': {'Low': (50, 144), 'Med': (144, 336), 'High': (336, 800)},
    'SO4': {'Low': (2, 10), 'Med': (10, 20), 'High': (20, 250)},
    'Fe (ppm)': {'Low': (1, 4.5), 'Med': (4.5, 10), 'High': (10, 50)},
    'Mn (ppm)': {'Low': (0.1, 2), 'Med': (2, 4), 'High': (4, 25)},
    'Cu (ppm)': {'Low': (0.1, 0.2), 'Med': (0.2, 0.4), 'High': (0.4, 10)},
    'Zn (ppm)': {'Low': (0.1, 0.6), 'Med': (0.6, 1.2), 'High': (1.2, 10)},
    'B (ppm)': {'Low': (0.1, 0.5), 'Med': (0.5, 1.0), 'High': (1.0, 10)},
    'Ca (meq)': {'Low': (1.0, 6.0), 'Med': (6.0, 15.0), 'High': (15.0, 100.0)},
    'Mg (meq)': {'Low': (0.0, 4.0), 'Med': (4.0, 10.0), 'High': (10.0, 50.0)}
}

NUTRIENT_ORDER = [
    ('OC%', 'OC'),
    ('N Kg/ha', 'N'),
    ('P2O5', 'P2O5'),
    ('K2O', 'K2O'),
    ('SO4', 'SO4'),
    ('Fe (ppm)', 'Fe'),
    ('Mn (ppm)', 'Mn'),
    ('Cu (ppm)', 'Cu'),
    ('Zn (ppm)', 'Zn'),
    ('B (ppm)', 'B'),
    ('Ca (meq)', 'Ca'),
    ('Mg (meq)', 'Mg')
]

def assign_ternary_class(val, rules):
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
    if act_cls == pred_cls: return True
    if act_cls not in rules: return False
    low, high = rules[act_cls]
    span = high - low
    exp_low = low - tol * span
    exp_high = high + tol * span
    return exp_low <= pred_val <= exp_high

excel_path = 'Master_30_Advanced_Combined_Models_LOOCV_Results.xlsx'
wb = openpyxl.load_workbook(excel_path)

# Update each individual LOOCV nutrient sheet
for target, short_n in NUTRIENT_ORDER:
    s_name = f"LOOCV_{short_n}"
    if s_name in wb.sheetnames:
        rules = CLASS_RULES_TERNARY[target]
        ws = wb[s_name]
        # Columns:
        # col 1: Sample ID, col 2: Actual Value, col 3: Pred Value, col 4: Abs Error, col 5: Value Acc %
        # col 6: Actual Class, col 7: Pred Class, col 8: ISO Class Match
        for r in range(4, ws.max_row + 1):
            act_val = ws.cell(row=r, column=2).value
            pred_val = ws.cell(row=r, column=3).value
            if act_val is not None and pred_val is not None:
                act_v = float(act_val)
                pred_v = float(pred_val)
                act_cls = assign_ternary_class(act_v, rules)
                pred_cls = assign_ternary_class(pred_v, rules)
                iso_match = check_iso_match(act_v, pred_v, act_cls, pred_cls, rules)
                
                ws.cell(row=r, column=6).value = act_cls
                ws.cell(row=r, column=7).value = pred_cls
                ws.cell(row=r, column=8).value = 'YES' if iso_match else 'NO'

# Update Actual_vs_Pred_Champion_LOOCV sheet
ws_avp = wb['Actual_vs_Pred_Champion_LOOCV']
# Headers at row 3
headers = [ws_avp.cell(row=3, column=c).value for c in range(1, ws_avp.max_column + 1)]
for target, short_n in NUTRIENT_ORDER:
    rules = CLASS_RULES_TERNARY[target]
    act_col_name = f"{short_n}_Actual"
    pred_col_name = f"{short_n}_LOOCV_Pred"
    match_col_name = f"{short_n}_Class_Match"
    
    if act_col_name in headers and pred_col_name in headers and match_col_name in headers:
        act_col_idx = headers.index(act_col_name) + 1
        pred_col_idx = headers.index(pred_col_name) + 1
        match_col_idx = headers.index(match_col_name) + 1
        
        for r in range(4, ws_avp.max_row + 1):
            act_val = ws_avp.cell(row=r, column=act_col_idx).value
            pred_val = ws_avp.cell(row=r, column=pred_col_idx).value
            if act_val is not None and pred_val is not None:
                act_v = float(act_val)
                pred_v = float(pred_val)
                act_cls = assign_ternary_class(act_v, rules)
                pred_cls = assign_ternary_class(pred_v, rules)
                iso_match = check_iso_match(act_v, pred_v, act_cls, pred_cls, rules)
                ws_avp.cell(row=r, column=match_col_idx).value = 'YES' if iso_match else 'NO'

wb.save(excel_path)
print(f"--> Updated '{excel_path}' with unified Low/Med/High classifications!")

# Update saved model bundles in 'Final_Saved_Models_30/'
models_dir = 'Final_Saved_Models_30'
for target, short_n in NUTRIENT_ORDER:
    clean_name = target.replace('/', '_').replace(' ', '_').replace('%', 'Pct').replace('(', '').replace(')', '')
    pkl_path = os.path.join(models_dir, f"Model30_{clean_name}.pkl")
    if os.path.exists(pkl_path):
        with open(pkl_path, 'rb') as f:
            bundle = pickle.load(f)
        bundle['rules'] = CLASS_RULES_TERNARY[target]
        with open(pkl_path, 'wb') as f:
            pickle.dump(bundle, f)
print(f"--> Updated model bundles in '{models_dir}/' with unified Low/Med/High rules!")

# Also run manual testing tool to create the manual testing excel report
import test_manually_saved_models
test_manually_saved_models.evaluate_excel_file(
    input_excel='data.xlsx',
    output_excel='Manual_Test_Actual_vs_Predicted_Results.xlsx'
)
print("--> Complete update and manual test export finished successfully!")
