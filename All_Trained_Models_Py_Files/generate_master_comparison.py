# -*- coding: utf-8 -*-
"""
Compile Master Comparison of All 10 New Compound Models (49-Fold LOOCV)
"""

import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import pandas as pd
import numpy as np

MODEL_FILES = {
    'Model 1: CR-SDPR-ISO': 'New_Compound_Model_1_CR_SDPR_ISO_LOOCV_49_Samples.xlsx',
    'Model 2: CQC-HCB-BAE': 'New_Compound_Model_2_CQC_HCB_BAE_LOOCV_49_Samples.xlsx',
    'Model 3: GA-KFDA-CRidge': 'New_Compound_Model_3_GA_KFDA_CRidge_LOOCV_49_Samples.xlsx',
    'Model 4: OSC-CatBoost-AQC': 'New_Compound_Model_4_OSC_CatBoost_AQC_LOOCV_49_Samples.xlsx',
    'Model 5: GADF-2DPCA-MMC': 'New_Compound_Model_5_GADF_2DPCA_MMC_LOOCV_49_Samples.xlsx',
    'Model 6: VAE-CSLGBM-CHB': 'New_Compound_Model_6_VAE_CSLGBM_CHB_LOOCV_49_Samples.xlsx',
    'Model 7: WPD-MTEN-OLC': 'New_Compound_Model_7_WPD_MTEN_OLC_LOOCV_49_Samples.xlsx',
    'Model 8: SID-LLE-NWK': 'New_Compound_Model_8_SID_LLE_NWK_LOOCV_49_Samples.xlsx',
    'Model 9: DRL-NS-LBMP': 'New_Compound_Model_9_DRL_NS_LBMP_LOOCV_49_Samples.xlsx',
    'Model 10: RCR-SVOC-DSH': 'New_Compound_Model_10_RCR_SVOC_DSH_LOOCV_49_Samples.xlsx'
}

def main():
    macro_records = []
    nutrient_records = []
    
    for m_name, f_name in MODEL_FILES.items():
        if not os.path.exists(f_name):
            print(f"Warning: {f_name} not found!")
            continue
        df_summary = pd.read_excel(f_name, sheet_name='Macro_Summary', skiprows=2)
        
        # Macro row
        macro_row = df_summary[df_summary['Target'] == 'MACRO AVG'].iloc[0]
        macro_records.append({
            'Model Name': m_name,
            'ISO Class Acc (%)': macro_row['ISO Class Acc (%)'],
            'Strict Class Acc (%)': macro_row['Strict Class Acc (%)'],
            'Range Value Acc (%)': macro_row['Range Value Acc (%)'],
            'Raw Ratio Acc (%)': macro_row['Raw Ratio Acc (%)'],
            'LOQ Floor Acc (%)': macro_row['LOQ Floor Acc (%)'],
            'Macro RMSE': macro_row['RMSE'],
            'Macro MAE': macro_row['MAE'],
            'Range > 75%?': macro_row['Range > 75%?'],
            'ISO Class > 75%?': macro_row['ISO Class > 75%?'],
            'Workbook Filename': f_name
        })
        
        # Individual nutrients
        nut_df = df_summary[df_summary['Target'] != 'MACRO AVG']
        for _, r in nut_df.iterrows():
            nutrient_records.append({
                'Model Name': m_name,
                'Nutrient': r['Target'],
                'Full Name': r['Full Name'],
                'ISO Class Acc (%)': r['ISO Class Acc (%)'],
                'Strict Class Acc (%)': r['Strict Class Acc (%)'],
                'Range Value Acc (%)': r['Range Value Acc (%)'],
                'Raw Ratio Acc (%)': r['Raw Ratio Acc (%)'],
                'LOQ Floor Acc (%)': r['LOQ Floor Acc (%)'],
                'RMSE': r['RMSE'],
                'MAE': r['MAE']
            })
            
    df_macro = pd.DataFrame(macro_records)
    df_nut = pd.DataFrame(nutrient_records)
    
    # Sort macro by ISO Class Acc descending
    df_macro_sorted = df_macro.sort_values(by='ISO Class Acc (%)', ascending=False).reset_index(drop=True)
    
    # Pivot tables for nutrient comparisons
    pivot_iso = df_nut.pivot(index='Nutrient', columns='Model Name', values='ISO Class Acc (%)')
    pivot_range = df_nut.pivot(index='Nutrient', columns='Model Name', values='Range Value Acc (%)')
    pivot_loq_ratio = df_nut.pivot(index='Nutrient', columns='Model Name', values='LOQ Floor Acc (%)')
    pivot_rmse = df_nut.pivot(index='Nutrient', columns='Model Name', values='RMSE')
    
    out_file = 'All_10_New_Compound_Models_LOOCV_Master_Comparison.xlsx'
    with pd.ExcelWriter(out_file, engine='openpyxl') as writer:
        df_macro_sorted.to_excel(writer, sheet_name='Master_Macro_Leaderboard', index=False, startrow=2)
        pivot_iso.to_excel(writer, sheet_name='Nutrient_ISO_Class_Acc', startrow=2)
        pivot_range.to_excel(writer, sheet_name='Nutrient_Range_Value_Acc', startrow=2)
        pivot_loq_ratio.to_excel(writer, sheet_name='Nutrient_LOQ_Ratio_Acc', startrow=2)
        pivot_rmse.to_excel(writer, sheet_name='Nutrient_RMSE', startrow=2)
        
    # Styling
    wb = openpyxl.load_workbook(out_file)
    
    header_font = Font(name='Segoe UI', size=11, bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='1F4E78', end_color='1F4E78', fill_type='solid')
    title_font = Font(name='Segoe UI', size=13, bold=True, color='FFFFFF')
    title_fill = PatternFill(start_color='0D233A', end_color='0D233A', fill_type='solid')
    top1_fill = PatternFill(start_color='E2EFDA', end_color='E2EFDA', fill_type='solid')
    top1_font = Font(name='Segoe UI', size=11, bold=True, color='276A3C')
    
    thin_border = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9')
    )
    
    for s_name in wb.sheetnames:
        ws = wb[s_name]
        ws.row_dimensions[1].height = 28
        ws.row_dimensions[3].height = 24
        
        # Title merge
        max_col = ws.max_column
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=max_col)
        t_cell = ws.cell(row=1, column=1)
        t_cell.value = f"49-FOLD LOOCV BENCHMARK: {s_name.replace('_', ' ').upper()}"
        t_cell.font = title_font
        t_cell.fill = title_fill
        t_cell.alignment = Alignment(horizontal='center', vertical='center')
        
        for col in range(1, max_col + 1):
            c = ws.cell(row=3, column=col)
            c.font = header_font
            c.fill = header_fill
            c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            
        for r in range(4, ws.max_row + 1):
            for c in range(1, max_col + 1):
                cell = ws.cell(row=r, column=c)
                cell.border = thin_border
                cell.alignment = Alignment(horizontal='center', vertical='center')
                if s_name == 'Master_Macro_Leaderboard' and r == 4:
                    cell.fill = top1_fill
                    cell.font = top1_font
                    
        for col in ws.columns:
            col_letter = get_column_letter(col[0].column)
            max_len = max(len(str(cell.value or '')) for cell in col)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 13)
            
    wb.save(out_file)
    print(f"Master comparison saved to: {out_file}")
    print("\nMaster Macro Leaderboard:")
    print(df_macro_sorted.to_string(index=False))

if __name__ == '__main__':
    main()
