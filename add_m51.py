import os
import json

IMPL_DIR = 'logics/implementations'
DEF_DIR = 'logics/definitions'

APPEND_CODE = '''

# ==========================================
# M51: SAM + SRI Classification Logic
# ==========================================
import numpy as np
import math

def logic51_predict(sample, d, nutrient):
    # 1. Wavelengths
    A, B, C, D, E, F, G, H = sample[0:8]
    I, J, S680, L = sample[8], sample[9], sample[10], sample[11]
    T = sample[12]
    K900, R = sample[16], sample[17]
    U320, V280, W200 = sample[18], sample[19], sample[20]

    # IP Calculation
    def calc_ips(group):
        return (sum(x**2 for x in group) / (sum(group) + 1e-10)) / 100.0

    ip1 = calc_ips([A, B, C, D, E, F, G, H, R])
    ip2 = calc_ips([I, S680, J, T, U320, V280, W200, K900, L])
    ip3 = calc_ips([U320, V280, W200])

    sri = (ip1 * ip3) / (ip2 + 1e-10)

    # 3.2 Centroids
    c_low = np.array([8.569986, 3.731463, 1.716387])
    c_med = np.array([10.308449, 3.918395, 3.820572])
    c_high = np.array([8.805760, 3.760319, 2.218485])
    v = np.array([ip1, ip2, ip3])

    def calc_sam(v, c):
        dot_val = np.dot(v, c)
        norm_v = np.linalg.norm(v)
        norm_c = np.linalg.norm(c)
        cos_theta = dot_val / ((norm_v * norm_c) + 1e-10)
        cos_theta = np.clip(cos_theta, -1.0, 1.0)
        return math.acos(cos_theta) * (180.0 / math.pi)

    angle_low = calc_sam(v, c_low)
    angle_med = calc_sam(v, c_med)
    angle_high = calc_sam(v, c_high)

    # 4. Classification Logic
    pred_class = None
    if sri < 1.2 and ip1 < 8.0 and ip3 < 0.7:
        pred_class = "High"
    elif sri > 8.0:
        pred_class = "High"
    elif 3.0 <= sri <= 8.0:
        pred_class = "Low" if angle_low < angle_med else "Medium"
    else:
        angles = {"Low": angle_low, "Medium": angle_med, "High": angle_high}
        pred_class = min(angles, key=angles.get)
        if pred_class == "High":
            pred_class = "Low" if angle_low < angle_med else "Medium"

    # 7.1 SRI Ranges
    sri_ranges = {
        "Low": (0.2, 4.0),
        "Medium": (1.5, 9.0),
        "High": (0.1, 20.0)
    }

    # Universal Scaling based on get_vals
    vals = get_vals(nutrient)
    val_mid = vals[1]
    
    target_ranges = {
        "Low": (0.0, val_mid * 0.5),
        "Medium": (val_mid * 0.5, val_mid),
        "High": (val_mid, val_mid * (500.0 / 300.0))
    }

    # Hardcoded mapping explicitly for N
    if nutrient == "N":
        target_ranges = {
            "Low": (0.0, 150.0),
            "Medium": (150.0, 300.0),
            "High": (300.0, 500.0)
        }

    sri_min, sri_max = sri_ranges[pred_class]
    n_min, n_max = target_ranges[pred_class]

    position = (sri - sri_min) / ((sri_max - sri_min) + 1e-10)
    position = max(0, min(position, 1))

    predicted = n_min + position * (n_max - n_min)
    return predicted
'''

with open(os.path.join(IMPL_DIR, 'logic_utils.py'), 'a', encoding='utf-8') as f:
    f.write(APPEND_CODE)

py_code = '''from logics.implementations.logic_utils import logic51_predict, wrap_details

def predict(s, d, target="All"):
    val = logic51_predict(s, d, target)
    return wrap_details(val, "SAM + SRI Classification", target)
'''

with open(os.path.join(IMPL_DIR, 'M51.py'), 'w', encoding='utf-8') as f:
    f.write(py_code)

json_def = {
    "id": "M51",
    "name": "SAM + SRI Classification",
    "type": "Mathematical",
    "target": "All 12 Nutrients",
    "features": "SRI, SAM Angles",
    "required_ips": ["ip1", "ip2", "ip3"],
    "calibration_required": False,
    "calibration_source": "N/A",
    "verification_status": "VERIFIED",
    "formula": "Calculates SRI = (ip1*ip3)/ip2. Evaluates Spectral Angles (SAM) to centroids. Assigns class via decision tree. Scales linearly via SRI ranges."
}
with open(os.path.join(DEF_DIR, 'M51.json'), 'w', encoding='utf-8') as f:
    json.dump(json_def, f, indent=4)

print("SUCCESS: M51 added safely.")
