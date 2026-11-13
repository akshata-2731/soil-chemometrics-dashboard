import requests
import json
import pandas as pd

r = requests.get('http://127.0.0.1:5000/api/models')
models = r.json()

df = pd.read_excel('data/data.xlsx')
df.fillna(0, inplace=True)
samples = df.to_dict(orient='records')[:2]
for idx, s in enumerate(samples):
    s['Sample_ID'] = f"Sample_{idx+1:03d}"

results = []

for m in models:
    m_id = m['id']
    target = m_id.split('_')[0]
    
    mapping = {target: {'method_type': 'ml', 'method_id': m_id, 'calibration_required': False}}
    resp = requests.post('http://127.0.0.1:5000/api/batch/predict', json={
        'samples': samples,
        'targets': [target],
        'mapping': mapping
    })
    
    try:
        data = resp.json()['results'][0]
        results.append({
            'Nutrient': target,
            'Model ID': m_id,
            'Cal Required': data['calibration_required'],
            'Clamp Required': data['clamp_applied'],
            'Status': 'PASS',
            'Raw': data['raw_prediction'],
            'Final': data['final_prediction']
        })
    except Exception as e:
        results.append({
            'Nutrient': target,
            'Model ID': m_id,
            'Cal Required': '?',
            'Clamp Required': '?',
            'Status': 'FAIL',
            'Raw': str(e),
            'Final': '?'
        })

print(f"Total ML Models Tested: {len(results)}")
df_res = pd.DataFrame(results)
print(df_res.to_string())
