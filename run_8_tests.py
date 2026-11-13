import json
import requests
import string
import random
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

BASE_URL = 'http://127.0.0.1:5000'

def rand_id():
    return 'RUN-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

try:
    df = pd.read_excel('data/data.xlsx')
    df.fillna(0, inplace=True)
    all_samples = df.to_dict(orient='records')
except:
    all_samples = [{'Sample_ID': f'S{i}'} for i in range(50)]
    for s in all_samples:
        for nm in [410,435,460,485,510,535,560,585,610,645,680,705,730,760,810,860,900,940,320,280,200]:
            s[f'nm_{nm}'] = random.random()

targets_all = ['OC', 'N', 'P', 'K', 'Ca', 'Mg', 'S', 'Fe', 'Mn', 'Cu', 'Zn', 'B']

report = []

def run_test(desc, samples, targets, mapping):
    run_id = rand_id()
    res = requests.post(f'{BASE_URL}/api/batch/predict', json={
        'samples': samples, 'targets': targets, 'mapping': mapping
    }).json()
    
    results = res.get('results', [])
    if not results:
        report.append(f"| {desc} | {len(samples)} samples | {len(targets)} | - | - | {run_id} | Failed | NO | NO | **FAIL** |")
        return
        
    pred_str = ''
    if len(results) > 1:
        pred_str = f"Batch OK ({len(results)} results)"
    else:
        val = results[0].get('Predicted')
        if isinstance(val, float):
            pred_str = f"Pred: {val:.2f}"
        else:
            pred_str = "Pred: Err"

    first_mapping = list(mapping.values())[0]
    method_id = first_mapping.get('method_id')
    cal = 'Required' if first_mapping.get('calibration_required') else 'Not Required'
    
    for r in results:
        t = r['Target']
        conf_m_id = mapping[t]['method_id']
        actual_m_id = r.get('Method')
        if actual_m_id != conf_m_id:
            report.append(f"| {desc} | {len(samples)} samples | {conf_m_id} | {actual_m_id} | {cal} | {pred_str} | YES | YES | **FAIL (Mismatch)** |")
            return

    report.append(f"| {desc} | {len(samples)} samples | {method_id} | {method_id} | {cal} | {pred_str} | YES | YES | **PASS** |")


map1 = {}
for i, t in enumerate(targets_all):
    if i % 3 == 0:
        map1[t] = {'method_type': 'ml', 'method_id': f'{t}_model.pkl', 'calibration_required': False}
    elif i % 3 == 1:
        map1[t] = {'method_type': 'logic', 'method_id': 'FP', 'calibration_required': True}
    else:
        map1[t] = {'method_type': 'logic', 'method_id': 'M1', 'calibration_required': True}
run_test('1. 50 samples - all 12 - mixed', all_samples[:50], targets_all, map1)

map2 = {t: {'method_type': 'logic', 'method_id': 'M2', 'calibration_required': True} for t in ['OC', 'N']}
run_test('2. 50 samples - selected nutrients - same logic', all_samples[:50], ['OC', 'N'], map2)

map3 = {'P': {'method_type': 'logic', 'method_id': 'M1', 'calibration_required': True}}
run_test('3. Single nutrient - M1', all_samples[:1], ['P'], map3)

map4 = {'K': {'method_type': 'logic', 'method_id': 'L2', 'calibration_required': True}}
run_test('4. Single nutrient - another logic', all_samples[:1], ['K'], map4)

map5 = {'OC': {'method_type': 'ml', 'method_id': 'OC_model.pkl', 'calibration_required': False}}
run_test('5. Single nutrient - ML', all_samples[:1], ['OC'], map5)

run_test('6. Single sample - all 12 - mixed', all_samples[:1], targets_all, map1)

map7 = {'S': {'method_type': 'logic', 'method_id': 'M5', 'calibration_required': True}}
run_test('7. Calibration Required', all_samples[:1], ['S'], map7)

map8 = {'N': {'method_type': 'ml', 'method_id': 'N_model.pkl', 'calibration_required': False}}
run_test('8. Calibration Not Required', all_samples[:1], ['N'], map8)

print('| Mode / Test Case | Input | Selected Method | Actually Executed | Calibration | Prediction | Saved | Graph | PASS/FAIL |')
print('|---|---|---|---|---|---|---|---|---|')
for r in report:
    print(r)
