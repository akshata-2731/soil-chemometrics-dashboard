import os, sys, json, importlib.util, math, time, glob
import numpy as np
import pandas as pd
import requests

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

df = pd.read_excel('data/data.xlsx')
df.fillna(0, inplace=True)
S = df.to_dict(orient='records')
S1 = S[0]

WAVELENGTH_ORDER = [410,435,460,485,510,535,560,585,610,645,680,705,730,760,810,860,900,940,320,280,200]
FEATURE_NAMES    = ['nm_' + str(w) for w in WAVELENGTH_ORDER]
ALL_TARGETS      = ['OC','N','P','K','Ca','Mg','S','Fe','Mn','Cu','Zn','B']
BASE             = 'http://127.0.0.1:5000'

with open('calibration/calibration.json', 'r', encoding='utf-8') as f:
    ALL_CAL = json.load(f)

LOGICS_DEF  = 'logics/definitions'
LOGICS_IMPL = 'logics/implementations'
MODELS_DIR  = 'models'

def_files = sorted(glob.glob(os.path.join(LOGICS_DEF, '*.json')))
all_logics = []
for fp in def_files:
    with open(fp, 'r') as f:
        d = json.load(f)
    lid = d.get('id') or d.get('logic_id') or d.get('method_id') or os.path.splitext(os.path.basename(fp))[0]
    d['id'] = lid
    impl = os.path.join(LOGICS_IMPL, lid + '.py')
    d['_implemented'] = os.path.exists(impl)
    all_logics.append(d)

implemented = [l for l in all_logics if l['_implemented']]
not_impl    = [l for l in all_logics if not l['_implemented']]

print("=" * 70)
print("  DEEP LOGIC ENGINE VERIFICATION")
print("=" * 70)
print(f"Total Logic definitions : {len(all_logics)}")
print(f"IMPLEMENTED             : {len(implemented)}")
print(f"NOT IMPLEMENTED         : {len(not_impl)}")
print(f"Implemented IDs : {', '.join(l['id'] for l in implemented)}")
print(f"NOT impl IDs    : {', '.join(l['id'] for l in not_impl)}")

def get_wvs(sample):
    return [float(sample.get('nm_' + str(w), sample.get(str(w), 0))) for w in WAVELENGTH_ORDER]

WVS = get_wvs(S1)

