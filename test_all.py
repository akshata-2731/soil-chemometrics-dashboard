import pandas as pd
from app import app
import warnings
warnings.filterwarnings('ignore')

df = pd.read_excel('data/data.xlsx')
samples = df.head(1).to_dict(orient='records')

TARGETS = ['OC', 'N', 'P', 'K', 'Ca', 'Mg', 'S', 'Fe', 'Mn', 'Cu', 'Zn', 'B']

with app.test_client() as c:
    print('========================================================')
    print('1. ML MODELS VERIFICATION')
    print('========================================================')
    m_ml = {t: {'method_type': 'ml', 'method_id': f'{t}_model.pkl', 'calibration_required': False} for t in TARGETS}
    r_ml = c.post('/api/batch/predict', json={'samples': samples, 'targets': TARGETS, 'mapping': m_ml}).json
    for r in r_ml['results']:
        print(f"Target: {r['Target']}")
        print(f"Method: {r['Method']}")
        print(f"Method Type: ML Model")
        print(f"Raw Prediction: {r.get('Raw_Prediction')}")
        print(f"Final Prediction: {r.get('Predicted')}")
        print(f"Min Limit: {r.get('Min_Limit')}")
        print(f"Max Limit: {r.get('Max_Limit')}")
        print(f"Status: {r['Status']}")
        print(f"Calibration: {r['Calibration']}")
        print('-'*40)

    print('========================================================')
    print('2. PYTHON LOGICS VERIFICATION')
    print('========================================================')
    
    logic_map = {
        'OC': 'M1', 'N': 'M2', 'P': 'M3', 'K': 'M4',
        'Ca': 'M6', 'Mg': 'M8', 'S': 'M9', 'Fe': 'M10',
        'Mn': 'M11', 'Cu': 'M12', 'Zn': 'M13', 'B': 'M14'
    }
    m_logic = {t: {'method_type': 'logic', 'method_id': logic_map[t], 'calibration_required': True} for t in TARGETS}
    r_logic = c.post('/api/batch/predict', json={'samples': samples, 'targets': TARGETS, 'mapping': m_logic}).json
    for r in r_logic['results']:
        print(f"Target: {r['Target']}")
        print(f"Method: {r['Method']}")
        print(f"Method Type: Logic")
        print(f"Raw Prediction: {r.get('Raw_Prediction')}")
        print(f"Final Prediction: {r.get('Predicted')}")
        print(f"Min Limit: {r.get('Min_Limit')}")
        print(f"Max Limit: {r.get('Max_Limit')}")
        print(f"Status: {r['Status']}")
        print(f"Calibration: {r['Calibration']}")
        print('-'*40)
