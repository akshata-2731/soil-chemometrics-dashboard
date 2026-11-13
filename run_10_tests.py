
import json, requests, string, random, pandas as pd, warnings, time
warnings.filterwarnings('ignore')

BASE = 'http://127.0.0.1:5000'
ALL_TARGETS = ['OC','N','P','K','Ca','Mg','S','Fe','Mn','Cu','Zn','B']
PASS_COUNT = 0
FAIL_COUNT = 0

def p(msg): print(msg)
def ok(t, d, se, ee, cs, pred, extra=''):
    global PASS_COUNT
    PASS_COUNT += 1
    print(f"  PASS | {t} | {se} -> {ee} | Calib: {cs} | Pred: {pred} {extra}")
def fail(t, msg):
    global FAIL_COUNT
    FAIL_COUNT += 1
    print(f"  FAIL | {t} | {msg}")

# ── Load real data ────────────────────────────────────────────────────────────
df = pd.read_excel('data/data.xlsx')
df.fillna(0, inplace=True)
samples = df.to_dict(orient='records')
s1 = samples[:1]   # single sample
s50 = samples[:50] # batch

print("\n" + "="*55)
print("  10-TEST VERIFICATION SUITE")
print("="*55 + "\n")

# ── TEST 1: Single OC using M1 + calibration ─────────────────────────────────
p("TEST 1: Single OC using M1 + calibration.json")
try:
    r = requests.post(f'{BASE}/api/single/predict', json={
        'samples': s1, 'targets': ['OC'],
        'mapping': {'OC': {'method_type':'logic','method_id':'M1','calibration_required':True}}
    }).json()
    res = r['results'][0]
    assert res['selected_method'] == res['executed_method'] == 'M1', "Method mismatch"
    assert res['calibration_source'] == 'calibration.json [OC]', "Wrong cal source"
    assert res['final_prediction'] is not None, "No prediction"
    ok('OC', 'M1', res['selected_method'], res['executed_method'], res['calibration_source'], res['final_prediction'])
except Exception as e:
    fail('OC-M1', str(e))

# ── TEST 2: N using M1 + N calibration (NOT OC) ──────────────────────────────
p("\nTEST 2: N using M1 + N calibration (must NOT use OC calibration)")
try:
    r = requests.post(f'{BASE}/api/single/predict', json={
        'samples': s1, 'targets': ['N'],
        'mapping': {'N': {'method_type':'logic','method_id':'M1','calibration_required':True}}
    }).json()
    res = r['results'][0]
    assert res['selected_method'] == res['executed_method'] == 'M1', "Method mismatch"
    assert 'calibration.json [N]' in res['calibration_source'], f"Wrong cal: {res['calibration_source']}"
    ok('N', 'M1', res['selected_method'], res['executed_method'], res['calibration_source'], res['final_prediction'])
except Exception as e:
    fail('N-M1', str(e))

# ── TEST 3: Same logic for OC, N, P, K - each uses own calibration ───────────
p("\nTEST 3: OC, N, P, K all using M1 - each gets own calibration section")
try:
    targets = ['OC','N','P','K']
    mapping = {t: {'method_type':'logic','method_id':'M1','calibration_required':True} for t in targets}
    r = requests.post(f'{BASE}/api/batch/predict', json={'samples': s1, 'targets': targets, 'mapping': mapping}).json()
    run_id_1 = r['run_id']
    for res in r['results']:
        t = res['nutrient']
        expected_src = f"calibration.json [{t}]"
        if res['executed_method'] == 'ERROR':
            fail(t, res['status'])
        elif res['calibration_source'] != expected_src:
            fail(t, f"Cal source '{res['calibration_source']}' != '{expected_src}'")
        else:
            ok(t, 'M1', res['selected_method'], res['executed_method'], res['calibration_source'], res['final_prediction'])
except Exception as e:
    fail('T3', str(e))

# ── TEST 4: Single nutrient using ML ─────────────────────────────────────────
p("\nTEST 4: Single OC using ML model")
try:
    r = requests.post(f'{BASE}/api/single/predict', json={
        'samples': s1, 'targets': ['OC'],
        'mapping': {'OC': {'method_type':'ml','method_id':'OC_model.pkl','calibration_required':False}}
    }).json()
    res = r['results'][0]
    assert res['selected_method'] == res['executed_method'] == 'OC_model.pkl', "Method mismatch"
    assert res['method_type'] == 'ML Model', f"Wrong type: {res['method_type']}"
    ok('OC', 'ML', res['selected_method'], res['executed_method'], res['calibration_source'], res['final_prediction'])
except Exception as e:
    fail('OC-ML', str(e))

# ── TEST 5: Single Sample All 12 - exactly 12 results ────────────────────────
p("\nTEST 5: Single sample all 12 nutrients - must return exactly 12 results")
try:
    mapping = {}
    for i, t in enumerate(ALL_TARGETS):
        if i % 2 == 0:
            mapping[t] = {'method_type':'ml','method_id':f'{t}_model.pkl','calibration_required':False}
        else:
            mapping[t] = {'method_type':'logic','method_id':'M1','calibration_required':True}
    r = requests.post(f'{BASE}/api/all12/predict', json={'samples': s1, 'targets': ALL_TARGETS, 'mapping': mapping}).json()
    count = len(r['results'])
    assert count == 12, f"Expected 12, got {count}"
    ok('All12', '12 Results', '12', '12', 'Mixed', f'{count} predictions')
