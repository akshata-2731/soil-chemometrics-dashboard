import os
import sys
import glob
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from app import execute_prediction, ALL_TARGETS, extract_actual, MODELS_DIR

OUTPUT_DIR = PROJECT_ROOT / "All_76_Models_Actual_vs_Predicted"
DATA_FILE = PROJECT_ROOT / "data" / "data.xlsx"

def run_export():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Loading data from {DATA_FILE}...")
    df_data = pd.read_excel(DATA_FILE)
    df_data.fillna(0, inplace=True)
    samples = df_data.to_dict(orient="records")
    total_samples = len(samples)
    print(f"Loaded {total_samples} soil samples.")

    # Discover all 76 models
    model_dirs = sorted([
        d for d in os.listdir(MODELS_DIR) 
        if os.path.isdir(os.path.join(MODELS_DIR, d)) and not d.startswith('.')
    ])
    print(f"Found {len(model_dirs)} ML model suites to evaluate.\n")

    master_summary_rows = []
    all_consolidated_predictions = []

    for m_idx, model_name in enumerate(model_dirs, 1):
        print(f"[{m_idx:02d}/{len(model_dirs)}] Evaluating: {model_name}...")
        model_predictions = []
        model_nut_summaries = []

        for target in ALL_TARGETS:
            actuals = []
            preds = []
            errors = []
            abs_errors = []
            accuracies = []
            passed_list = []

            for s_idx, sample in enumerate(samples, 1):
                s_id = sample.get("Sample_ID", f"Sample_{s_idx}")
                actual = extract_actual(sample, target)
                if actual is None:
                    continue

                try:
                    res = execute_prediction(
                        sample_data=sample,
                        target=target,
                        method_type="ml",
                        method_id=model_name,
                        is_cal_required=False
                    )
                    pred = res.get("final_prediction")
                    if pred is None:
                        continue

                    err = pred - actual
                    denom = abs(actual) if abs(actual) > 1e-4 else 1.0
                    err_pct = (abs(err) / denom) * 100.0
                    acc = max(0.0, 100.0 - err_pct)
                    passed = (acc >= 75.0)

                    actuals.append(actual)
                    preds.append(pred)
                    errors.append(err)
                    abs_errors.append(abs(err))
                    accuracies.append(acc)
                    passed_list.append(passed)

                    row_record = {
                        "Model_Name": model_name,
                        "Sample_Index": s_idx,
                        "Sample_ID": s_id,
                        "Nutrient": target,
                        "Actual_Value": round(actual, 4),
                        "Predicted_Value": round(pred, 4),
                        "Error": round(err, 4),
                        "Absolute_Error": round(abs(err), 4),
                        "Accuracy_Pct": round(acc, 2),
                        "Passed_75Pct": "PASS" if passed else "FAIL"
                    }
                    model_predictions.append(row_record)
                    all_consolidated_predictions.append(row_record)

                except Exception as e:
                    pass

            n_count = len(actuals)
            if n_count > 0:
                avg_acc = np.mean(accuracies)
                pass_rate = (sum(passed_list) / n_count) * 100.0
                mae = np.mean(abs_errors)
                rmse = np.sqrt(np.mean(np.array(errors) ** 2))

                nut_summary = {
                    "Model_Name": model_name,
                    "Nutrient": target,
                    "Total_Samples": n_count,
                    "Passed_Samples": sum(passed_list),
                    "Pass_Rate_Pct": round(pass_rate, 2),
                    "Avg_Accuracy_Pct": round(avg_acc, 2),
                    "MAE": round(mae, 4),
                    "RMSE": round(rmse, 4)
                }
                model_nut_summaries.append(nut_summary)
                master_summary_rows.append(nut_summary)

        # Save individual model Excel file
        if model_predictions:
            indiv_file = OUTPUT_DIR / f"{model_name}_Actual_vs_Predicted.xlsx"
            with pd.ExcelWriter(indiv_file, engine='xlsxwriter') as writer:
                wb = writer.book
                hdr_fmt = wb.add_format({'bold': True, 'bg_color': '#0284c7', 'font_color': 'white', 'border': 1})
                sub_hdr = wb.add_format({'bold': True, 'bg_color': '#10b981', 'font_color': 'white', 'border': 1})

                # Summary sheet
                df_nut_sum = pd.DataFrame(model_nut_summaries)
                df_nut_sum.to_excel(writer, sheet_name="Performance Summary", index=False)
                ws1 = writer.sheets["Performance Summary"]
                for c_idx, c_name in enumerate(df_nut_sum.columns):
                    ws1.write(0, c_idx, c_name, sub_hdr)
                    ws1.set_column(c_idx, c_idx, 18)

                # Predictions sheet
                df_preds = pd.DataFrame(model_predictions)
                df_preds.to_excel(writer, sheet_name="Actual vs Predicted", index=False)
                ws2 = writer.sheets["Actual vs Predicted"]
                for c_idx, c_name in enumerate(df_preds.columns):
                    ws2.write(0, c_idx, c_name, hdr_fmt)
                    ws2.set_column(c_idx, c_idx, 16)

    # Now create Master Summary Workbook
    print("\nGenerating Master Workbook in folder...")
    master_file = OUTPUT_DIR / "00_ALL_76_MODELS_MASTER_SUMMARY.xlsx"
    df_all_sum = pd.DataFrame(master_summary_rows)

    with pd.ExcelWriter(master_file, engine='xlsxwriter') as writer:
        wb = writer.book
        h_gold = wb.add_format({'bold': True, 'bg_color': '#d97706', 'font_color': 'white', 'border': 1})
        h_blue = wb.add_format({'bold': True, 'bg_color': '#0284c7', 'font_color': 'white', 'border': 1})
        h_green = wb.add_format({'bold': True, 'bg_color': '#059669', 'font_color': 'white', 'border': 1})

        # 1. Best / Champion Model per Nutrient
        champions = []
        for target in ALL_TARGETS:
            target_rows = [r for r in master_summary_rows if r["Nutrient"] == target]
            if target_rows:
                target_rows.sort(key=lambda x: (-x["Avg_Accuracy_Pct"], -x["Pass_Rate_Pct"], x["MAE"]))
                top = target_rows[0].copy()
                top["Rank"] = 1
                champions.append(top)

        if champions:
            df_champ = pd.DataFrame(champions)
            cols = ["Nutrient", "Model_Name", "Avg_Accuracy_Pct", "Pass_Rate_Pct", "MAE", "RMSE", "Passed_Samples", "Total_Samples"]
            df_champ = df_champ[[c for c in cols if c in df_champ.columns]]
            df_champ.to_excel(writer, sheet_name="Champion Models Per Nutrient", index=False)
            ws = writer.sheets["Champion Models Per Nutrient"]
            for c_idx, c_name in enumerate(df_champ.columns):
                ws.write(0, c_idx, c_name, h_gold)
                ws.set_column(c_idx, c_idx, 20)

        # 2. Leaderboard by Nutrient (Ranked Highest to Lowest Accuracy)
        df_ranked = df_all_sum.sort_values(by=["Nutrient", "Avg_Accuracy_Pct", "Pass_Rate_Pct"], ascending=[True, False, False])
        df_ranked.to_excel(writer, sheet_name="Leaderboard By Nutrient", index=False)
        ws = writer.sheets["Leaderboard By Nutrient"]
        for c_idx, c_name in enumerate(df_ranked.columns):
            ws.write(0, c_idx, c_name, h_green)
            ws.set_column(c_idx, c_idx, 18)

        # 3. Overall Global Model Ranking
        global_avg = df_all_sum.groupby("Model_Name").agg({
            "Avg_Accuracy_Pct": "mean",
            "Pass_Rate_Pct": "mean",
            "MAE": "mean",
            "RMSE": "mean",
            "Passed_Samples": "sum",
            "Total_Samples": "sum"
        }).reset_index()
        global_avg["Avg_Accuracy_Pct"] = global_avg["Avg_Accuracy_Pct"].round(2)
        global_avg["Pass_Rate_Pct"] = global_avg["Pass_Rate_Pct"].round(2)
        global_avg["MAE"] = global_avg["MAE"].round(4)
        global_avg["RMSE"] = global_avg["RMSE"].round(4)
        global_avg = global_avg.sort_values(by=["Avg_Accuracy_Pct", "Pass_Rate_Pct"], ascending=[False, False])
        global_avg.insert(0, "Global_Rank", range(1, len(global_avg) + 1))

        global_avg.to_excel(writer, sheet_name="Overall Model Rankings", index=False)
        ws = writer.sheets["Overall Model Rankings"]
        for c_idx, c_name in enumerate(global_avg.columns):
            ws.write(0, c_idx, c_name, h_blue)
            ws.set_column(c_idx, c_idx, 18)

        # 4. Master Consolidated Predictions Sheet
        df_all_preds = pd.DataFrame(all_consolidated_predictions)
        # Limit rows to 100,000 if too large
        df_all_preds.iloc[:100000].to_excel(writer, sheet_name="All Models Predictions Sample", index=False)
        ws = writer.sheets["All Models Predictions Sample"]
        for c_idx, c_name in enumerate(df_all_preds.columns):
            ws.write(0, c_idx, c_name, h_blue)
            ws.set_column(c_idx, c_idx, 16)

    # Create README index in the folder
    readme_path = OUTPUT_DIR / "00_INDEX_AND_REPORT.txt"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("================================================================================\n")
        f.write("      ALL 76 ML MODELS — ACTUAL VS PREDICTED COMPREHENSIVE REPOSITORY           \n")
        f.write("================================================================================\n\n")
        f.write(f"Generated Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Models Evaluated: {len(model_dirs)}\n")
        f.write(f"Total Soil Samples: {total_samples}\n")
        f.write(f"Target Nutrients: {', '.join(ALL_TARGETS)}\n\n")
        f.write("FILES IN THIS FOLDER:\n")
        f.write("1. 00_ALL_76_MODELS_MASTER_SUMMARY.xlsx -> Master workbook with Champions, Leaderboard & Comparisons\n")
        f.write("2. {Model_Name}_Actual_vs_Predicted.xlsx -> Dedicated Excel file for each of the 76 models\n\n")
        f.write("TOP 5 OVERALL MODELS BY AVERAGE ACCURACY:\n")
        for idx, row in global_avg.head(5).iterrows():
            f.write(f"  #{row['Global_Rank']} {row['Model_Name']} | Avg Acc: {row['Avg_Accuracy_Pct']}% | Pass Rate: {row['Pass_Rate_Pct']}%\n")
        f.write("\nCHAMPION MODEL PER NUTRIENT:\n")
        for c in champions:
            f.write(f"  * {c['Nutrient']}: {c['Model_Name']} (Accuracy: {c['Avg_Accuracy_Pct']}%, Pass Rate: {c['Pass_Rate_Pct']}%)\n")

    print(f"\nALL 76 MODELS ACTUAL VS PREDICTED COMPLETED SUCCESSFULLY!")
    print(f"Results saved to folder: {OUTPUT_DIR}")

if __name__ == "__main__":
    run_export()
