import requests

BASE_URL = "http://127.0.0.1:5000"

def test_predict(nutrient, method_id, cal_req):
    payload = {
        "samples": [{
            "Sample_ID": "TEST-001",
            "nm_410": 1000, "nm_435": 1100, "nm_460": 1200, "nm_485": 1300,
            "nm_510": 1400, "nm_535": 1500, "nm_560": 1600, "nm_585": 1700,
            "nm_610": 1800, "nm_645": 1900, "nm_680": 2000, "nm_705": 2100,
            "nm_730": 2200, "nm_760": 2300, "nm_810": 2400, "nm_860": 2500,
            "nm_900": 2600, "nm_940": 2700, "nm_320": 800,  "nm_280": 700,
            "nm_200": 600
        }],
        "targets": [nutrient],
        "mapping": {
            nutrient: {
                "method_type": "logic",
                "method_id": method_id,
                "calibration_required": cal_req
            }
        }
    }
    try:
        r = requests.post(f"{BASE_URL}/api/single/predict", json=payload)
        if r.status_code == 200:
            data = r.json()
            res = data.get("results", [{}])[0]
            status = res.get("status")
            if status and "FAILED" in status:
                return False
            return True
        return False
    except:
        return False

success_count = 0
failed = []
for i in range(1, 48):
    if test_predict("OC", f"M{i}", True):
        success_count += 1
    else:
        failed.append(f"M{i}")

print(f"Total Tested: 47")
print(f"Successful: {success_count}")
if failed:
    print(f"Failed: {failed}")
else:
    print("ALL 47 LOGICS VERIFIED SUCCESSFULLY!")
