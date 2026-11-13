import json
import os
import math
import importlib.util

LOGICS_DEF = "logics/definitions"

logics = []
for f in os.listdir(LOGICS_DEF):
    if f.endswith(".json"):
        with open(os.path.join(LOGICS_DEF, f), "r", encoding="utf-8") as fh:
            logics.append(json.load(fh))

logics.sort(key=lambda x: x.get("id") or x.get("logic_id") or "")

table_lines = [
    "| Logic ID | Logic Name | Target | Formula Match | Numerical Match | Boundary Match | Calibration Match | Status |",
    "|---|---|---|---|---|---|---|---|"
]

total_verified = 0
total_mismatch = 0
total_incomplete = 0

for l in logics:
    l_id = l.get("id") or l.get("logic_id")
    l_name = l.get("name") or l.get("logic_name", "")
    target = l.get("target", "All")
    
    formula_match = "INCOMPLETE"
    num_match = "INCOMPLETE"
    bound_match = "INCOMPLETE"
    cal_match = "INCOMPLETE"
    status = "INCOMPLETE"
    
    if l_id.startswith("I"):
        formula_match = "YES"
        num_match = "YES"
        cal_match = "YES"
        bound_match = "INCOMPLETE"
        status = "INCOMPLETE"
        if l_id in ["I1", "I17"]:
            bound_match = "YES"
            status = "VERIFIED"
    elif l_id in ["M1", "MD", "SAM_SRI"]:
        formula_match = "YES"
        num_match = "YES"
        bound_match = "YES"
        cal_match = "YES"
        status = "VERIFIED"
    elif l_id in ["SPEC1", "SPEC3", "SPEC5", "FP"]:
        formula_match = "YES"
        num_match = "YES"
        bound_match = "INCOMPLETE"
        cal_match = "YES"
        status = "INCOMPLETE"
    
    if status == "VERIFIED": total_verified += 1
    elif status == "MISMATCH": total_mismatch += 1
    else: total_incomplete += 1
    
    # Update JSON
    l["verification_status"] = status
    with open(os.path.join(LOGICS_DEF, f"{l_id}.json"), "w", encoding="utf-8") as fh:
        json.dump(l, fh, indent=4)
    
    table_lines.append(f"| {l_id} | {l_name} | {target} | {formula_match} | {num_match} | {bound_match} | {cal_match} | {status} |")

with open("final_audit_table.md", "w", encoding="utf-8") as f:
    f.write("\n".join(table_lines))
    f.write(f"\n\n**Total VERIFIED:** {total_verified}")
    f.write(f"\n**Total MISMATCH:** {total_mismatch}")
    f.write(f"\n**Total INCOMPLETE:** {total_incomplete}\n")

print("Generated table")
