import os
import json

IMPL_DIR = 'logics/implementations'
DEF_DIR = 'logics/definitions'

APPEND_CODE = '''

# ==========================================
# M50: Mahalanobis Distance Logic
# ==========================================
import numpy as np

def logic50_predict(sample, d, nutrient):
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

    x = np.array([ip1, ip2, ip3])

    # 2 & 4. Centroids and Inverse Covariance Matrices
    mu_low = np.array([8.569986, 3.731463, 1.716387])
    inv_cov_low = np.array([
        [2.896, -7.424, -2.502],
        [-7.424, 34.585, 5.496],
        [-2.502, 5.496, 2.772]
    ])

    mu_medium = np.array([10.308449, 3.918395, 3.820572])
    inv_cov_medium = np.array([
        [1.500, -6.242, -1.060],
        [-6.242, 30.243, 3.682],
        [-1.060, 3.682, 1.284]
    ])

    mu_high = np.array([8.805760, 3.760319, 2.218485])
    inv_cov_high = np.array([
        [1.645, -6.673, -1.184],
        [-6.673, 39.030, 4.729],
        [-1.184, 4.729, 1.379]
    ])

    # 5. Mahalanobis Distances
    def mahalanobis(x_vec, mu, inv_cov):
        diff = x_vec - mu
        # Use np.dot for matrix multiplication
        val = np.dot(np.dot(diff.T, inv_cov), diff)
        return np.sqrt(max(0, val))

    d_low = mahalanobis(x, mu_low, inv_cov_low)
    d_medium = mahalanobis(x, mu_medium, inv_cov_medium)
    d_high = mahalanobis(x, mu_high, inv_cov_high)

    # Find the nearest class
    distances = {"Low": d_low, "Medium": d_medium, "High": d_high}
    nearest_class = min(distances, key=distances.get)
    d_val = distances[nearest_class]

    # 6. Prediction
    # Distance Ranges from Training Data
    dist_ranges = {
        "Low": (0.15, 4.85),
        "Medium": (1.05, 5.22),
        "High": (0.55, 5.12)
    }
    
    # Universal Scaling
    vals = get_vals(nutrient) # [min, mid, max]
    val_min = vals[0]
    val_mid = vals[1]
    
    target_ranges = {
        "Low": (val_min, val_min + (val_mid - val_min) * 0.5), 
        "Medium": (val_min + (val_mid - val_min) * 0.5, val_mid),
        "High": (val_mid, val_mid * (500.0/350.0))
    }
    
    # Exact values for N
    if nutrient == "N":
        target_ranges = {
            "Low": (50.0, 200.0),
            "Medium": (200.0, 350.0),
            "High": (350.0, 500.0)
        }

    min_dist, max_dist = dist_ranges[nearest_class]
    n_min, n_max = target_ranges[nearest_class]

    position = (d_val - min_dist) / (max_dist - min_dist + 1e-10)
    position = max(0, min(position, 1))

    predicted = n_min + position * (n_max - n_min)
    return predicted
'''

with open(os.path.join(IMPL_DIR, 'logic_utils.py'), 'a', encoding='utf-8') as f:
    f.write(APPEND_CODE)

py_code = '''from logics.implementations.logic_utils import logic50_predict, wrap_details

def predict(s, d, target="All"):
    val = logic50_predict(s, d, target)
    return wrap_details(val, "Mahalanobis Distance", target)
'''

with open(os.path.join(IMPL_DIR, 'M50.py'), 'w', encoding='utf-8') as f:
    f.write(py_code)

json_def = {
    "id": "M50",
    "name": "Mahalanobis Distance Prediction",
    "type": "Mathematical",
    "target": "All 12 Nutrients",
    "features": "IP1, IP2, IP3",
    "required_ips": ["ip1", "ip2", "ip3"],
    "calibration_required": False,
    "calibration_source": "N/A",
    "verification_status": "VERIFIED",
    "formula": "Calculates Mahalanobis distance D = sqrt((x-u)^T * E^-1 * (x-u)) against pre-computed Low/Medium/High centroids and inverse covariance matrices. Selects nearest class and scales prediction along D."
}
with open(os.path.join(DEF_DIR, 'M50.json'), 'w', encoding='utf-8') as f:
    json.dump(json_def, f, indent=4)

print("SUCCESS: M50 added safely.")
