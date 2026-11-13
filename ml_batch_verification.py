import pandas as pd
import requests

df = pd.read_excel('data/data.xlsx')
df.fillna(0, inplace=True)
samples = df.to_dict(orient='records')
for idx, s in enumerate(samples):
    s['Sample_ID'] = f"Sample_{idx+1:03d}"

ALL_TARGETS = ['OC']
mapping = {
    'OC': {'method_type': 'ml', 'method_id': 'B24_Heterogeneous_TwoStage/OC_model.pkl', 'calibration_required': False}
}

url = 'http://127.0.0.1:5000/api/batch/predict'
response = requests.post(url, json={
    'samples': samples[:5],
    'targets': ALL_TARGETS,
    'mapping': mapping
})

for r in response.json()['results']:
    actual_val = r.get('actual', 'N/A')
    if isinstance(actual_val, float):
        actual_val = f"{actual_val:.3f}"
        
    print(f"Sample: {r['sample_id']} | Value: {actual_val} vs {r['final_prediction']:.3f} | Class: {r.get('actual_class', 'N/A')} vs {r.get('predicted_class', 'N/A')}")
