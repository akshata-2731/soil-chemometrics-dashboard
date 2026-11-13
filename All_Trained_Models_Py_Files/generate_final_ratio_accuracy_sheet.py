# -*- coding: utf-8 -*-
"""
================================================================================
FINAL EXCEL GENERATOR: VALUE ACCURACY IN RATIO FORM [min(A, P) / max(A, P) * 100]
================================================================================
Calculates sample-by-sample value accuracy where:
  If Actual = 1 and Predicted = 0.5 -> Accuracy = 50.0%
  Formula: (min(Actual, Predicted) / max(Actual, Predicted)) * 100%

Applies this formula across all 502 samples and 12 nutrients from Model 33:
Triple-Algorithm Hybrid LOOCV (PLSR + SVR-RBF + HistGB + 81 Chemometric Features).

Generates:
  1. 'Model_33_Triple_Hybrid_LOOCV_Ratio_Accuracy_Final.xlsx'
  2. 'Actual_vs_Predicted_Ratio_Accuracy_500_Samples.xlsx'
================================================================================
"""

import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import pandas as pd
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()
SOURCE_FILE = os.path.join(SCRIPT_DIR, 'Model_33_Triple_Hybrid_LOOCV_500_Samples_Results.xlsx')
OUTPUT_FILE_1 = os.path.join(SCRIPT_DIR, 'Model_33_Triple_Hybrid_LOOCV_Ratio_Accuracy_Final.xlsx')
OUTPUT_FILE_2 = os.path.join(SCRIPT_DIR, 'Actual_vs_Predicted_Ratio_Accuracy_500_Samples.xlsx')

NUTRIENT_FULL_NAMES = {
    'OC': 'Organic Carbon (%)',
    'Ca meq': 'Available Calcium (meq/100g)',
    'Mg meq': 'Available Magnesium (meq/100g)',
    'N Kg_ha': 'Available Nitrogen (Kg/ha)',
    'P2O5': 'Available Phosphorus (Kg/ha)',
    'K2O': 'Available Potassium (Kg/ha)',
    'SO4': 'Available Sulfate (ppm)',
    'Fe ppm': 'Available Iron (ppm)',
    'Mn ppm': 'Available Manganese (ppm)',
    'Cu ppm': 'Available Copper (ppm)',
    'Zn ppm': 'Available Zinc (ppm)',
    'B ppm': 'Available Boron (ppm)'
}

def compute_ratio_accuracy(act_v, pred_v):
    if act_v == 0 and pred_v == 0:
        return 100.0
    if act_v <= 0 or pred_v <= 0:
        return 0.0
    return (min(act_v, pred_v) / max(act_v, pred_v)) * 100.0

