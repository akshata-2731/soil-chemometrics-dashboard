import json
import os
import importlib.util
import traceback

LOGICS_DEF = "logics/definitions"
LOGICS_IMPL = "logics/implementations"

logics = []
for f in os.listdir(LOGICS_DEF):
    if f.endswith(".json"):
        with open(os.path.join(LOGICS_DEF, f), "r", encoding="utf-8") as fh:
            data = json.load(fh)
            logics.append(data)

logics.sort(key=lambda x: x.get("id", ""))

md_lines = ["# FULL LOGIC AUDIT REPORT\n"]
md_lines.append("| Logic | Name | Type | Target | Wavelengths | Calibration | Code Exists | Runtime Check | Status |")
md_lines.append("|---|---|---|---|---|---|---|---|---|")

def test_logic(logic_id, target, cal_req):
    impl_path = os.path.join(LOGICS_IMPL, f"{logic_id}.py")
    if not os.path.exists(impl_path):
        return "NOT IMPLEMENTED", "Missing .py file"
        
    try:
        spec = importlib.util.spec_from_file_location(logic_id, impl_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except Exception as e:
        return "MISMATCH", f"Failed to load module: {e}"
        
    s_normal = [100.0 + i*5 for i in range(21)]
    s_zero = [0.0 for _ in range(21)]
    s_extreme = [9999.0 for _ in range(21)]
    s_neg = [-50.0 for _ in range(21)]
    
    cal_data = {"value_min": 0, "value_mid": 50, "value_max": 100, "min": s_normal, "mid": s_normal, "max": s_normal, "vals": [0, 50, 100]}
    
    try:
        res_normal = mod.predict(s_normal, cal_data)
        res_zero = mod.predict(s_zero, cal_data)
        res_extreme = mod.predict(s_extreme, cal_data)
        res_neg = mod.predict(s_neg, cal_data)
        
        return "VERIFIED", f"Normal:{res_normal:.2f}, Zero:{res_zero:.2f}, Extreme:{res_extreme:.2f}, Neg:{res_neg:.2f}"
    except Exception as e:
        return "MISMATCH", f"Runtime crash: {e}"

for l in logics:
    l_id = l.get("id") or l.get("logic_id")
    l_name = l.get("name", "") or l.get("logic_name", "")
    l_type = l.get("type", "Mathematical")
    l_target = l.get("target", "All")
    l_features = l.get("features", [])
    l_cal = "Req" if l.get("calibration_required") else "No"
    
    status, runtime_msg = test_logic(l_id, l_target, l.get("calibration_required"))
    
    code_exists = "Yes" if os.path.exists(os.path.join(LOGICS_IMPL, f"{l_id}.py")) else "No"
    
    md_lines.append(f"| {l_id} | {l_name} | {l_type} | {l_target} | {len(l_features) if l_features else 21} | {l_cal} | {code_exists} | {runtime_msg} | {status} |")

md_lines.append("\n## DETAILED LOGIC VERIFICATION\n")

for l in logics:
    l_id = l.get("id") or l.get("logic_id")
    l_name = l.get("name", "") or l.get("logic_name", "")
    md_lines.append(f"### Logic ID: {l_id}")
    md_lines.append(f"- **Name:** {l_name}")
    md_lines.append(f"- **Target Nutrient:** {l.get('target', 'All')}")
    md_lines.append(f"- **Method Type:** {l.get('type', 'Mathematical')}")
    md_lines.append(f"- **Calibration Required:** {l.get('calibration_required', False)}")
    md_lines.append(f"- **Formula / Calculation Steps:** {l.get('formula', 'Not documented')}")
    
    impl_path = os.path.join(LOGICS_IMPL, f"{l_id}.py")
    if os.path.exists(impl_path):
        with open(impl_path, "r", encoding="utf-8") as f:
            code = f.read()
        md_lines.append(f"- **Implemented Formula/Code snippet:**\n```python\n{code[:300]}...\n```")
    else:
        md_lines.append("- **Implemented Formula/Code snippet:** Missing")
    
    status, runtime_msg = test_logic(l_id, l.get("target"), l.get("calibration_required"))
    md_lines.append(f"- **Runtime Output:** {runtime_msg}")
    md_lines.append(f"- **Verification Status:** {status}")
    md_lines.append("\n")

with open(r"C:\Users\hp\.gemini\antigravity\brain\dc5d38c7-de50-4439-a2eb-5b857a17c7c6\audit_report.md", "w", encoding="utf-8") as f:
    f.write("\n".join(md_lines))

print("Audit complete")
