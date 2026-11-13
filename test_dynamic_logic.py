import requests
import json
import time

BASE_URL = "http://127.0.0.1:5000"

print("1. Creating new custom logic M99 via API...")

new_logic_payload = {
    "id": "M99",
    "definition": {
        "name": "Custom Test Logic API",
        "target": "All 12 Nutrients",
        "type": "Mathematical",
        "features": "Dynamic per NUTRIENT_CONFIG",
        "calibration_required": True,
        "calibration_source": "calibration.json",
        "review_status": "Verified"
    },
    "implementation": '''from logics.implementations.logic_utils import wrap_details

def predict(s, d, target="All"):
    # Custom test calculation
    test_value = 999.99
    return wrap_details(test_value, "Custom_Test_M99", target)
'''
}

r_create = requests.post(f"{BASE_URL}/api/logics", json=new_logic_payload)
print("Create Status:", r_create.status_code, r_create.text)

time.sleep(1) # wait for filesystem sync

print("2. Testing M99 in prediction engine...")

predict_payload = {
    "samples": [{
        "Sample_ID": "TEST-001",
        "nm_410": 1000, "nm_435": 1100, "nm_460": 1200, "nm_485": 1300,
        "nm_510": 1400, "nm_535": 1500, "nm_560": 1600, "nm_585": 1700,
        "nm_610": 1800, "nm_645": 1900, "nm_680": 2000, "nm_705": 2100,
        "nm_730": 2200, "nm_760": 2300, "nm_810": 2400, "nm_860": 2500,
        "nm_900": 2600, "nm_940": 2700, "nm_320": 800,  "nm_280": 700,
        "nm_200": 600
    }],
    "targets": ["OC"],
    "mapping": {
        "OC": {
            "method_type": "logic",
            "method_id": "M99",
            "calibration_required": True
        }
    }
}

r_predict = requests.post(f"{BASE_URL}/api/single/predict", json=predict_payload)
if r_predict.status_code == 200:
    data = r_predict.json()
    res = data.get("results", [{}])[0]
    print(f"Prediction Result for M99 -> OC:")
    print(f"Status: {res.get('status')}")
    print(f"Final Prediction: {res.get('final_prediction')}")
    print(f"Detailed Steps:")
    for k, v in res.get("detailed_steps", {}).items():
        print(f"  {k}: {v}")
else:
    print("Prediction Failed:", r_predict.status_code, r_predict.text)

# 3. Clean up
import os
try:
    os.remove("logics/definitions/M99.json")
    os.remove("logics/implementations/M99.py")
    print("3. Cleaned up M99 test files.")
except:
    pass