def build_workbook(output_path):
    print(f"Reading source data from: {SOURCE_FILE}")
    wb_src = openpyxl.load_workbook(SOURCE_FILE)
    nutrient_sheets = [s for s in wb_src.sheetnames if s != 'Triple_Hybrid_Summary']

    wb_out = openpyxl.Workbook()
    wb_out.remove(wb_out.active)

    font_family = "Segoe UI"
    title_font = Font(name=font_family, size=13, bold=True, color="FFFFFF")
    header_font = Font(name=font_family, size=10, bold=True, color="FFFFFF")
    data_font = Font(name=font_family, size=10)
    bold_font = Font(name=font_family, size=10, bold=True)
    
    correct_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
    correct_font = Font(name=font_family, size=10, color="375623", bold=True)
    missed_fill = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")
    missed_font = Font(name=font_family, size=10, color="C65911", bold=True)

    header_navy = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_blue = PatternFill(start_color="2F5597", end_color="2F5597", fill_type="solid")
    header_dark = PatternFill(start_color="203764", end_color="203764", fill_type="solid")
    zebra_fill = PatternFill(start_color="F9FAFB", end_color="F9FAFB", fill_type="solid")
    white_fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
    total_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")

    thin_line = Side(border_style="thin", color="D9D9D9")
    thick_bottom = Side(border_style="medium", color="1F4E78")
    double_bottom = Side(border_style="double", color="1F4E78")
    border_cell = Border(left=thin_line, right=thin_line, top=thin_line, bottom=thin_line)

    summary_rows = []
    processed_dfs = {}

    for s_name in nutrient_sheets:
        df = pd.read_excel(SOURCE_FILE, sheet_name=s_name, skiprows=2)
        act = df['Actual Value'].values.astype(float)
        pred = df['Final Predicted Value'].values.astype(float)
        val_range = float(act.max() - act.min())

        ratio_accs = np.array([compute_ratio_accuracy(a, p) for a, p in zip(act, pred)])
        range_accs = np.array([(1.0 - abs(a - p) / val_range) * 100.0 if val_range > 0 else 0.0 for a, p in zip(act, pred)])

        df['Value Accuracy (%)'] = np.round(ratio_accs, 2)
        df['Status Value Acc (>=50%)'] = np.where(ratio_accs >= 50.0, 'Pass', 'Fail')
        df['Status Value Acc (>=75%)'] = np.where(ratio_accs >= 75.0, 'Pass', 'Fail')
        df['Range Value Acc (%)'] = np.round(range_accs, 2)

        # Sort ascending by Actual Value
        df = df.sort_values(by='Actual Value', ascending=True).reset_index(drop=True)
        processed_dfs[s_name] = df

        n_valid = len(df)
        strict_acc = (df['Status'] == 'Correct').mean() * 100.0
        iso_acc = (df['ISO Buffer Status'] == 'Correct').mean() * 100.0
        mean_ratio_acc = ratio_accs.mean()
        pct_ge_50 = (ratio_accs >= 50.0).mean() * 100.0
        pct_ge_70 = (ratio_accs >= 70.0).mean() * 100.0
        pct_ge_75 = (ratio_accs >= 75.0).mean() * 100.0
        mean_range_acc = range_accs.mean()
        rmse = np.sqrt(np.mean((act - pred) ** 2))
        mae = np.mean(np.abs(act - pred))

        summary_rows.append({
            'Target Nutrient': s_name,
            'Full Name': NUTRIENT_FULL_NAMES.get(s_name, s_name),
            'Valid Samples': n_valid,
            'Strict Class Acc (%)': round(strict_acc, 2),
            'ISO Buffer Class Acc (%)': round(iso_acc, 2),
            'Mean Value Acc (Ratio %)': round(mean_ratio_acc, 2),
            '% Samples >= 50% Acc': round(pct_ge_50, 1),
            '% Samples >= 70% Acc': round(pct_ge_70, 1),
            '% Samples >= 75% Acc': round(pct_ge_75, 1),
            'Range Value Acc (%)': round(mean_range_acc, 2),
            'LOOCV RMSE': round(rmse, 4),
            'LOOCV MAE': round(mae, 4)
        })

    summary_df = pd.DataFrame(summary_rows)

    # -------------------------------------------------------------
    # 1. SHEET 1: SUMMARY
    # -------------------------------------------------------------
    ws_sum = wb_out.create_sheet(title='Performance_Summary')
    ws_sum.views.sheetView[0].showGridLines = True

    ws_sum.merge_cells('A1:L1')
    ws_sum['A1'] = "SOIL NUTRIENT PREDICTION PERFORMANCE BENCHMARK (500 SAMPLES)"
    ws_sum['A1'].font = title_font
    ws_sum['A1'].fill = header_navy
    ws_sum['A1'].alignment = Alignment(horizontal="center", vertical="center")
    ws_sum.row_dimensions[1].height = 28

    ws_sum.merge_cells('A2:L2')
    ws_sum['A2'] = "Value Accuracy Formula: min(Actual, Pred) / max(Actual, Pred) * 100% (e.g., Act=1, Pred=0.5 -> 50% Acc) | Strict LOOCV"
    ws_sum['A2'].font = Font(name=font_family, size=9, italic=True, color="595959")
    ws_sum['A2'].alignment = Alignment(horizontal="center", vertical="center")
    ws_sum.row_dimensions[2].height = 18

    headers_sum = [
        'Target Nutrient', 'Full Target Name', 'Valid Samples',
        'Strict Class Acc (%)', 'ISO Buffer Class Acc (%)',
        'Mean Value Acc (Ratio %)', '% Samples >= 50% Acc', '% Samples >= 70% Acc', '% Samples >= 75% Acc',
        'Range Value Acc (%)', 'LOOCV RMSE', 'LOOCV MAE'
    ]
    for col_idx, h in enumerate(headers_sum, 1):
        cell = ws_sum.cell(row=3, column=col_idx, value=h)
        cell.font = header_font
        cell.fill = header_blue
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = Border(left=thin_line, right=thin_line, top=thin_line, bottom=thick_bottom)
    ws_sum.row_dimensions[3].height = 28

    for row_idx, r in enumerate(summary_rows, 4):
        vals = [
            r['Target Nutrient'], r['Full Name'], r['Valid Samples'],
            r['Strict Class Acc (%)'], r['ISO Buffer Class Acc (%)'],
            r['Mean Value Acc (Ratio %)'], r['% Samples >= 50% Acc'], r['% Samples >= 70% Acc'], r['% Samples >= 75% Acc'],
            r['Range Value Acc (%)'], r['LOOCV RMSE'], r['LOOCV MAE']
        ]
        fill_c = zebra_fill if row_idx % 2 == 0 else white_fill
        for col_idx, val in enumerate(vals, 1):
            cell = ws_sum.cell(row=row_idx, column=col_idx, value=val)
            cell.font = data_font
            cell.fill = fill_c
            cell.border = border_cell
            cell.alignment = Alignment(horizontal="center" if col_idx in [1, 3] else ("left" if col_idx == 2 else "right"), vertical="center")
        ws_sum.row_dimensions[row_idx].height = 20

    # Macro Average Row
    avg_row_idx = len(summary_rows) + 4
    avg_vals = [
        'OVERALL AVERAGE', 'All 12 Soil Nutrients', int(summary_df['Valid Samples'].mean()),
        round(summary_df['Strict Class Acc (%)'].mean(), 2),
        round(summary_df['ISO Buffer Class Acc (%)'].mean(), 2),
        round(summary_df['Mean Value Acc (Ratio %)'].mean(), 2),
        round(summary_df['% Samples >= 50% Acc'].mean(), 1),
        round(summary_df['% Samples >= 70% Acc'].mean(), 1),
        round(summary_df['% Samples >= 75% Acc'].mean(), 1),
        round(summary_df['Range Value Acc (%)'].mean(), 2),
        round(summary_df['LOOCV RMSE'].mean(), 2),
        round(summary_df['LOOCV MAE'].mean(), 2)
    ]
    for col_idx, val in enumerate(avg_vals, 1):
        cell = ws_sum.cell(row=avg_row_idx, column=col_idx, value=val)
        cell.font = bold_font
        cell.fill = total_fill
        cell.border = Border(left=thin_line, right=thin_line, top=thick_bottom, bottom=double_bottom)
        cell.alignment = Alignment(horizontal="center" if col_idx in [1, 3] else ("left" if col_idx == 2 else "right"), vertical="center")
    ws_sum.row_dimensions[avg_row_idx].height = 22

    for col in ws_sum.columns:
        max_len = max(len(str(c.value or '')) for c in col)
        col_letter = get_column_letter(col[0].column)
        ws_sum.column_dimensions[col_letter].width = max(max_len + 3, 12)
    ws_sum.column_dimensions['B'].width = 28

    # -------------------------------------------------------------
    # 2. SHEETS 2-13: NUTRIENT SHEETS
    # -------------------------------------------------------------
    for s_name in nutrient_sheets:
        df_elem = processed_dfs[s_name]
        ws = wb_out.create_sheet(title=s_name)
        ws.views.sheetView[0].showGridLines = True

        ws.merge_cells('A1:J1')
        ws['A1'] = f"{s_name} ({NUTRIENT_FULL_NAMES.get(s_name, s_name)}) - PREDICTED VS ACTUAL (500 SAMPLES)"
        ws['A1'].font = title_font
        ws['A1'].fill = header_dark
        ws['A1'].alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[1].height = 28

        ws.merge_cells('A2:J2')
        ws['A2'] = f"Sorted ascending by Actual Value | Value Accuracy Formula: min(Actual, Pred) / max(Actual, Pred) * 100% (e.g. Act=1, Pred=0.5 -> 50%)"
        ws['A2'].font = Font(name=font_family, size=9, italic=True, color="595959")
        ws['A2'].alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[2].height = 18

        headers_cols = [
            'Sample ID', 'Actual Class', 'Predicted Class', 'Status', 'ISO Buffer Status',
            'Actual Value', 'Final Predicted Value',
            'Value Accuracy (%)', 'Status Value Acc (>=50%)', 'Status Value Acc (>=75%)'
        ]

        for col_idx, h in enumerate(headers_cols, 1):
            cell = ws.cell(row=3, column=col_idx, value=h)
            cell.font = header_font
            cell.fill = header_navy
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = Border(left=thin_line, right=thin_line, top=thin_line, bottom=thick_bottom)
        ws.row_dimensions[3].height = 26

        for r_i, row in df_elem.iterrows():
            curr_row = r_i + 4
            fill_c = zebra_fill if curr_row % 2 == 0 else white_fill
            row_vals = [
                row['Sample ID'], row['Actual Class'], row['Predicted Class'],
                row['Status'], row['ISO Buffer Status'],
                row['Actual Value'], row['Final Predicted Value'],
                row['Value Accuracy (%)'], row['Status Value Acc (>=50%)'], row['Status Value Acc (>=75%)']
            ]
            for c_i, val in enumerate(row_vals, 1):
                col_name = headers_cols[c_i - 1]
                cell = ws.cell(row=curr_row, column=c_i, value=val)
                cell.font = data_font
                cell.fill = fill_c
                cell.border = border_cell

                if col_name in ['Status', 'ISO Buffer Status']:
                    if val == 'Correct':
                        cell.fill = correct_fill
                        cell.font = correct_font
                    else:
                        cell.fill = missed_fill
                        cell.font = missed_font
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                elif col_name in ['Status Value Acc (>=50%)', 'Status Value Acc (>=75%)']:
                    if val == 'Pass':
                        cell.fill = correct_fill
                        cell.font = correct_font
                    else:
                        cell.fill = missed_fill
                        cell.font = missed_font
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                elif col_name in ['Actual Value', 'Final Predicted Value', 'Value Accuracy (%)']:
                    cell.alignment = Alignment(horizontal="right", vertical="center")
                    cell.number_format = '0.00'
                elif col_name == 'Sample ID':
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                else:
                    cell.alignment = Alignment(horizontal="center", vertical="center")
            ws.row_dimensions[curr_row].height = 18

        for col in ws.columns:
            max_len = max(len(str(c.value or '')) for c in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 14)

    wb_out.save(output_path)
    print(f"Workbook successfully saved to: {output_path}")

def main():
    build_workbook(OUTPUT_FILE_1)
    build_workbook(OUTPUT_FILE_2)

if __name__ == '__main__':
    main()
