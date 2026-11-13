# -*- coding: utf-8 -*-
"""
Generate Value Accuracy Report and Graphic for First 10 Compound Models
Matching the layout, styling, and formatting of Image 2.
"""

import os
import shutil
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle

FILES = [
    ('Compound Model 1 (KM-SVC-ET)', 'Compound_Model_1_KM_SVC_ET_LOOCV_49_Samples.xlsx'),
    ('Compound Model 2 (SNV-SG1-SVR)', 'Compound_Model_2_SNV_SG1_SVR_LOOCV_49_Samples.xlsx'),
    ('Compound Model 3 (PLS-GB-CB)', 'Compound_Model_3_PLS_GB_CB_LOOCV_49_Samples.xlsx'),
    ('Compound Model 4 (MGOQI)', 'Compound_Model_4_MGOQI_LOOCV_49_Samples.xlsx'),
    ('Compound Model 5 (LOQ Floor)', 'Compound_Model_5_LOQ_Floor_LOOCV_49_Samples.xlsx'),
    ('Compound Model 6 (ZIH-ET-LOQ)', 'Compound_Model_6_ZIH_ET_LOQ_LOOCV_49_Samples.xlsx'),
    ('Compound Model 7 (EN-KRR-H)', 'Compound_Model_7_EN_KRR_H_LOOCV_49_Samples.xlsx'),
    ('Compound Model 8 (LW-KNN-Manifold)', 'Compound_Model_8_LW_KNN_Manifold_LOOCV_49_Samples.xlsx'),
    ('Compound Model 9 (SuperLearner Stack)', 'Compound_Model_9_SuperLearner_Stack_LOOCV_49_Samples.xlsx'),
    ('Compound Model 10 (Bayes Log Shrink)', 'Compound_Model_10_Bayes_Log_Shrink_LOOCV_49_Samples.xlsx')
]

NUTRIENTS_10 = [
    ('OC', 'OC'),
    ('N', 'N Kg_ha'),
    ('P2O5', 'P2O5'),
    ('K2O', 'K2O'),
    ('SO4', 'SO4'),
    ('Fe', 'Fe ppm'),
    ('Mn', 'Mn ppm'),
    ('Cu', 'Cu ppm'),
    ('Zn', 'Zn ppm'),
    ('B', 'B ppm')
]

ALL_NUTRIENTS_12 = [
    ('OC', 'OC'),
    ('Ca', 'Ca meq'),
    ('Mg', 'Mg meq'),
    ('N', 'N Kg_ha'),
    ('P2O5', 'P2O5'),
    ('K2O', 'K2O'),
    ('SO4', 'SO4'),
    ('Fe', 'Fe ppm'),
    ('Mn', 'Mn ppm'),
    ('Cu', 'Cu ppm'),
    ('Zn', 'Zn ppm'),
    ('B', 'B ppm')
]

def compute_user_accuracy(act, pred):
    """
    User formula: if actual = 1 and pred = 0.5 or 1.5, accuracy = 50%
    Formula: max(0, 1 - abs(act - pred) / act) * 100
    """
    accs = []
    for a, p in zip(act, pred):
        if a == 0:
            accs.append(100.0 if p == 0 else 0.0)
        else:
            rel_err = abs(a - p) / a
            accs.append(max(0.0, (1.0 - rel_err)) * 100.0)
    return np.array(accs)

