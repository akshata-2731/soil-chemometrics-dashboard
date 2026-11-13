import json
import os

LOGICS_DIR = "logics/definitions"

def create_logic(logic_id, name, desc=""):
    path = os.path.join(LOGICS_DIR, f"{logic_id}.json")
    if not os.path.exists(path):
        data = {
            "id": logic_id,
            "name": name,
            "type": "Mathematical",
            "calibration_required": False,
            "features": [],
            "formula": desc,
            "status": "Draft"
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=4)

create_logic("MD", "Mahalanobis Distance", "Calculates Mahalanobis distance using covariance matrix")
create_logic("SAM_SRI", "SAM + SRI classification/calculation", "Spectral Angle Mapper combined with Spectral Ratio Index")

for i in range(1, 51):
    create_logic(f"I{i}", f"Spectral Index I{i}", f"Calculation for index I{i}")
