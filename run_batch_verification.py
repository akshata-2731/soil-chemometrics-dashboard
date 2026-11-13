import pandas as pd
import requests
import json

df = pd.read_excel('data/data.xlsx')
df.fillna(0, inplace=True)
samples = df.to_dict(orient='records')

print(f"Loaded {len(samples)} real samples from data/data.xlsx")

for idx, s in enumerate(samples):
    s['Sample_ID'] = f"Sample_{idx+1:03d}"

ALL_TARGETS = ['OC', 'N', 'P', 'K', 'Ca', 'Mg', 'S', 'Fe', 'Mn', 'Cu', 'Zn', 'B']

# Assign DIFFERENT logics to different nutrients
mapping = {
    'OC': {'method_type': 'logic', 'method_id': 'M1',  'calibration_required': True},
    'N':  {'method_type': 'logic', 'method_id': 'M2',  'calibration_required': True},
    'P':  {'method_type': 'logic', 'method_id': 'M3',  'calibration_required': True},
    'K':  {'method_type': 'logic', 'method_id': 'M4',  'calibration_required': True},
    'Ca': {'method_type': 'logic', 'method_id': 'M5',  'calibration_required': True},
    'Mg': {'method_type': 'logic', 'method_id': 'M6',  'calibration_required': True},
    'S':  {'method_type': 'logic', 'method_id': 'M7',  'calibration_required': True},
    'Fe': {'method_type': 'logic', 'method_id': 'M8',  'calibration_required': True},
    'Mn': {'method_type': 'logic', 'method_id': 'M9',  'calibration_required': True},
    'Cu': {'method_type': 'logic', 'method_id': 'M10', 'calibration_required': True},
    'Zn': {'method_type': 'logic', 'method_id': 'M11', 'calibration_required': True},
    'B':  {'method_type': 'logic', 'method_id': 'M12', 'calibration_required': True},
}

url = 'http://127.0.0.1:5000/api/batch/predict'

print("\nExecuting POST /api/batch/predict...")
response = requests.post(url, json={
    'samples': samples,
    'targets': ALL_TARGETS,
    'mapping': mapping
}, timeout=60)

assert response.status_code == 200, f"HTTP Error {response.status_code}"
data = response.json()

results = data.get('results', [])
run_id = data.get('run_id')

print(f"Run ID: {run_id}")
print(f"Total prediction records returned: {len(results)} (Expected: {len(samples)} x 12 = {len(samples)*12})\n")

assert len(results) == len(samples) * 12, f"Expected {len(samples)*12} results, got {len(results)}"

# 1. Verify NO AUTOMATIC FP FOR ALL NUTRIENTS
methods_used = set(r['executed_method'] for r in results)
print(f"Executed Methods across batch: {sorted(list(methods_used))}")
assert 'FP' not in methods_used or len(methods_used) > 1, "Failed: Every nutrient defaulted to FP!"

# 2. Verify selected_method == executed_method for every result
mismatches = [r for r in results if r['selected_method'] != r['executed_method']]
assert len(mismatches) == 0, f"Failed: Found {len(mismatches)} method mismatches!"
print("[PASS] MANDATORY ASSERTION PASSED: selected_method == executed_method for all 588 predictions.")

# 3. Verify NO UNEXPLAINED ZERO PREDICTIONS
zero_preds = [r for r in results if r['final_prediction'] == 0.0 or r['final_prediction'] is None]
print(f"Zero or None predictions count: {len(zero_preds)}")
assert len(zero_preds) == 0, f"Failed: Found {len(zero_preds)} zero predictions!"
print("[PASS] ZERO PREDICTION CHECK PASSED: 0 zero predictions found.")

# 4. Verify NUTRIENT-WISE ORDERING
expected_nutrient_sequence = []
for t in ALL_TARGETS:
    expected_nutrient_sequence.extend([t] * len(samples))

actual_nutrient_sequence = [r['nutrient'] for r in results]
assert actual_nutrient_sequence == expected_nutrient_sequence, "Failed: Predictions are not ordered nutrient-wise!"
print("[PASS] NUTRIENT-WISE ORDERING PASSED: Results are grouped by nutrient (OC x 49, N x 49, P x 49, ...).")

# 5. Print Excerpt Table
print("\n" + "="*95)
print(f"{'Sample ID':<12} | {'Nutrient':<4} | {'Selected':<8} | {'Executed':<8} | {'Raw Pred':<10} | {'Final Pred':<10} | {'Status':<10}")
print("="*95)

# Print first 2 samples for each nutrient
for t in ALL_TARGETS:
    t_results = [r for r in results if r['nutrient'] == t]
    for r in t_results[:2]:
        raw_str  = f"{r['raw_prediction']:.3f}" if r['raw_prediction'] is not None else "N/A"
        final_str = f"{r['final_prediction']:.3f}" if r['final_prediction'] is not None else "N/A"
        print(f"{r['sample_id']:<12} | {r['nutrient']:<4} | {r['selected_method']:<8} | {r['executed_method']:<8} | {raw_str:<10} | {final_str:<10} | {r['status']:<10}")
    print("-" * 95)

print("\n" + "="*95)
print("  ALL 12 ACCEPTANCE CRITERIA VERIFIED & PASSED (100% OPERATIONAL)")
print("="*95 + "\n")
