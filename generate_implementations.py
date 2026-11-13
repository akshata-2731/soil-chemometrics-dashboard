import os
import math

IMPL_DIR = "logics/implementations"
os.makedirs(IMPL_DIR, exist_ok=True)

ips_base = """import math

def get_ips(s):
    try:
        g1 = s[0:9]
        g2 = s[9:18]
        g3 = s[18:21]
        def ip(g):
            den = sum(g)
            if den == 0: return 0.0
            num = sum(x**2 for x in g)
            return (num / den) / 100.0
        return ip(g1), ip(g2), ip(g3)
    except Exception:
        return 0.0, 0.0, 0.0

def predict(s, d):
    ip1, ip2, ip3 = get_ips(s)
    try:
        val = {formula}
        return float(val) if not math.isnan(val) and not math.isinf(val) else 0.0
    except Exception:
        return 0.0
"""

# I1 to I50 formulas mapping
formulas = {
    1: "ip1 + ip2",
    2: "ip1 + ip3",
    3: "ip2 + ip3",
    4: "ip1 - ip2",
    5: "ip1 - ip3",
    6: "ip2 - ip3",
    7: "ip1 * ip2",
    8: "ip1 * ip3",
    9: "ip2 * ip3",
    10: "ip1 / ip2 if ip2 else 0.0",
    11: "ip1 / ip3 if ip3 else 0.0",
    12: "ip2 / ip3 if ip3 else 0.0",
    13: "ip2 / ip1 if ip1 else 0.0",
    14: "ip3 / ip1 if ip1 else 0.0",
    15: "ip3 / ip2 if ip2 else 0.0",
    16: "(ip1 + ip2) * ip3",
    17: "(ip1 - ip2) * ip3",
    18: "(ip1 * ip3) + ip2",
    19: "(ip1 + ip3) * ip2",
    20: "(ip1 * ip2) / ip3 if ip3 else 0.0",
    21: "(ip2 * ip3) / ip1 if ip1 else 0.0",
    22: "ip1 + ip2 + ip3",
    23: "ip1 * ip2 * ip3",
    24: "ip1**2",
    25: "math.sqrt(max(0, ip1))",
    26: "math.exp(min(ip1, 700))",
    27: "math.exp(min(ip1**2, 700))",
    28: "1/ip1 if ip1 else 0.0",
    29: "abs(ip1)",
    30: "math.log(max(1e-10, ip1))",
    31: "ip2**2",
    32: "math.sqrt(max(0, ip2))",
    33: "math.exp(min(ip2, 700))",
    34: "math.exp(min(ip2**2, 700))",
    35: "1/ip2 if ip2 else 0.0",
    36: "abs(ip2)",
    37: "math.log(max(1e-10, ip2))",
    38: "ip3**2",
    39: "math.sqrt(max(0, ip3))",
    40: "math.exp(min(ip3, 700))",
    41: "(ip1 - ip2) * ip3",
    42: "1/ip3 if ip3 else 0.0",
    43: "abs(ip3)",
    44: "math.log(max(1e-10, ip3))",
    45: "math.exp(min(ip1, 700)) / math.exp(min(ip2, 700)) if math.exp(min(ip2, 700)) else 0.0",
    46: "math.exp(min(ip1, 700)) / math.exp(min(ip3, 700)) if math.exp(min(ip3, 700)) else 0.0",
    47: "math.exp(min(ip2, 700)) / math.exp(min(ip3, 700)) if math.exp(min(ip3, 700)) else 0.0",
    48: "math.exp(min(ip1 - ip2, 700))",
    49: "math.exp(min(ip1 - ip3, 700))",
    50: "math.exp(min(ip2 - ip3, 700))",
}

for i in range(1, 51):
    path = os.path.join(IMPL_DIR, f"I{i}.py")
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write(ips_base.replace("{formula}", formulas[i]))


