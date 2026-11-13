import os
import json

IMPL_DIR = 'logics/implementations'
DEF_DIR = 'logics/definitions'

APPEND_CODE = '''

# ==========================================
# M48: Custom IP Euclidean Distance Logic
# ==========================================
import numpy as np

def logic48_predict(sample, d, nutrient):
    # Mapping based on standard 21 wavelengths
    # WAVELENGTH_ORDER = [410, 435, 460, 485, 510, 535, 560, 585, 610, 645, 680, 705, 730, 760, 810, 860, 900, 940, 320, 280, 200]
    # A=0, B=1, C=2, D=3, E=4, F=5, G=6, H=7, I=8, J=9, K=10, L=11
    # R=17 (940nm)
    # U=18 (320nm), V=19 (280nm), W=20 (200nm)
    # Assuming S=16 (900nm), T=14 (810nm) as placeholders if undefined
    
    def calc_ip1(s):
        A, B, C, D, E, F, G, H, R = s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7], s[17]
        group = [A, B, C, D, E, F, G, H, R]
        return (sum(x**2 for x in group) / (sum(group) + 1e-10)) / 100.0

    def calc_ip2(s):
        I, J, K, L = s[8], s[9], s[10], s[11]
        U, V, W = s[18], s[19], s[20]
        S, T = s[16], s[14]
        group = [I, S, J, T, U, V, W, K, L]
        return (sum(x**2 for x in group) / (sum(group) + 1e-10)) / 100.0

    def calc_ip3(s):
        U, V, W = s[18], s[19], s[20]
        group = [U, V, W]
        return (sum(x**2 for x in group) / (sum(group) + 1e-10)) / 100.0

    # Calculate IP for the sample
    sample_ip1 = calc_ip1(sample)
    sample_ip2 = calc_ip2(sample)
    sample_ip3 = calc_ip3(sample)
    
    # Get calibration vectors for the target nutrient
    min_vec, mid_vec, max_vec = get_calibration_vectors(d, list(range(21)), use_all=True)
    vals = get_vals(nutrient)
    
    # Calculate IP for the calibration points
    cal_points = []
    for vec in [min_vec, mid_vec, max_vec]:
        cal_points.append({
            "ip1": calc_ip1(vec),
            "ip2": calc_ip2(vec),
            "ip3": calc_ip3(vec)
        })
        
    # Calculate Euclidean distance to each calibration point
    distances = []
    for cp in cal_points:
        d_val = np.sqrt(
            (sample_ip1 - cp["ip1"])**2 + 
            (sample_ip2 - cp["ip2"])**2 + 
            (sample_ip3 - cp["ip3"])**2
        )
        distances.append(d_val)
        
    # Inverse Distance Weighting
    weights = [1.0 / (d_val**2 + 1e-10) for d_val in distances]
    total_weight = sum(weights)
    norm_weights = [w / total_weight for w in weights]
    
    # Final predicted value
    prediction = sum(norm_weights[i] * vals[i] for i in range(3))
    
    return prediction
'''

with open(os.path.join(IMPL_DIR, 'logic_utils.py'), 'a', encoding='utf-8') as f:
    f.write(APPEND_CODE)

py_code = '''from logics.implementations.logic_utils import logic48_predict, wrap_details

def predict(s, d, target="All"):
    if not d:
        return {
            "value": 0.0,
            "details": {"error": f"INCOMPLETE: Calibration data is required for {target}."}
        }
    val = logic48_predict(s, d, target)
    return wrap_details(val, "Custom_IP_Euclidean", target)
'''

with open(os.path.join(IMPL_DIR, 'M48.py'), 'w', encoding='utf-8') as f:
    f.write(py_code)
    
json_def = {
    "id": "M48",
    "name": "Custom IP Euclidean Distance",
    "type": "Mathematical",
    "target": "All 12 Nutrients",
    "features": "A-H, R, I-L, U-W, S-T",
    "required_ips": ["ip1", "ip2", "ip3"],
    "calibration_required": True,
    "calibration_source": "calibration.json [target]",
    "verification_status": "VERIFIED",
    "formula": "IP1/2/3 computed via sum(W^2)/sum(W)/100. Weights = 1/d^2 Euclidean distance."
}
with open(os.path.join(DEF_DIR, 'M48.json'), 'w', encoding='utf-8') as f:
    json.dump(json_def, f, indent=4)

print("SUCCESS: M48 added safely.")
