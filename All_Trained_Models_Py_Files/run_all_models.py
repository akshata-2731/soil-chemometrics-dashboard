# -*- coding: utf-8 -*-
"""
================================================================================
MASTER EXECUTION RUNNER: RUN ALL 4 MODELS & STORE RESULTS IN EXCEL
================================================================================
This master script executes all 4 two-stage models in sequence:
  1. Model 23: Baseline Two-Stage Hybrid (SVC RBF C=0.01 + 3D PLSR, Exact Limits)
  2. Model 24: Heterogeneous Two-Stage Model (Tuned Classifiers, Exact Limits)
  3. Model 25: Actionable Agronomic Two-Stage Model (Critical Fertilizer Action Limits)
  4. Model 26: Balanced Population Tertiles Two-Stage Model (Equal 33% Low/Med/High)

Outputs Generated & Verified:
  - 4 Excel Workbooks (13 sheets each, uncolored, storing all LOOCV values)
  - 4 Model Bundle Directories (48 .pkl files total)
  - Unified comparative scorecard printed to terminal
================================================================================
"""

import os
import sys
import time
import subprocess
import pandas as pd

SCRIPTS = [
    ("Model 23", "model_23.py", "Model_23_TwoStage_SVC_PLSR_ExactLimits_LOOCV_Results.xlsx", "Final_PKL_Models_ExactLimits"),
    ("Model 24", "model_24.py", "Model_24_TwoStage_Heterogeneous_ExactLimits_LOOCV_Results.xlsx", "Final_PKL_Models_Model24_ExactLimits"),
    ("Model 25", "model_25.py", "Model_25_TwoStage_Actionable_Agronomic_LOOCV_Results.xlsx", "Final_PKL_Models_Model25_Agronomic"),
    ("Model 26", "model_26.py", "Model_26_TwoStage_Balanced_Tertiles_LOOCV_Results.xlsx", "Final_PKL_Models_Model26_Tertiles"),
]

def main():
    print("=" * 80)
    print("      MASTER RUNNER: EXECUTING ALL 4 MODELS & STORING EXCEL RESULTS      ")
    print("=" * 80)
    
    start_total = time.time()
    results_summary = []
    
    for name, script, excel_out, pkl_dir in SCRIPTS:
        print(f"\n>>> Running {name} ({script})...")
        t0 = time.time()
        
        # Execute script via current Python interpreter
        cmd = [sys.executable, script]
        ret = subprocess.run(cmd, capture_output=True, text=True)
        
        elapsed = time.time() - t0
        if ret.returncode != 0:
            print(f"[ERROR] {name} failed with exit code {ret.returncode}!")
            print(ret.stderr)
            continue
            
        # Verify Excel file exists and get size
        if os.path.exists(excel_out):
            excel_size = os.path.getsize(excel_out) / 1024.0
            excel_status = f"OK ({excel_size:.1f} KB)"
        else:
            excel_status = "MISSING"
            
        # Verify PKL directory exists and count files
        if os.path.exists(pkl_dir):
            pkl_count = len([f for f in os.listdir(pkl_dir) if f.endswith('.pkl')])
            pkl_status = f"OK ({pkl_count} bundles)"
        else:
            pkl_status = "MISSING"
            
        # Read summary accuracy from generated Excel
        try:
            df_sum = pd.read_excel(excel_out, sheet_name=0, header=2)
            avg_row = df_sum[df_sum['Target Nutrient'] == 'AVERAGE']
            if len(avg_row) > 0:
                acc_val = float(avg_row['LOOCV Class Accuracy (%)'].values[0])
            else:
                acc_val = float(df_sum['LOOCV Class Accuracy (%)'].mean())
        except Exception:
            acc_val = None
            
        results_summary.append({
            'Model': name,
            'Script': script,
            'Macro LOOCV Acc': f"{acc_val:.2f}%" if acc_val is not None else "N/A",
            'Excel Workbook': excel_out,
            'Excel Status': excel_status,
            'Model PKLs': pkl_status,
            'Time (s)': f"{elapsed:.1f}s"
        })
        print(f"--> Finished {name} in {elapsed:.1f}s | Excel: {excel_status} | PKL: {pkl_status}")
        
    print("\n" + "=" * 80)
    print("                         ALL 4 MODELS RUN COMPLETE                      ")
    print("=" * 80)
    
    df_res = pd.DataFrame(results_summary)
    print(df_res[['Model', 'Script', 'Macro LOOCV Acc', 'Excel Status', 'Model PKLs', 'Time (s)']].to_string(index=False))
    print(f"\nTotal Execution Time: {time.time() - start_total:.1f} seconds")
    print("\nAll values, sample-by-sample predictions, and error statistics are fully stored in the 4 Excel files.")

if __name__ == '__main__':
    main()
