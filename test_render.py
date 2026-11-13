import requests
import json

url = 'https://soil-chemometrics-dashboard.onrender.com/api/models/multi-eval'
print("Calling:", url)

with open('data.xlsx', 'rb') as f:
    files = {'file': ('data.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
    data = {
        'mode': 'custom',
        'methods': json.dumps([{'id': 'B01_PLSR', 'type': 'ml', 'name': 'B01_PLSR'}]),
        'targets': json.dumps(['ALL']),
        'pass_threshold': '75',
        'dataset_type': 'new_test'
    }
    resp = requests.post(url, files=files, data=data, timeout=60)
    print('STATUS:', resp.status_code)
    print('CONTENT-TYPE:', resp.headers.get('content-type'))
    print('TEXT:', resp.text[:1000])
