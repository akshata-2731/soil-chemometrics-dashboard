# -*- coding: utf-8 -*-
"""
================================================================================
BUILD SELECTED 10 MODELS EXCEL REPORT FROM 27-MODEL BENCHMARK
Extracts the Top 10 Performing Models from 'Master_27_Models_Value_And_Class_Accuracy.xlsx'
and provides both ISO Class Accuracy and User Value Accuracy across all 12 nutrients.
================================================================================
"""

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import pandas as pd
import numpy as np

# Load source data
source_file = 'Master_27_Models_Value_And_Class_Accuracy.xlsx'
output_excel = 'Selected_10_Models_Class_And_Value_Accuracy.xlsx'

df_class_all = pd.read_excel(source_file, sheet_name='ISO_Class_Accuracy', skiprows=2)
df_value_all = pd.read_excel(source_file, sheet_name='User_Value_Accuracy', skiprows=2)
df_ratio_all = pd.read_excel(source_file, sheet_name='Ratio_Value_Accuracy', skiprows=2)
df_range_all = pd.read_excel(source_file, sheet_name='Range_Value_Accuracy', skiprows=2)
df_rank_all  = pd.read_excel(source_file, sheet_name='Overall_Performance_Rank', skiprows=2)

# Top 10 Models by Combined Score
top10_models = df_rank_all['Model'].iloc[:10].tolist()

# Descriptions for the 10 models
model_descriptions = {
    'Model 22: airPLS-BiPLS-Huber': 'Adaptive Baseline Correction + Interval PLS + Huber Estimator',
    'Model 15: EMSC-PACE': 'Extended Multiplicative Scatter Correction + PACE Regression',
    'Model 5: CR-BDI-Stacker': 'Continuum Removal Band-Depth Integrals + Non-Negative Stacker',
    'Model 11: UVE-VIP-HC': 'Uninformative Variable Elimination + VIP Filter + Huber Cascade',
    'Model 19: SpecGCN': 'Chebyshev Graph Convolutions + Spectral Adjacency Regressor',
    'Model 26: GA-NDSI-CatBoost': 'Pairwise Normalized Difference Spectral Indices + Hist Gradient Trees',
    'Model 1: CARS-SPA-QR': 'CARS Band Selection + Successive Projections + Quantile Ridge',
    'Model 27: SpecEnsemble-OptStack': 'Multi-Stream Preprocessing Consensus Stacking Engine',
    'Model 24: OSC-PLSR-EN': 'Orthogonal Signal Correction + Latent PLS Scores + ElasticNet',
    'Model 4: MAPE-DGB': 'Direct-Loss Gradient Booster + Sample-Weighted MAPE Optimization'
}

# 1. Summary DataFrame
summary_rows = []
for rank, m in enumerate(top10_models, 1):
    c_avg = df_class_all[df_class_all['Model'] == m]['Average'].values[0]
    v_avg = df_value_all[df_value_all['Model'] == m]['Average'].values[0]
    r_avg = df_ratio_all[df_ratio_all['Model'] == m]['Average'].values[0]
    rng_avg = df_range_all[df_range_all['Model'] == m]['Average'].values[0]
    c_val = float(str(c_avg).replace('%', ''))
    v_val = float(str(v_avg).replace('%', ''))
    r_val = float(str(r_avg).replace('%', ''))
    rng_val = float(str(rng_avg).replace('%', ''))
    c_score = (c_val + v_val) / 2.0
    summary_rows.append({
        'Rank': f"#{rank}",
        'Model Name': m,
        'Architecture / Preprocessing': model_descriptions.get(m, 'Advanced Chemometric ML'),
        'Class Accuracy (%)': round(c_val, 1),
        'User Value Accuracy (%)': round(v_val, 1),
        'Ratio Value Accuracy (%)': round(r_val, 1),
        'Range Value Accuracy (%)': round(rng_val, 1),
        'Combined Score (%)': round(c_score, 1)
    })
df_summary = pd.DataFrame(summary_rows)

# 2. Filter Class and Value Accuracy Matrices
nutrients = ['OC', 'N', 'P2O5', 'K2O', 'SO4', 'Fe', 'Mn', 'Cu', 'Zn', 'B', 'Ca', 'Mg', 'Average']
df_class_top10 = df_class_all[df_class_all['Model'].isin(top10_models)].copy()
# Order according to ranking
df_class_top10['sort_order'] = df_class_top10['Model'].map({m: i for i, m in enumerate(top10_models)})
df_class_top10 = df_class_top10.sort_values('sort_order').drop(columns=['sort_order']).reset_index(drop=True)

df_value_top10 = df_value_all[df_value_all['Model'].isin(top10_models)].copy()
df_value_top10['sort_order'] = df_value_top10['Model'].map({m: i for i, m in enumerate(top10_models)})
df_value_top10 = df_value_top10.sort_values('sort_order').drop(columns=['sort_order']).reset_index(drop=True)

# 3. Side-by-Side Comparison Matrix
sbs_rows = []
for m in top10_models:
    c_vals = df_class_top10[df_class_top10['Model'] == m].iloc[0]
    v_vals = df_value_top10[df_value_top10['Model'] == m].iloc[0]
    row_dict = {'Model': m}
    for n in ['OC', 'N', 'P2O5', 'K2O', 'SO4', 'Fe', 'Mn', 'Cu', 'Zn', 'B', 'Ca', 'Mg', 'Average']:
        c_num = float(str(c_vals[n]).replace('%', ''))
        v_num = float(str(v_vals[n]).replace('%', ''))
        row_dict[f"{n} (Class %)"] = round(c_num, 1)
        row_dict[f"{n} (Value %)"] = round(v_num, 1)
    sbs_rows.append(row_dict)