def main():
    print("Extracting sample data from first 10 compound models...")
    
    # Build 10-nutrient summary
    rows_10 = []
    for label, fpath in FILES:
        row = {'Model': label}
        vals = []
        for short_n, sheet_n in NUTRIENTS_10:
            df = pd.read_excel(fpath, sheet_name=sheet_n, skiprows=2)
            act = df['Actual Value'].values
            pred = df['Predicted Value'].values
            accs = compute_user_accuracy(act, pred)
            m_acc = round(float(np.mean(accs)), 1)
            row[short_n] = m_acc
            vals.append(m_acc)
        row['Mean'] = round(float(np.mean(vals)), 1)
        rows_10.append(row)
    df_10 = pd.DataFrame(rows_10)
    
    # Build 12-nutrient summary
    rows_12 = []
    for label, fpath in FILES:
        row = {'Model': label}
        vals = []
        for short_n, sheet_n in ALL_NUTRIENTS_12:
            df = pd.read_excel(fpath, sheet_name=sheet_n, skiprows=2)
            act = df['Actual Value'].values
            pred = df['Predicted Value'].values
            accs = compute_user_accuracy(act, pred)
            m_acc = round(float(np.mean(accs)), 1)
            row[short_n] = m_acc
            vals.append(m_acc)
        row['Mean'] = round(float(np.mean(vals)), 1)
        rows_12.append(row)
    df_12 = pd.DataFrame(rows_12)
    
    print("\n--- 10-Nutrient Summary Table (Matches Image 2) ---")
    print(df_10.to_string(index=False))
    
    # -------------------------------------------------------------------------
    # 1. RENDER GRAPHIC MATCHING IMAGE 2 EXACTLY
    # -------------------------------------------------------------------------
    print("\nRendering high-res graphic matching Image 2 styling...")
    
    models = df_10['Model'].values
    cols = ['OC', 'N', 'P2O5', 'K2O', 'SO4', 'Fe', 'Mn', 'Cu', 'Zn', 'B', 'Mean']
    matrix = df_10[cols].values
    
    n_rows, n_cols = matrix.shape
    
    fig, ax = plt.subplots(figsize=(14, 7.5), dpi=300)
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    
    # Min and max for colormap
    vmin, vmax = 20.0, 75.0
    cmap = plt.cm.Greens
    
    # Geometry settings
    cell_w = 0.82
    cell_h = 0.52
    col_w_model = 3.6
    
    y_start = n_rows * cell_h + 0.5
    
    # Title & Subtitle
    ax.text(0.1, y_start + 1.25, "2. Value accuracy (%) by nutrient and model",
            fontsize=17, fontweight='bold', color='#1B4D2E', ha='left', va='center',
            family='sans-serif')
    
    ax.text(0.1, y_start + 0.72,
            "Each cell is the mean per-sample value accuracy for one nutrient and one model. Darker green means higher accuracy. The best model in each column is outlined in bold.",
            fontsize=10.5, color='#333333', ha='left', va='center', family='sans-serif')
    
    # Header row
    # Model header
    ax.add_patch(Rectangle((0.1, y_start), col_w_model, cell_h, facecolor='#1B4D2E', edgecolor='white', linewidth=1))
    ax.text(0.1 + col_w_model / 2.0, y_start + cell_h / 2.0, "Model",
            fontsize=11.5, fontweight='bold', color='white', ha='center', va='center', family='sans-serif')
    
    # Nutrient headers
    for j, col_name in enumerate(cols):
        x = 0.1 + col_w_model + j * cell_w
        ax.add_patch(Rectangle((x, y_start), cell_w, cell_h, facecolor='#1B4D2E', edgecolor='white', linewidth=1))
        # Formatted label for P2O5 and SO4
        disp_name = col_name
        if col_name == 'P2O5':
            disp_name = r"$\mathregular{P_2O_5}$"
        elif col_name == 'SO4':
            disp_name = r"$\mathregular{SO_4}$"
        elif col_name == 'K2O':
            disp_name = r"$\mathregular{K_2O}$"
            
        ax.text(x + cell_w / 2.0, y_start + cell_h / 2.0, disp_name,
                fontsize=11, fontweight='bold', color='white', ha='center', va='center', family='sans-serif')
        
    # Best model indices per column
    best_row_indices = np.argmax(matrix, axis=0)
    
    # Data rows
    for i in range(n_rows):
        y = y_start - (i + 1) * cell_h
        
        # Model label box
        # Slightly softer dark green for model labels to distinguish from header
        ax.add_patch(Rectangle((0.1, y), col_w_model, cell_h, facecolor='#1F4E2E', edgecolor='white', linewidth=1))
        ax.text(0.25, y + cell_h / 2.0, models[i],
                fontsize=9.8, fontweight='bold', color='white', ha='left', va='center', family='sans-serif')
        
        # Data cells
        for j in range(n_cols):
            x = 0.1 + col_w_model + j * cell_w
            val = matrix[i, j]
            norm_val = (val - vmin) / (vmax - vmin)
            norm_val = np.clip(norm_val, 0.05, 0.95)
            cell_color = cmap(norm_val)
            
            # Determine text color based on brightness
            text_color = 'white' if norm_val > 0.52 else '#1A3311'
            
            is_best = (i == best_row_indices[j])
            
            # Base cell
            ax.add_patch(Rectangle((x, y), cell_w, cell_h, facecolor=cell_color, edgecolor='#E0E0E0', linewidth=0.8))
            
            # Text value
            txt_weight = 'bold' if is_best else 'normal'
            ax.text(x + cell_w / 2.0, y + cell_h / 2.0, f"{val:.1f}",
                    fontsize=10.2, fontweight=txt_weight, color=text_color, ha='center', va='center', family='sans-serif')
            
            # If best, add bold outline box
            if is_best:
                ax.add_patch(Rectangle((x, y), cell_w, cell_h, fill=False, edgecolor='#0D3012', linewidth=2.8))
                
    total_w = 0.1 + col_w_model + n_cols * cell_w + 0.3
    total_h = y_start + cell_h + 1.6
    
    ax.set_xlim(0, total_w)
    ax.set_ylim(0, total_h)
    ax.axis('off')
    
    plt.tight_layout()
    img_filename = 'Value_Accuracy_By_Nutrient_And_Model_First_10_Compound_Models.png'
    plt.savefig(img_filename, dpi=300, bbox_inches='tight', pad_inches=0.2)
    plt.close()
    print(f"Saved graphic to: {img_filename}")
    
    # Copy to artifacts directory
    artifact_dir = r'C:\Users\akash\.gemini\antigravity\brain\2e06cfda-6433-46b2-9d73-32b535b66c25'
    if os.path.exists(artifact_dir):
        dest_img = os.path.join(artifact_dir, img_filename)
        shutil.copy(img_filename, dest_img)
        print(f"Copied graphic to artifact directory: {dest_img}")
        
    # -------------------------------------------------------------------------
    # 2. CREATE MASTER EXCEL REPORT WITH SAMPLE-BY-SAMPLE ACCURACY
    # -------------------------------------------------------------------------
    excel_out = 'First_10_Compound_Models_Value_Accuracy_Report.xlsx'
    print(f"\nWriting dedicated Excel report: {excel_out}...")
    
    with pd.ExcelWriter(excel_out, engine='openpyxl') as writer:
        df_10.to_excel(writer, sheet_name='Summary_10_Nutrients', index=False, startrow=3)
        df_12.to_excel(writer, sheet_name='Summary_12_Nutrients', index=False, startrow=3)
        
        # Add sample-by-sample sheets for each of the 10 models
        for m_idx, (label, fpath) in enumerate(FILES, start=1):
            sample_records = []
            for short_n, sheet_n in ALL_NUTRIENTS_12:
                df_nut = pd.read_excel(fpath, sheet_name=sheet_n, skiprows=2)
                for s_i, r in df_nut.iterrows():
                    a = r['Actual Value']
                    p = r['Predicted Value']
                    if a == 0:
                        acc = 100.0 if p == 0 else 0.0
                    else:
                        acc = max(0.0, 1.0 - abs(a - p) / a) * 100.0
                    sample_records.append({
                        'Nutrient': short_n,
                        'Full Name': sheet_n,
                        'Sample ID': r['Sample ID'],
                        'Actual Value': a,
                        'Predicted Value': p,
                        'Absolute Error': abs(a - p),
                        'Value Accuracy (%) [User Formula]': round(acc, 2),
                        'Actual Class': r.get('Actual Class', ''),
                        'Predicted Class': r.get('Predicted Class', ''),
                        'ISO Class Match': r.get('ISO Class Match', '')
                    })
            df_m_samples = pd.DataFrame(sample_records)
            sheet_title = f"Model_{m_idx}_Samples"
            df_m_samples.to_excel(writer, sheet_name=sheet_title, index=False, startrow=2)
            
    # Format Excel sheets
    wb = openpyxl.load_workbook(excel_out)
    
    header_fill = PatternFill(start_color='1B4D2E', end_color='1B4D2E', fill_type='solid')
    header_font = Font(name='Segoe UI', size=11, bold=True, color='FFFFFF')
    title_font = Font(name='Segoe UI', size=13, bold=True, color='FFFFFF')
    title_fill = PatternFill(start_color='0E2E1B', end_color='0E2E1B', fill_type='solid')
    
    thin_border = Border(
        left=Side(style='thin', color='D0D0D0'),
        right=Side(style='thin', color='D0D0D0'),
        top=Side(style='thin', color='D0D0D0'),
        bottom=Side(style='thin', color='D0D0D0')
    )
    bold_box_border = Border(
        left=Side(style='medium', color='0E2E1B'),
        right=Side(style='medium', color='0E2E1B'),
        top=Side(style='medium', color='0E2E1B'),
        bottom=Side(style='medium', color='0E2E1B')
    )
    
    # Format Summary_10_Nutrients
    ws10 = wb['Summary_10_Nutrients']
    ws10.merge_cells('A1:L1')
    t_c = ws10['A1']
    t_c.value = "2. VALUE ACCURACY (%) BY NUTRIENT AND MODEL (FIRST 10 COMPOUND MODELS)"
    t_c.font = title_font
    t_c.fill = title_fill
    t_c.alignment = Alignment(horizontal='center', vertical='center')
    
    ws10.merge_cells('A2:L2')
    sub_c = ws10['A2']
    sub_c.value = "Each cell is the mean per-sample value accuracy [Formula: max(0, 1 - |Actual - Pred| / Actual) * 100]. Bold outlined = Best model."
    sub_c.font = Font(name='Segoe UI', size=10, italic=True, color='444444')
    sub_c.alignment = Alignment(horizontal='center', vertical='center')
    
    ws10.row_dimensions[1].height = 28
    ws10.row_dimensions[2].height = 20
    ws10.row_dimensions[4].height = 24
    
    for c in range(1, 13):
        cell = ws10.cell(row=4, column=c)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center')
        
    for r in range(5, 15):
        ws10.row_dimensions[r].height = 22
        # Model name cell
        m_cell = ws10.cell(row=r, column=1)
        m_cell.font = Font(name='Segoe UI', size=10, bold=True, color='FFFFFF')
        m_cell.fill = PatternFill(start_color='1F4E2E', end_color='1F4E2E', fill_type='solid')
        m_cell.alignment = Alignment(horizontal='left', vertical='center')
        m_cell.border = thin_border
        
        for c in range(2, 13):
            cell = ws10.cell(row=r, column=c)
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.font = Font(name='Segoe UI', size=10.5)
            cell.border = thin_border
            
    # Highlight best in each column in ws10
    for c_idx, c_name in enumerate(cols, start=2):
        best_val = df_10[c_name].max()
        for r_idx in range(5, 15):
            cell = ws10.cell(row=r_idx, column=c_idx)
            if round(float(cell.value), 1) == round(float(best_val), 1):
                cell.font = Font(name='Segoe UI', size=11, bold=True, color='0E2E1B')
                cell.border = bold_box_border
                cell.fill = PatternFill(start_color='C8E6C9', end_color='C8E6C9', fill_type='solid')
                
    for col in ws10.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = max(len(str(cell.value or '')) for cell in col)
        ws10.column_dimensions[col_letter].width = max(max_len + 3, 11)
    ws10.column_dimensions['A'].width = 38
    
    wb.save(excel_out)
    print(f"Successfully generated master workbook: {excel_out}")

if __name__ == '__main__':
    main()