# MD.py
md_code = """import math
import numpy as np

def get_ips(s):
    try:
        g1 = s[0:9]
        g2 = s[9:18]
        g3 = s[18:21]
        def ip(g):
            den = sum(g)
            return ((sum(x**2 for x in g) / den) / 100.0) if den != 0 else 0.0
        return ip(g1), ip(g2), ip(g3)
    except:
        return 0.0, 0.0, 0.0

def predict(s, d):
    ip1, ip2, ip3 = get_ips(s)
    x = np.array([ip1, ip2, ip3])
    
    c_low = np.array([8.569986, 3.731463, 1.716387])
    c_med = np.array([10.308449, 3.918395, 3.820572])
    c_high = np.array([8.805760, 3.760319, 2.218485])
    
    inv_low = np.array([[2.896, -7.424, -2.502], [-7.424, 34.585, 5.496], [-2.502, 5.496, 2.772]])
    inv_med = np.array([[1.500, -6.242, -1.060], [-6.242, 30.243, 3.682], [-1.060, 3.682, 1.284]])
    inv_high = np.array([[1.645, -6.673, -1.184], [-6.673, 39.030, 4.729], [-1.184, 4.729, 1.379]])
    
    def calc_d(x_v, c_v, inv_v):
        diff = x_v - c_v
        return math.sqrt(max(0, np.dot(np.dot(diff.T, inv_v), diff)))
        
    try:
        d_low = calc_d(x, c_low, inv_low)
        d_med = calc_d(x, c_med, inv_med)
        d_high = calc_d(x, c_high, inv_high)
    except:
        return 0.0
        
    distances = {'Low': d_low, 'Medium': d_med, 'High': d_high}
    min_c = min(distances, key=distances.get)
    min_dist = distances[min_c]
    
    if min_c == 'Low':
        n_min, n_max = 50, 200
        d_min, d_max = 0.15, 4.85
    elif min_c == 'Medium':
        n_min, n_max = 200, 350
        d_min, d_max = 1.05, 5.22
    else:
        n_min, n_max = 350, 500
        d_min, d_max = 0.55, 5.12
        
    pos = (min_dist - d_min) / (d_max - d_min + 1e-10)
    pos = max(0.0, min(pos, 1.0))
    return float(n_min + pos * (n_max - n_min))
"""
if not os.path.exists(os.path.join(IMPL_DIR, "MD.py")):
    with open(os.path.join(IMPL_DIR, "MD.py"), "w") as f:
        f.write(md_code)

# SAM_SRI.py
sam_code = """import math
import numpy as np

def get_ips(s):
    try:
        g1 = s[0:9]
        g2 = s[9:18]
        g3 = s[18:21]
        def ip(g):
            den = sum(g)
            return ((sum(x**2 for x in g) / den) / 100.0) if den != 0 else 0.0
        return ip(g1), ip(g2), ip(g3)
    except:
        return 0.0, 0.0, 0.0

def predict(s, d):
    ip1, ip2, ip3 = get_ips(s)
    if ip2 == 0: return 0.0
    sri = (ip1 * ip3) / ip2
    
    c_low = np.array([8.569986, 3.731463, 1.716387])
    c_med = np.array([10.308449, 3.918395, 3.820572])
    c_high = np.array([8.805760, 3.760319, 2.218485])
    v = np.array([ip1, ip2, ip3])
    
    def calc_angle(v1, v2):
        den = np.linalg.norm(v1) * np.linalg.norm(v2)
        if den == 0: return 90.0
        val = np.dot(v1, v2) / den
        val = max(-1.0, min(val, 1.0))
        return math.acos(val) * 180.0 / math.pi
        
    a_low = calc_angle(v, c_low)
    a_med = calc_angle(v, c_med)
    a_high = calc_angle(v, c_high)
    
    final_class = "Low"
    
    if (sri < 1.2 and ip1 < 8.0 and ip3 < 0.7) or (sri > 8.0):
        final_class = "High"
    elif 3.0 <= sri <= 8.0:
        final_class = "Low" if a_low < a_med else "Medium"
    else:
        angles = {'Low': a_low, 'Medium': a_med, 'High': a_high}
        sam_class = min(angles, key=angles.get)
        if sam_class == 'High':
            final_class = "Low" if a_low < a_med else "Medium"
        else:
            final_class = sam_class
            
    if final_class == "Low":
        sri_min, sri_max, n_min, n_max = 0.2, 4.0, 0, 150
    elif final_class == "Medium":
        sri_min, sri_max, n_min, n_max = 1.5, 9.0, 150, 300
    else:
        sri_min, sri_max, n_min, n_max = 0.1, 20.0, 300, 500
        
    pos = (sri - sri_min) / (sri_max - sri_min + 1e-10)
    pos = max(0.0, min(pos, 1.0))
    return float(n_min + pos * (n_max - n_min))
"""
if not os.path.exists(os.path.join(IMPL_DIR, "SAM_SRI.py")):
    with open(os.path.join(IMPL_DIR, "SAM_SRI.py"), "w") as f:
        f.write(sam_code)

print("Created 52 missing implementation files successfully.")
