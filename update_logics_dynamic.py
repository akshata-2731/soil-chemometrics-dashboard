import os
import re

IMPL_DIR = 'logics/implementations'
UTIL_FILE = os.path.join(IMPL_DIR, 'logic_utils.py')

with open(UTIL_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace logic50_predict
new_logic50 = '''def logic50_predict(sample, d, nutrient):
    import json
    import os
    # 1. Wavelengths
    A, B, C, D, E, F, G, H = sample[0:8]
    I, J, S680, L = sample[8], sample[9], sample[10], sample[11]
    T = sample[12]
    K900, R = sample[16], sample[17]
    U320, V280, W200 = sample[18], sample[19], sample[20]

    def calc_ips(group):
        return (sum(x**2 for x in group) / (sum(group) + 1e-10)) / 100.0

    ip1 = calc_ips([A, B, C, D, E, F, G, H, R])
    ip2 = calc_ips([I, S680, J, T, U320, V280, W200, K900, L])
    ip3 = calc_ips([U320, V280, W200])

    x = np.array([ip1, ip2, ip3])

    # Dynamically load nutrient specific matrices
    matrices_path = os.path.join('logics', 'implementations', 'advanced_matrices.json')
    try:
        with open(matrices_path, 'r') as mf:
            all_matrices = json.load(mf)
    except:
        all_matrices = {}
    
    nut_m = all_matrices.get(nutrient, all_matrices.get('N', {}))
    if not nut_m:
        return 0.0 # Fallback

    mu_low = np.array(nut_m['centroids']['Low'])
    inv_cov_low = np.array(nut_m['covariances']['Low'])

    mu_medium = np.array(nut_m['centroids']['Medium'])
    inv_cov_medium = np.array(nut_m['covariances']['Medium'])

    mu_high = np.array(nut_m['centroids']['High'])
    inv_cov_high = np.array(nut_m['covariances']['High'])

    def calc_mahalanobis(x, mu, inv_cov):
        diff = x - mu
        return np.dot(np.dot(diff.T, inv_cov), diff)

    d_low = calc_mahalanobis(x, mu_low, inv_cov_low)
    d_med = calc_mahalanobis(x, mu_medium, inv_cov_medium)
    d_high = calc_mahalanobis(x, mu_high, inv_cov_high)

    distances = {"Low": d_low, "Medium": d_med, "High": d_high}
    pred_class = min(distances, key=distances.get)

    min_dist = distances[pred_class]
    max_dist = max(distances.values())

    sri_ranges = nut_m['sri_ranges']
    val_min = sri_ranges[pred_class]['val_min']
    val_max = sri_ranges[pred_class]['val_max']

    position = (min_dist - 0.15) / (max_dist - 0.15 + 1e-10)
    position = max(0, min(position, 1))

    predicted = val_min + position * (val_max - val_min)
    return predicted'''

content = re.sub(r'def logic50_predict\(sample, d, nutrient\):.*?return predicted', new_logic50, content, flags=re.DOTALL)


# Replace logic51_predict
new_logic51 = '''def logic51_predict(sample, d, nutrient):
    import json
    import os
    # 1. Wavelengths
    A, B, C, D, E, F, G, H = sample[0:8]
    I, J, S680, L = sample[8], sample[9], sample[10], sample[11]
    T = sample[12]
    K900, R = sample[16], sample[17]
    U320, V280, W200 = sample[18], sample[19], sample[20]

    def calc_ips(group):
        return (sum(x**2 for x in group) / (sum(group) + 1e-10)) / 100.0

    ip1 = calc_ips([A, B, C, D, E, F, G, H, R])
    ip2 = calc_ips([I, S680, J, T, U320, V280, W200, K900, L])
    ip3 = calc_ips([U320, V280, W200])

    sri = (ip1 * ip3) / (ip2 + 1e-10)

    matrices_path = os.path.join('logics', 'implementations', 'advanced_matrices.json')
    try:
        with open(matrices_path, 'r') as mf:
            all_matrices = json.load(mf)
    except:
        all_matrices = {}
    
    nut_m = all_matrices.get(nutrient, all_matrices.get('N', {}))
    if not nut_m:
        return 0.0

    c_low = np.array(nut_m['centroids']['Low'])
    c_med = np.array(nut_m['centroids']['Medium'])
    c_high = np.array(nut_m['centroids']['High'])
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

    hr = nut_m['high_rules']
    pred_class = None
    if sri < hr['Group_B']['sri_threshold'] and ip1 < hr['Group_B']['ip1_threshold'] and ip3 < hr['Group_B']['ip3_threshold']:
        pred_class = "High"
    elif sri > hr['Group_A']['sri_threshold']:
        pred_class = "High"
    elif 3.0 <= sri <= 8.0:
        pred_class = "Low" if angle_low < angle_med else "Medium"
    else:
        angles = {"Low": angle_low, "Medium": angle_med, "High": angle_high}
        pred_class = min(angles, key=angles.get)
        if pred_class == "High":
            pred_class = "Low" if angle_low < angle_med else "Medium"

    sri_ranges = nut_m['sri_ranges']
    sri_min = sri_ranges[pred_class]['sri_min']
    sri_max = sri_ranges[pred_class]['sri_max']
    n_min = sri_ranges[pred_class]['val_min']
    n_max = sri_ranges[pred_class]['val_max']

    position = (sri - sri_min) / ((sri_max - sri_min) + 1e-10)
    position = max(0, min(position, 1))

    predicted = n_min + position * (n_max - n_min)
    return predicted'''

content = re.sub(r'def logic51_predict\(sample, d, nutrient\):.*?return predicted', new_logic51, content, flags=re.DOTALL)

with open(UTIL_FILE, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated logic_utils.py with dynamic JSON loading!")