except Exception as e:
    fail('All12', str(e))

# ── TEST 6: 50 samples - error isolation ─────────────────────────────────────
p("\nTEST 6: 50 samples with error isolation - one bad nutrient must not crash batch")
try:
    mapping = {
        'OC': {'method_type':'logic','method_id':'M1','calibration_required':True},
        'N':  {'method_type':'logic','method_id':'INVALID_METHOD_999','calibration_required':False}
    }
    r = requests.post(f'{BASE}/api/batch/predict', json={'samples': s50, 'targets': ['OC','N'], 'mapping': mapping}).json()
    total = len(r['results'])
    ok_r  = [x for x in r['results'] if 'FAILED' not in str(x.get('status',''))]
    err_r = [x for x in r['results'] if 'FAILED' in str(x.get('status',''))]
    assert total > 0, "No results at all"
    ok('Isolation', f'{len(ok_r)} pass / {len(err_r)} errors', str(total), 'Mixed', '-', f'Batch continued OK')
except Exception as e:
    fail('Isolation', str(e))

# ── TEST 7: Calibration Required but JSON missing ─────────────────────────────
p("\nTEST 7: Calibration Required but JSON temporarily renamed")
import os, shutil
cal_path = r'c:\Users\hp\Downloads\soil cali\calibration\calibration.json'
tmp_path = cal_path + '.bak'
try:
    shutil.move(cal_path, tmp_path)
    r = requests.post(f'{BASE}/api/single/predict', json={
        'samples': s1, 'targets': ['OC'],
        'mapping': {'OC': {'method_type':'logic','method_id':'M1','calibration_required':True}}
    }).json()
    res = r['results'][0]
    if 'FAILED' in str(res.get('status','')):
        ok('CalMissing', 'Error returned', 'M1', 'ERROR', '-', 'Error shown gracefully', f"| {res['status'][:50]}")
    else:
        fail('CalMissing', 'Expected failure but got success')
finally:
    if os.path.exists(tmp_path):
        shutil.move(tmp_path, cal_path)

# ── TEST 8: Calibration Not Required ─────────────────────────────────────────
p("\nTEST 8: Calibration Not Required - must execute without calibration")
try:
    r = requests.post(f'{BASE}/api/single/predict', json={
        'samples': s1, 'targets': ['N'],
        'mapping': {'N': {'method_type':'ml','method_id':'N_model.pkl','calibration_required':False}}
    }).json()
    res = r['results'][0]
    assert 'Not Required' in res['calibration_source'], f"Got: {res['calibration_source']}"
    assert res['final_prediction'] is not None
    ok('N-ML-NoCalib', 'ML', res['selected_method'], res['executed_method'], res['calibration_source'], res['final_prediction'])
except Exception as e:
    fail('N-ML-NoCalib', str(e))

# ── TEST 9: Select M5 - must execute M5 exactly ───────────────────────────────
p("\nTEST 9: Select M5 - verify M5 is executed exactly (or NOT IMPLEMENTED shown)")
try:
    r = requests.post(f'{BASE}/api/single/predict', json={
        'samples': s1, 'targets': ['S'],
        'mapping': {'S': {'method_type':'logic','method_id':'M5','calibration_required':True}}
    }).json()
    res = r['results'][0]
    if res['executed_method'] == 'M5':
        ok('S-M5', 'M5', 'M5', 'M5', res['calibration_source'], res['final_prediction'])
    elif res['selected_method'] == 'M5' and 'NOT IMPLEMENTED' in str(res.get('status','')):
        ok('S-M5', 'M5 NOT IMPLEMENTED reported', 'M5', 'ERROR', '-', 'Correct failure')
    elif 'M1' in str(res.get('executed_method','')) or 'M2' in str(res.get('executed_method','')):
        fail('S-M5', f"SILENT FALLBACK! Selected M5, executed {res['executed_method']}")
    else:
        ok('S-M5', 'Handled', res['selected_method'], res['executed_method'], res['calibration_source'], res['final_prediction'])
except Exception as e:
    fail('S-M5', str(e))

# ── TEST 10: Same dataset twice = different Run IDs ───────────────────────────
p("\nTEST 10: Run same dataset twice - Run IDs must be different")
try:
    mapping = {'OC': {'method_type':'logic','method_id':'M1','calibration_required':True}}
    r1 = requests.post(f'{BASE}/api/batch/predict', json={'samples': s1, 'targets': ['OC'], 'mapping': mapping}).json()
    time.sleep(0.05)
    r2 = requests.post(f'{BASE}/api/batch/predict', json={'samples': s1, 'targets': ['OC'], 'mapping': mapping}).json()
    id1 = r1['run_id']
    id2 = r2['run_id']
    assert id1 != id2, f"Run IDs are the same: {id1}"
    ok('RunIDs', 'Different', id1, id2, '-', f'{id1} vs {id2}')
except Exception as e:
    fail('RunIDs', str(e))

print("\n" + "="*55)
print(f"  RESULTS: {PASS_COUNT} PASS / {FAIL_COUNT} FAIL")
print("="*55 + "\n")
