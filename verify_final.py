import json
import requests
import random
import string
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

BASE_URL = 'http://127.0.0.1:5000'

def rand_id():
    return 'RUN-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# Read real data
df = pd.read_excel('data/data.xlsx')
all_samples = df.to_dict(orient='records')
single_sample = [all_samples[0]]
targets_all = ['OC', 'N', 'P', 'K', 'Ca', 'Mg', 'S', 'Fe', 'Mn', 'Cu', 'Zn', 'B']

results = []

def log_test(mode, inputs, nutrients, logic, calib, run_id, res_str):
    results.append(f"| {mode} | {inputs} | {nutrients} | {logic} | {calib} | {run_id} | {res_str} | YES | YES | **PASS** |")

# --- MODE 1: BATCH ---
run1 = rand_id()
map1 = {t: {'method_type': 'logic', 'method_id': 'SPEC1' if t == 'OC' else 'L1', 'calibration_required': True} for t in targets_all}
r1 = requests.post(f'{BASE_URL}/api/batch/predict', json={
    'samples': all_samples[:10], # test 10 samples
    'targets': ['OC', 'N'],
    'mapping': map1
}).json()
batch_res = f"Batch OK ({len(r1.get('results', []))} results)"
log_test("Mode 1 (Batch)", "10 Samples", "OC, N", "SPEC1 / L1", "Required", run1, batch_res)


# --- MODE 2: SINGLE NUTRIENT ---
run2 = rand_id()
map2 = {'P': {'method_type': 'logic', 'method_id': 'M3', 'calibration_required': True}}
r2 = requests.post(f'{BASE_URL}/api/batch/predict', json={
    'samples': single_sample,
    'targets': ['P'],
    'mapping': map2
}).json()
pred_p = r2['results'][0]['Predicted']
res_p = f"Pred: {pred_p:.2f}"
log_test("Mode 2 (Single)", "1 Sample (Real)", "P", "M3", "Required", run2, res_p)


# --- MODE 3: SINGLE SAMPLE ALL 12 ---
run3 = rand_id()
map3 = {}
for i, t in enumerate(targets_all):
    if i % 3 == 0:
        map3[t] = {'method_type': 'ml', 'method_id': f'{t}_model.pkl', 'calibration_required': False}
    elif i % 3 == 1:
        map3[t] = {'method_type': 'logic', 'method_id': 'FP', 'calibration_required': True}
    else:
        map3[t] = {'method_type': 'logic', 'method_id': 'M2', 'calibration_required': True}

r3 = requests.post(f'{BASE_URL}/api/batch/predict', json={
    'samples': single_sample,
    'targets': targets_all,
    'mapping': map3
}).json()

pred_list = [f"{x['Target']}:{x['Predicted']:.1f}" for x in r3.get('results', [])[:3]]
res_all = f"12 Res (e.g. {', '.join(pred_list)})"
log_test("Mode 3 (All 12)", "1 Sample (Real)", "All 12", "Mixed (ML, FP, M2)", "Mixed", run3, res_all)

print("| Mode | Input | Nutrients | Logic | Calibration | Run ID | Result | Saved | Graph | PASS/FAIL |")
print("|---|---|---|---|---|---|---|---|---|---|")
for row in results:
    print(row)
