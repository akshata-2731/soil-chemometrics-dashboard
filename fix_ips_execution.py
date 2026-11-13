import json
import os
import re

IMPL_DIR = "logics/implementations"
DEF_DIR = "logics/definitions"

formulas = {
    1: "ip1 + ip2", 2: "ip1 + ip3", 3: "ip2 + ip3", 4: "ip1 - ip2", 5: "ip1 - ip3",
    6: "ip2 - ip3", 7: "ip1 * ip2", 8: "ip1 * ip3", 9: "ip2 * ip3",
    10: "ip1 / ip2 if ip2 else 0.0", 11: "ip1 / ip3 if ip3 else 0.0", 12: "ip2 / ip3 if ip3 else 0.0",
    13: "ip2 / ip1 if ip1 else 0.0", 14: "ip3 / ip1 if ip1 else 0.0", 15: "ip3 / ip2 if ip2 else 0.0",
    16: "(ip1 + ip2) * ip3", 17: "(ip1 - ip2) * ip3", 18: "(ip1 * ip3) + ip2",
    19: "(ip1 + ip3) * ip2", 20: "(ip1 * ip2) / ip3 if ip3 else 0.0",
    21: "(ip2 * ip3) / ip1 if ip1 else 0.0", 22: "ip1 + ip2 + ip3", 23: "ip1 * ip2 * ip3",
    24: "ip1**2", 25: "math.sqrt(max(0, ip1))", 26: "math.exp(min(ip1, 700))",
    27: "math.exp(min(ip1**2, 700))", 28: "1/ip1 if ip1 else 0.0", 29: "abs(ip1)",
    30: "math.log(max(1e-10, ip1))", 31: "ip2**2", 32: "math.sqrt(max(0, ip2))",
    33: "math.exp(min(ip2, 700))", 34: "math.exp(min(ip2**2, 700))", 35: "1/ip2 if ip2 else 0.0",
    36: "abs(ip2)", 37: "math.log(max(1e-10, ip2))", 38: "ip3**2", 39: "math.sqrt(max(0, ip3))",
    40: "math.exp(min(ip3, 700))", 41: "(ip1 - ip2) * ip3", 42: "1/ip3 if ip3 else 0.0",
    43: "abs(ip3)", 44: "math.log(max(1e-10, ip3))",
    45: "math.exp(min(ip1, 700)) / math.exp(min(ip2, 700)) if math.exp(min(ip2, 700)) else 0.0",
    46: "math.exp(min(ip1, 700)) / math.exp(min(ip3, 700)) if math.exp(min(ip3, 700)) else 0.0",
    47: "math.exp(min(ip2, 700)) / math.exp(min(ip3, 700)) if math.exp(min(ip3, 700)) else 0.0",
    48: "math.exp(min(ip1 - ip2, 700))", 49: "math.exp(min(ip1 - ip3, 700))", 50: "math.exp(min(ip2 - ip3, 700))"
}

def generate_ip_code(req_ips):
    code = ""
    if "ip1" in req_ips:
        code += "    g1 = s[0:9]\n    den1 = sum(g1)\n    ip1 = ((sum(x**2 for x in g1) / den1) / 100.0) if den1 != 0 else 0.0\n"
    if "ip2" in req_ips:
        code += "    g2 = s[9:18]\n    den2 = sum(g2)\n    ip2 = ((sum(x**2 for x in g2) / den2) / 100.0) if den2 != 0 else 0.0\n"
    if "ip3" in req_ips:
        code += "    g3 = s[18:21]\n    den3 = sum(g3)\n    ip3 = ((sum(x**2 for x in g3) / den3) / 100.0) if den3 != 0 else 0.0\n"
    return code

for i in range(1, 51):
    f_str = formulas[i]
    req = []
    if "ip1" in f_str: req.append("ip1")
    if "ip2" in f_str: req.append("ip2")
    if "ip3" in f_str: req.append("ip3")
    
    py_code = f"import math\n\ndef predict(s, d):\n{generate_ip_code(req)}\n    try:\n        val = {f_str}\n        return float(val) if not math.isnan(val) and not math.isinf(val) else 0.0\n    except Exception:\n        return 0.0\n"
    
    with open(os.path.join(IMPL_DIR, f"I{i}.py"), "w", encoding="utf-8") as f:
        f.write(py_code)
        
    json_path = os.path.join(DEF_DIR, f"I{i}.json")
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            jdata = json.load(f)
        jdata["required_ips"] = req
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(jdata, f, indent=4)

# Update MD and SAM_SRI which require all 3
for lid in ["MD", "SAM_SRI"]:
    json_path = os.path.join(DEF_DIR, f"{lid}.json")
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            jdata = json.load(f)
        jdata["required_ips"] = ["ip1", "ip2", "ip3"]
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(jdata, f, indent=4)
            
print("Fixed IPS requirements dynamically")
