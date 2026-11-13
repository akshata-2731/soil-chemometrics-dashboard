import pandas as pd
from app import app
import warnings
warnings.filterwarnings('ignore')

df = pd.read_excel('data/data.xlsx')
samples = df.head(1).to_dict(orient='records')

print('========================================================')
print('TEST ALL 24 IMPLEMENTED PYTHON LOGICS')
print('========================================================')

logic_targets = {
    'M1': 'OC', 'M2': 'N', 'M3': 'P', 'M4': 'K', 'M5': 'K', 'M6': 'Ca', 'M7': 'Ca',
    'M8': 'Mg', 'M9': 'S', 'M10': 'Fe', 'M11': 'Mn', 'M12': 'Cu', 'M13': 'Zn', 'M14': 'B',
    'M15': 'OC', 'M16': 'OC', 'M17': 'S', 'M18': 'Fe', 'M19': 'Mn', 'M20': 'Cu',
    'M22': 'K', 'M23': 'Mg', 'M24': 'Zn', 'M25': 'N'
}

with app.test_client() as c:
    for m_id, t in logic_targets.items():
        m_logic = {t: {'method_type': 'logic', 'method_id': m_id, 'calibration_required': True}}
        r_logic = c.post('/api/batch/predict', json={'samples': samples, 'targets': [t], 'mapping': m_logic}).json
        
        for r in r_logic['results']:
            print(f"Logic ID: {m_id}")
            print(f"Target: {r['Target']}")
            print(f"Raw Prediction: {r.get('Raw_Prediction')}")
            print(f"Final Prediction: {r.get('Predicted')}")
            print(f"Min Limit: {r.get('Min_Limit')}")
            print(f"Max Limit: {r.get('Max_Limit')}")
            print(f"Clamp Applied: {r.get('Clamp_Applied')}")
            print(f"Status: {r['Status']}")
            print('-'*40)