def run_logic_local(logic_id, wvs, cal_data):
    impl_path = os.path.join(LOGICS_IMPL, logic_id + '.py')
    spec = importlib.util.spec_from_file_location(logic_id, impl_path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return float(mod.predict(wvs, cal_data))

print("\n" + "=" * 70)
print("  SECTION 1 - M1 FORMULA TRACE")
print("=" * 70)

def m1_trace(wvs, cal, nutrient):
    mn = cal.get('min', [])
    md = cal.get('mid', [])
    mx = cal.get('max', [])
    vs = cal.get('vals', [0,0,0])
    n  = len(mn)
    dm = math.sqrt(sum((wvs[i]-mn[i])**2 for i in range(n)))
    dd = math.sqrt(sum((wvs[i]-md[i])**2 for i in range(n)))
    dx = math.sqrt(sum((wvs[i]-mx[i])**2 for i in range(n)))
    eps = 1e-10
    wm = 1/(dm+eps); wd = 1/(dd+eps); wx = 1/(dx+eps)
    result = (wm*vs[0] + wd*vs[1] + wx*vs[2]) / (wm+wd+wx)
    print(f"\n  {nutrient}:")
    print(f"    vals (reference values) : {vs}")
    print(f"    min spectrum len        : {len(mn)}")
    print(f"    d(sample, MIN)          : {dm:.6f}")
    print(f"    d(sample, MID)          : {dd:.6f}")
    print(f"    d(sample, MAX)          : {dx:.6f}")
    print(f"    w_min={wm:.6e}  w_mid={wd:.6e}  w_max={wx:.6e}")
    print(f"    IDW weighted result     : {result:.6f}")
    return result

for t in ['OC', 'N', 'P', 'K', 'S']:
    if t in ALL_CAL and ALL_CAL[t].get('min') and ALL_CAL[t].get('mid'):
        m1_trace(WVS, ALL_CAL[t], f"M1 -> {t}")

print("\n" + "=" * 70)
print("  SECTION 2 - ALL IMPLEMENTED LOGICS x ALL NUTRIENTS")
print("=" * 70)

PASS = 0
FAIL = 0
REPORT = []

def test_logic_nutrient(logic_id, nutrient, wvs, cal_override=None):
    global PASS, FAIL
    cal_data = cal_override or ALL_CAL.get(nutrient, None)
    cal_section = f"calibration[{nutrient}]" if cal_data else "None"

    try:
        pred_local = run_logic_local(logic_id, wvs, cal_data)

        r = requests.post(f"{BASE}/api/single/predict", json={
            "samples": [S1],
            "targets": [nutrient],
            "mapping": {nutrient: {"method_type": "logic", "method_id": logic_id, "calibration_required": bool(cal_data)}}
        }, timeout=10).json()

        api_res = r['results'][0]
        api_sel = api_res.get('selected_method', '')
        api_exe = api_res.get('executed_method', '')
        api_cal = api_res.get('calibration_source', '')
        api_pred = api_res.get('final_prediction', None)

        if api_exe == 'ERROR':
            status = str(api_res.get('status',''))
            FAIL += 1
            REPORT.append({'Logic': logic_id, 'Nutrient': nutrient, 'Selected': logic_id,
                           'Executed': api_exe, 'Cal': cal_section, 'LocalPred': f"{pred_local:.4f}",
                           'APIPred': 'ERROR', 'RESULT': f"FAIL: {status[:40]}"})
            return
        if api_sel != api_exe:
            FAIL += 1
            REPORT.append({'Logic': logic_id, 'Nutrient': nutrient, 'Selected': api_sel,
                           'Executed': api_exe, 'Cal': cal_section, 'LocalPred': f"{pred_local:.4f}",
                           'APIPred': str(api_pred), 'RESULT': "FAIL: method mismatch"})
            return

        if cal_data and f"[{nutrient}]" not in api_cal:
            FAIL += 1
            REPORT.append({'Logic': logic_id, 'Nutrient': nutrient, 'Selected': logic_id,
                           'Executed': api_exe, 'Cal': f"WRONG: {api_cal}", 'LocalPred': f"{pred_local:.4f}",
                           'APIPred': str(api_pred), 'RESULT': "FAIL: wrong calibration section"})
            return

        p_str = f"{api_pred:.4f}" if api_pred is not None else "N/A"
        PASS += 1
        REPORT.append({'Logic': logic_id, 'Nutrient': nutrient, 'Selected': logic_id,
                       'Executed': api_exe, 'Cal': cal_section,
                       'LocalPred': f"{pred_local:.4f}", 'APIPred': p_str,
                       'RESULT': 'PASS'})

    except Exception as e:
        FAIL += 1
        REPORT.append({'Logic': logic_id, 'Nutrient': nutrient, 'Selected': logic_id,
                       'Executed': 'EXCEPTION', 'Cal': cal_section, 'LocalPred': 'ERR',
                       'APIPred': 'ERR', 'RESULT': f"FAIL: {str(e)[:60]}"})

for logic in implemented:
    lid = logic['id']
    cal_req = logic.get('calibration_required', True)
    for nutrient in ALL_TARGETS:
        if cal_req and nutrient not in ALL_CAL:
            continue
        test_logic_nutrient(lid, nutrient, WVS, ALL_CAL.get(nutrient) if cal_req else None)

print("\n" + "=" * 70)
print("  SECTION 3 - NO-FALLBACK GUARANTEE")
print("=" * 70)

NOT_IMPL_ID = not_impl[0]['id'] if not_impl else 'NONEXISTENT_M99'
r = requests.post(f"{BASE}/api/single/predict", json={
    "samples": [S1], "targets": ["OC"],
    "mapping": {"OC": {"method_type": "logic", "method_id": NOT_IMPL_ID, "calibration_required": False}}
}, timeout=10).json()
res = r['results'][0]
exe = res.get('executed_method', '')
status = res.get('status', '')
if exe == 'ERROR':
    print(f"  PASS | Selected: {NOT_IMPL_ID} | Executed: ERROR | Status: {status[:60]}")
    PASS += 1
else:
    print(f"  FAIL | Selected: {NOT_IMPL_ID} | Executed: {exe}")
    FAIL += 1

print("\n" + "=" * 70)
print("  SECTION 4 - ML MODEL VERIFICATION")
print("=" * 70)

import joblib
pkl_files = sorted(glob.glob(os.path.join(MODELS_DIR, '*.pkl')))
for pf in pkl_files:
    bn = os.path.basename(pf)
    target = bn.split('_')[0]
    try:
        r = requests.post(f"{BASE}/api/single/predict", json={
            "samples": [S1], "targets": [target],
            "mapping": {target: {"method_type": "ml", "method_id": bn, "calibration_required": False}}
        }, timeout=10).json()
        res = r['results'][0]
        sel = res.get('selected_method','')
        exe = res.get('executed_method','')
        pred = res.get('final_prediction')
        p_str = f"{pred:.4f}" if pred is not None else "ERR"
        ok = (sel == exe == bn and pred is not None)
        print(f"  {bn:<20} | Selected={sel} | Executed={exe} | Pred={p_str} | {'PASS' if ok else 'FAIL'}")
        if ok: PASS += 1
        else: FAIL += 1
    except Exception as e:
        print(f"  {bn}: ERROR - {e}")
        FAIL += 1

print("\n" + "=" * 70)
print("  SECTION 5 - RUN ID UNIQUENESS")
print("=" * 70)

mapping_oc = {"OC": {"method_type": "logic", "method_id": "M1", "calibration_required": True}}
r1 = requests.post(f"{BASE}/api/single/predict", json={"samples":[S1],"targets":["OC"],"mapping":mapping_oc}).json()
time.sleep(0.05)
r2 = requests.post(f"{BASE}/api/single/predict", json={"samples":[S1],"targets":["OC"],"mapping":mapping_oc}).json()
id1 = r1.get('run_id','')
id2 = r2.get('run_id','')
ok  = id1 != id2 and id1 and id2
print(f"  Run 1: {id1}")
print(f"  Run 2: {id2}")
print(f"  Run IDs different: {'YES - PASS' if ok else 'NO - FAIL'}")
if ok: PASS += 1
else: FAIL += 1

print("\n" + "=" * 70)
print("  SECTION 6 - BATCH ERROR ISOLATION")
print("=" * 70)

samples_20 = S[:20]
invalid_sample = {"Sample_ID": "INVALID_SAMPLE_XXX"}
samples_with_bad = samples_20 + [invalid_sample]

mapping_batch = {
    "OC": {"method_type": "logic", "method_id": "M1", "calibration_required": True},
    "N":  {"method_type": "logic", "method_id": "NONEXISTENT_ZZZ", "calibration_required": False}
}
r = requests.post(f"{BASE}/api/batch/predict", json={
    "samples": samples_with_bad, "targets": ["OC","N"], "mapping": mapping_batch
}, timeout=30).json()

total  = len(r.get('results', []))
passed = [x for x in r['results'] if 'FAILED' not in str(x.get('status',''))]
errors = [x for x in r['results'] if 'FAILED' in str(x.get('status',''))]
print(f"  Samples sent  : {len(samples_with_bad)}")
print(f"  Total results : {total}")
print(f"  Successful    : {len(passed)}")
print(f"  Errors        : {len(errors)}")
print(f"  Batch continued despite errors: {'PASS' if len(passed) > 0 and len(errors) > 0 else 'FAIL'}")
if passed: PASS += 1

print("\n" + "=" * 70)
print("  SECTION 7 - SINGLE SAMPLE ALL 12 NUTRIENTS")
print("=" * 70)

mapping_12 = {t: {"method_type": "logic", "method_id": "M1", "calibration_required": True} for t in ALL_TARGETS}
r = requests.post(f"{BASE}/api/all12/predict", json={"samples":[S1],"targets":ALL_TARGETS,"mapping":mapping_12}, timeout=30).json()
count = len(r.get('results', []))
print(f"  Expected: 12  |  Received: {count}  |  {'PASS' if count==12 else 'FAIL'}")
if count == 12: PASS += 1
else: FAIL += 1

print("\n" + "=" * 70)
print("  TOTAL VERIFICATION SUMMARY")
print("=" * 70)
print(f"  TOTAL CHECKS: {PASS} PASS / {FAIL} FAIL")
print("=" * 70 + "\n")