df_sbs = pd.DataFrame(sbs_rows)

# 4. First 10 Models (Models 1 to 10 from Suite 1)
first10_models = df_class_all['Model'].iloc[:10].tolist()
df_class_first10 = df_class_all[df_class_all['Model'].isin(first10_models)].copy().reset_index(drop=True)
df_value_first10 = df_value_all[df_value_all['Model'].isin(first10_models)].copy().reset_index(drop=True)

# Write to Excel
with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
    df_summary.to_excel(writer, sheet_name='Top_10_Models_Summary', index=False, startrow=2)
    df_class_top10.to_excel(writer, sheet_name='Class_Accuracy_Top_10', index=False, startrow=2)
    df_value_top10.to_excel(writer, sheet_name='Value_Accuracy_Top_10', index=False, startrow=2)
    df_sbs.to_excel(writer, sheet_name='Side_By_Side_Comparison', index=False, startrow=2)
    df_class_first10.to_excel(writer, sheet_name='Models_1_to_10_Class', index=False, startrow=2)
    df_value_first10.to_excel(writer, sheet_name='Models_1_to_10_Value', index=False, startrow=2)

# Styling with openpyxl
wb = openpyxl.load_workbook(output_excel)

title_font = Font(name='Segoe UI', size=13, bold=True, color='FFFFFF')
title_fill = PatternFill(start_color='0D233A', end_color='0D233A', fill_type='solid')
header_font = Font(name='Segoe UI', size=11, bold=True, color='FFFFFF')
header_fill = PatternFill(start_color='1F4E78', end_color='1F4E78', fill_type='solid')

high_fill = PatternFill(start_color='E2EFDA', end_color='E2EFDA', fill_type='solid')  # Green (>= 75% or top)
med_fill = PatternFill(start_color='FFF2CC', end_color='FFF2CC', fill_type='solid')   # Yellow (50-74%)
low_fill = PatternFill(start_color='FCE4D6', end_color='FCE4D6', fill_type='solid')   # Soft orange (< 50%)

thin_border = Border(left=Side(style='thin', color='D9D9D9'), right=Side(style='thin', color='D9D9D9'),
                     top=Side(style='thin', color='D9D9D9'), bottom=Side(style='thin', color='D9D9D9'))

sheet_titles = {
    'Top_10_Models_Summary': 'TOP 10 ADVANCED MODELS BENCHMARK SUMMARY (CLASS & VALUE ACCURACY)',
    'Class_Accuracy_Top_10': 'TOP 10 MODELS: ISO 17025 CLASS ACCURACY (%) ACROSS 12 SOIL NUTRIENTS',
    'Value_Accuracy_Top_10': 'TOP 10 MODELS: USER RELATIVE VALUE ACCURACY (%) [max(0, 1 - |A-P|/A) * 100]',
    'Side_By_Side_Comparison': 'TOP 10 MODELS: SIDE-BY-SIDE CLASS ACCURACY (%) VS VALUE ACCURACY (%)',
    'Models_1_to_10_Class': 'SUITE 1 (MODELS 1 TO 10): ISO 17025 CLASS ACCURACY (%)',
    'Models_1_to_10_Value': 'SUITE 1 (MODELS 1 TO 10): USER VALUE ACCURACY (%)'
}

for s_name, title_text in sheet_titles.items():
    ws = wb[s_name]
    num_cols = ws.max_column
    
    # Title banner
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=num_cols)
    tc = ws.cell(row=1, column=1)
    tc.value = title_text
    tc.font = title_font
    tc.fill = title_fill
    tc.alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[1].height = 28
    ws.row_dimensions[3].height = 24
    
    # Header row
    for c in range(1, num_cols + 1):
        cell = ws.cell(row=3, column=c)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center')
        
    # Data rows
    for r in range(4, ws.max_row + 1):
        for c in range(1, num_cols + 1):
            cell = ws.cell(row=r, column=c)
            cell.border = thin_border
            cell.alignment = Alignment(horizontal='center', vertical='center')
            
            # Format numbers as percentages and color-code
            val_num = None
            if isinstance(cell.value, (int, float)):
                val_num = float(cell.value)
                cell.value = f"{val_num:.1f}%"
            elif isinstance(cell.value, str):
                cleaned = cell.value.replace('%', '').strip()
                try:
                    val_num = float(cleaned)
                    if not cell.value.endswith('%'):
                        cell.value = f"{val_num:.1f}%"
                except:
                    pass
                    
            if val_num is not None:
                if val_num >= 75.0:
                    cell.fill = high_fill
                elif val_num >= 50.0:
                    cell.fill = med_fill
                elif val_num > 0:
                    cell.fill = low_fill
                    
    # Auto-adjust column widths
    for col in ws.columns:
        cl = get_column_letter(col[0].column)
        max_l = max(len(str(c.value or '')) for c in col)
        ws.column_dimensions[cl].width = max(max_l + 4, 12)

wb.save(output_excel)
print(f"Successfully generated: {output_excel}")
