import requests

with open('data/data.xlsx', 'rb') as f:
    r = requests.post('http://localhost:5000/api/models/multi-eval', 
                      data={'mode': 'all_ml', 'targets': '["OC", "N", "Mg"]', 'pass_threshold': 70.0},
                      files={'file': f})
d = r.json()
print('Total summary combinations:', len(d.get('summary', [])))
print('Returned results length:', len(d.get('results', [])))
sample_combos = set((r['nutrient'], r['method_id']) for r in d.get('results', []))
print('Unique (nutrient, method) in results payload:', len(sample_combos))
mg_models = [r['method_id'] for r in d.get('results', []) if r['nutrient'] == 'Mg']
print('Number of Mg predictions returned in results:', len(mg_models))
