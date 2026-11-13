import requests
import json
import pandas as pd

# 1. Fetch all logics
r = requests.get('http://127.0.0.1:5000/api/logics')
logics = r.json()

# 2. Get samples
df = pd.read_excel('data/data.xlsx')
df.fillna(0, inplace=True)
samples = df.to_dict(orient='records')[:2] # take 2 samples
for idx, s in enumerate(samples):
    s['Sample_ID'] = f"Sample_{idx+1:03d}"

results = []

# test all mathematical logics
for l in logics:
    l_id = l['id']
    if l['status'] != 'Implemented':
        continue
    
    mapping = {'OC': {'method_type': 'logic', 'method_id': l_id, 'calibration_required': False}} # cal will be auto-determined
    resp = requests.post('http://127.0.0.1:5000/api/batch/predict', json={
        'samples': samples,
        'targets': ['OC'],
        'mapping': mapping
    })
    
    try:
        data = resp.json()['results'][0]
        results.append({
            'Logic ID': l_id,
            'Name': l['name'],
            'Cal Required': data['calibration_required'],
            'Clamp Required': data['clamp_applied'],
            'Status': 'PASS',
            'Raw': data['raw_prediction']
        })
    except Exception as e:
        results.append({
            'Logic ID': l_id,
            'Name': l['name'],
            'Cal Required': '?',
            'Clamp Required': '?',
            'Status': 'FAIL',
            'Raw': str(e)
        })

print(f"Total Logics Tested: {len(results)}")
df_res = pd.DataFrame(results)
print(df_res.to_string())
